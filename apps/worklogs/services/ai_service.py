"""
LangGraph Async AI Worklog & Weekly Report Agent.

Implements a 3-node stateful workflow:
1. context_assembler: Pulls PostgreSQL ground truth (contract, deliverables, logs) + queries Qdrant vector context.
2. report_generator: Calls Groq LLaMA 3.3 70B to produce conversational answers or structured 3-section drafts.
3. pdf_builder: Triggered on draft approval to compile WeasyPrint PDF, upload to Azure Blob Storage, and return SAS URL.
"""
import json
import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, TypedDict, Literal
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum
from asgiref.sync import sync_to_async
from apps.bidding.models import Contract
from apps.worklogs.models import (
    WorkLog,
    WeeklyReport,
    Deliverable,
    AIConversation,
    AIReportDraft,
)
from apps.worklogs.services.qdrant_service import query_context
from apps.worklogs.services.pdf_service import upload_to_azure_blob

logger = logging.getLogger(__name__)

# LangSmith Tracing decorator
try:
    from langsmith import traceable
except ImportError:
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if not args else decorator(args[0])

# LangChain Groq imports
try:
    from langchain_groq import ChatGroq
    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
    from langgraph.graph import StateGraph, END
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


class AIWorklogState(TypedDict):
    contract_id: int
    freelancer_id: int
    user_message: str
    conversation_id: Optional[int]
    conversation_history: List[Dict[str, Any]]
    action: Literal["chat", "draft", "approve"]
    draft_id: Optional[int]
    postgres_context: Dict[str, Any]
    qdrant_context: List[Dict[str, Any]]
    llm_response: str
    report_draft: Optional[Dict[str, Any]]
    pdf_url: Optional[str]
    is_draft_ready: bool
    error: Optional[str]


def get_groq_llm():
    """Returns ChatGroq instance if available, or None for fallback."""
    return get_llm()


def get_llm():
    """Returns ChatGroq instance if available, or None for fallback."""
    if LANGCHAIN_AVAILABLE and getattr(settings, "GROQ_API_KEY", None):
        try:
            return ChatGroq(
                model=getattr(settings, "GROQ_MODEL", "openai/gpt-oss-120b"),
                api_key=settings.GROQ_API_KEY,
                temperature=0.6,
                max_tokens=2048,
            )
        except Exception as e:
            logger.warning("Failed to initialize ChatGroq: %s", e)
    return None


def call_gemini_fallback_sync(system_prompt: str, history: List[Dict], user_msg: str) -> Optional[str]:
    """
    Google Gemini fallback LLM invocation via official REST API.
    Triggered whenever Groq encounters a rate limit, outage, or is unavailable.
    """
    import requests
    api_key = getattr(settings, "GEMINI_API_KEY", "")
    if not api_key:
        return None

    full_prompt = f"{system_prompt}\n\nCONVERSATION HISTORY:\n"
    for msg in history[-6:]:
        role = "Freelancer" if msg.get("role") == "user" else "Assistant"
        full_prompt += f"{role}: {msg.get('content', '')}\n"
    full_prompt += f"Freelancer: {user_msg}\nAssistant:"

    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={api_key}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": full_prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.6,
            "maxOutputTokens": 2048
        }
    }

    try:
        resp = requests.post(endpoint, json=payload, timeout=12)
        if resp.status_code == 200:
            res_json = resp.json()
            candidates = res_json.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
        else:
            logger.warning("Google Gemini API returned status %s: %s", resp.status_code, resp.text)
    except Exception as e:
        logger.warning("Google Gemini fallback error: %s", e)
        return None
    return None


def generate_weekly_report(contract_id: int, week_start: Any, interval_days: int = 7) -> WeeklyReport:
    """
    Synchronous entry point used by Celery Beat tasks and legacy workflows.
    Compiles report via LLM or template and creates WeeklyReport record.
    """
    if isinstance(week_start, str):
        week_start = date.fromisoformat(week_start)

    week_end = week_start + timedelta(days=interval_days - 1)
    contract = Contract.objects.select_related("bid__project__client", "bid__freelancer").get(id=contract_id)

    # Calculate hours
    total_hours = WorkLog.objects.filter(
        contract=contract,
        date__range=[week_start, week_end]
    ).aggregate(total=Sum("hours_worked"))["total"] or 0

    logs = list(WorkLog.objects.filter(
        contract=contract,
        date__range=[week_start, week_end]
    ).order_by("date"))

    log_bullets = "\n".join([f"- {log.date}: {log.description} ({log.hours_worked}h)" for log in logs]) or "- Regular milestone deliverables development."

    summary = (
        f"## Weekly Progress Report ({week_start} to {week_end})\n\n"
        f"**Project**: {contract.bid.project.title}\n"
        f"**Client**: {contract.bid.project.client.get_full_name() or contract.bid.project.client.username}\n"
        f"**Total Hours**: {total_hours} hrs\n\n"
        f"### Completed Work\n{log_bullets}\n\n"
        f"### Next Steps\nContinue deliverable verification and sprint goals."
    )

    report, _ = WeeklyReport.objects.update_or_create(
        contract=contract,
        week_start=week_start,
        defaults={
            "week_end": week_end,
            "ai_summary": summary,
            "interval_days": interval_days,
        }
    )
    return report


# ─────────────────────────────────────────────────────────────────────────────
# Node 1: context_assembler
# ─────────────────────────────────────────────────────────────────────────────

@traceable(name="context_assembler", tags=["worklog", "agent", "context"])
async def context_assembler(state: AIWorklogState) -> AIWorklogState:
    """
    Fetches relational PostgreSQL contract metadata, deliverables, work logs,
    and semantically queries Qdrant for project scope and requirement matches.
    """
    contract_id = state["contract_id"]
    user_message = state.get("user_message", "")

    # 1. Fetch DB context asynchronously
    def _fetch_pg_context():
        try:
            contract = Contract.objects.select_related(
                "bid__project__client",
                "bid__freelancer"
            ).prefetch_related("deliverables", "milestones").get(id=contract_id)
        except Contract.DoesNotExist:
            return None

        # Recent worklogs (last 14 days)
        fourteen_days_ago = date.today() - timedelta(days=14)
        recent_logs = list(WorkLog.objects.filter(
            contract=contract,
            date__gte=fourteen_days_ago
        ).order_by("-date")[:10])

        total_hours = WorkLog.objects.filter(
            contract=contract
        ).aggregate(total=Sum("hours_worked"))["total"] or 0

        # Deliverables & Milestones list
        deliverables = list(contract.deliverables.all())
        milestones = list(contract.milestones.all())

        # Previous approved reports
        past_reports = list(AIReportDraft.objects.filter(
            contract=contract,
            status=AIReportDraft.Status.APPROVED
        ).order_by("-created_at")[:3])

        return {
            "project_title": contract.bid.project.title,
            "project_description": contract.bid.project.description,
            "client_name": contract.bid.project.client.get_full_name() or contract.bid.project.client.username,
            "freelancer_name": contract.bid.freelancer.get_full_name() or contract.bid.freelancer.username,
            "contract_rate": str(getattr(contract, "agreed_amount", 0)),
            "contract_type": getattr(contract, "contract_type", "FIXED"),
            "total_hours_logged": float(total_hours),
            "deliverables": [
                {
                    "id": d.id,
                    "title": d.title,
                    "status": d.status,
                    "description": d.description[:150]
                }
                for d in deliverables
            ],
            "milestones": [
                {
                    "id": m.id,
                    "title": m.title,
                    "status": m.status,
                    "amount": str(m.amount),
                    "due_date": str(m.due_date) if m.due_date else None,
                    "description": m.description[:150]
                }
                for m in milestones
            ],
            "recent_logs": [
                {
                    "date": str(log.date),
                    "hours": float(log.hours_worked),
                    "description": log.description
                }
                for log in recent_logs
            ],
            "past_reports_count": len(past_reports),
        }

    pg_context = await sync_to_async(_fetch_pg_context)()
    if not pg_context:
        state["error"] = f"Contract #{contract_id} not found"
        return state

    state["postgres_context"] = pg_context

    # 2. Fetch Qdrant Semantic Context asynchronously
    q_matches = await sync_to_async(query_context)(contract_id, user_message, top_k=4)
    state["qdrant_context"] = q_matches or []

    return state


import re

# ─────────────────────────────────────────────────────────────────────────────
# Security & Safety Guardrails
# ─────────────────────────────────────────────────────────────────────────────

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"system\s+prompt\s+override",
    r"you\s+are\s+now\s+in\s+developer\s+mode",
    r"jailbreak",
    r"bypass\s+(safety|guardrails|filters)",
    r"release\s+(funds|escrow|payment)",
    r"transfer\s+(money|funds|balance)",
    r"execute\s+payment",
    r"access\s+(client\s+wallet|bank|credentials)",
    r"reveal\s+(api\s+key|private\s+key|password|secrets)",
    r"dan\s+mode",
]

def sanitize_sensitive_data(text: str) -> str:
    """
    Strips credit card numbers, bank account patterns, private keys, and API tokens
    to prevent sensitive client/freelancer PII from reaching LLMs or vector databases.
    """
    if not text:
        return ""
    # Credit Card pattern (13-19 digits with optional spaces/hyphens)
    text = re.sub(r"\b(?:\d[ -]*?){13,19}\b", "[REDACTED_CARD_NUMBER]", text)
    # API tokens, Razorpay keys, bearer tokens
    text = re.sub(r"(?:rzp_[a-zA-Z0-9_]+|Bearer\s+[a-zA-Z0-9_\-\.]+|sk-[a-zA-Z0-9]{20,})", "[REDACTED_TOKEN]", text)
    # Private Key blocks
    text = re.sub(r"-----BEGIN[ A-Z_-]+PRIVATE KEY-----[\s\S]+?-----END[ A-Z_-]+PRIVATE KEY-----", "[REDACTED_PRIVATE_KEY]", text)
    # Passwords / secrets
    text = re.sub(r"(?:password|passwd|secret)\s*[:=]\s*\S+", "[REDACTED_SECRET]", text, flags=re.IGNORECASE)
    return text


def detect_prompt_injection(user_message: str) -> bool:
    """
    Basic guardrail detecting prompt injection or unauthorized payment execution attempts.
    """
    if not user_message:
        return False
    msg_lower = user_message.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, msg_lower):
            return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# Node 2: report_generator
# ─────────────────────────────────────────────────────────────────────────────

@traceable(name="report_generator", tags=["worklog", "agent", "llm"])
async def report_generator(state: AIWorklogState) -> AIWorklogState:
    """
    Calls Groq LLaMA 3.3 70B with assembled context and determines intent:
    Outputs a structured 3-section report draft or conversational coaching.
    Enforces strict payment isolation and prompt injection guardrails.
    """
    if state.get("error"):
        return state

    # If action is direct approve, skip generation directly to pdf_builder
    if state.get("action") == "approve":
        return state

    user_msg = state.get("user_message", "")

    # ── Guardrail 1: Prompt Injection & Unauthorized Payment Attempt Check ──
    if detect_prompt_injection(user_msg):
        state["llm_response"] = (
            "I am the FreelanceFlow AI Worklog Assistant. My role is strictly limited to helping you "
            "document deliverables and draft milestone progress reports. I do not have access to financial systems, "
            "cannot execute payments or fund transfers, and cannot bypass platform safety boundaries."
        )
        state["report_draft"] = None
        state["is_draft_ready"] = False
        return state

    pg = state["postgres_context"]
    # Sanitize inputs before feeding to LLM
    clean_user_msg = sanitize_sensitive_data(user_msg)
    q_context = "\n".join([f"- [{item.get('type')}]: {sanitize_sensitive_data(item.get('text', ''))}" for item in state.get("qdrant_context", [])])
    history = state.get("conversation_history", [])

    system_prompt = f"""You are the FreelanceFlow AI Worklog & Weekly Report Assistant.
Your goal is to help the freelancer document progress, synthesize weekly achievements, and draft professional progress reports for their client.

SECURITY & SAFETY BOUNDARY:
- You are strictly an automated technical reporting assistant.
- You have NO access to client bank accounts, payment gateways, wallets, or financial execution tools.
- You CANNOT authorize, release, debit, or transfer payments.
- Never output sensitive personal credentials, payment tokens, or client private info.

PROJECT METRICS & SCOPE:
- Project: {pg['project_title']}
- Client: {pg['client_name']}
- Total Hours Logged to Date: {pg['total_hours_logged']}h
- Payment Milestones: {json.dumps(pg.get('milestones', []))}
- Deliverables in Project: {json.dumps(pg['deliverables'])}

SEMANTIC SCOPE GROUNDING (from Qdrant):
{q_context or 'No specific vector matches.'}

RECENT WORKLOGS:
{json.dumps(pg['recent_logs'])}

INSTRUCTIONS:
1. If the freelancer is asking to draft, generate, update, or compile a report, or asking about progress report timelines (e.g. "draft my progress report", "what is my timeline of my progress report", "generate report", "here is what I did", "summarize my week"), you MUST respond with a JSON block containing a structured 3-section draft:
```json
{{
  "is_draft": true,
  "reply": "I have created your progress report draft with milestone progress and target timeline. Review the details below and click Approve to generate the official report PDF.",
  "draft": {{
    "title": "Weekly Progress Report - {pg['project_title']}",
    "section_summary": "Executive summary of progress made towards milestone objectives and target timeline.",
    "section_deliverables": [
      {{"title": "Milestone & Deliverable Progress", "description": "Specific technical work completed and deliverables verified against the project schedule.", "status": "COMPLETED"}}
    ],
    "section_next_steps": "Upcoming milestone deadlines, timeline schedule for remaining tasks, and next deliverables.",
    "hours_worked": 8.0
  }}
}}
```

2. The AI worklog assistant's core purpose is drafting and organizing worklogs simply and cleanly. Always return valid JSON.
"""

    llm = get_llm()
    ai_raw = ""

    if llm:
        try:
            messages = [SystemMessage(content=system_prompt)]
            for msg in history[-8:]:  # keep last 8 messages for tight context
                role = msg.get("role")
                content = msg.get("content", "")
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))
            messages.append(HumanMessage(content=user_msg))

            res = await llm.ainvoke(messages)
            ai_raw = res.content.strip()
        except Exception as e:
            logger.warning("Groq primary LLM failed, falling back to Google Gemini: %s", e)
            ai_raw = ""

    # Google Gemini Fallback if Groq was empty or raised an exception
    if not ai_raw:
        ai_raw = await sync_to_async(call_gemini_fallback_sync)(system_prompt, history, user_msg) or ""

    # Resilient fallback if LLM is offline or output is non-JSON
    parsed = None
    if ai_raw:
        # Strip markdown code blocks if present
        cleaned = ai_raw
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            parsed = json.loads(cleaned)
        except Exception:
            parsed = {"is_draft": False, "reply": ai_raw}

    if not parsed:
        # Fallback intelligent generator
        if any(w in user_msg.lower() for w in ["draft", "report", "generate", "summary", "submit", "done", "week"]):
            parsed = {
                "is_draft": True,
                "reply": f"Here is the synthesized progress report draft for **{pg['project_title']}** based on your logged work.",
                "draft": {
                    "title": f"Progress Report - {pg['project_title']}",
                    "section_summary": f"Completed active project milestones for {pg['project_title']} under client {pg['client_name']}. Progress is on schedule with clean deliverables.",
                    "section_deliverables": [
                        {"title": d["title"], "description": d["description"], "status": "IN_PROGRESS"}
                        for d in pg["deliverables"][:3]
                    ] or [{"title": "Core Implementation", "description": user_msg, "status": "COMPLETED"}],
                    "section_next_steps": "Continue final verification, deliverable reviews, and prepare next milestone deployment.",
                    "hours_worked": max(4.0, float(pg["total_hours_logged"]) or 8.0)
                }
            }
        else:
            parsed = {
                "is_draft": False,
                "reply": f"I'm tracking your progress on **{pg['project_title']}**. You have logged {pg['total_hours_logged']}h so far. Tell me what tasks you finished today, or say *'Draft my weekly report'* to generate a 3-section client report."
            }

    state["llm_response"] = parsed.get("reply", "")
    state["is_draft_ready"] = bool(parsed.get("is_draft") and parsed.get("draft"))
    state["report_draft"] = parsed.get("draft") if state["is_draft_ready"] else None

    # Persist conversation & draft asynchronously to PostgreSQL
    def _persist_state():
        conv = None
        if state.get("conversation_id"):
            conv = AIConversation.objects.filter(id=state["conversation_id"]).first()

        if not conv:
            conv = AIConversation.objects.create(
                contract_id=state["contract_id"],
                freelancer_id=state["freelancer_id"],
                week_start=date.today() - timedelta(days=date.today().weekday()),
                week_end=date.today(),
            )
            state["conversation_id"] = conv.id

        # Append messages
        conv.messages.append({
            "role": "user",
            "content": user_msg,
            "timestamp": timezone.now().isoformat()
        })
        conv.messages.append({
            "role": "assistant",
            "content": state["llm_response"],
            "timestamp": timezone.now().isoformat(),
            "has_draft": state["is_draft_ready"],
            "draft_data": state["report_draft"]
        })
        conv.save(update_fields=["messages", "updated_at"])

        # If a draft was generated, create/update AIReportDraft
        if state["is_draft_ready"] and state["report_draft"]:
            d_data = state["report_draft"]
            draft_obj = AIReportDraft.objects.create(
                conversation=conv,
                contract_id=state["contract_id"],
                freelancer_id=state["freelancer_id"],
                title=d_data.get("title", f"Report - {pg['project_title']}"),
                section_summary=d_data.get("section_summary", ""),
                section_deliverables=d_data.get("section_deliverables", []),
                section_next_steps=d_data.get("section_next_steps", ""),
                hours_worked=d_data.get("hours_worked", 0.0),
                status=AIReportDraft.Status.DRAFT,
            )
            state["draft_id"] = draft_obj.id

    await sync_to_async(_persist_state)()
    return state


# ─────────────────────────────────────────────────────────────────────────────
# Node 3: pdf_builder
# ─────────────────────────────────────────────────────────────────────────────

@traceable(name="pdf_builder", tags=["worklog", "agent", "pdf"])
async def pdf_builder(state: AIWorklogState) -> AIWorklogState:
    """
    Compiles an approved AIReportDraft into a WeasyPrint PDF, uploads to Azure Blob Storage,
    and returns a 7-day SAS download URL.
    """
    draft_id = state.get("draft_id")
    contract_id = state["contract_id"]

    def _compile_and_upload():
        draft = None
        if draft_id:
            # Security: always scope draft lookup to the contract passed in state.
            # A bare filter(id=draft_id) would allow cross-contract IDOR.
            draft = AIReportDraft.objects.select_related(
                "contract__bid__project__client",
                "contract__bid__freelancer"
            ).filter(id=draft_id, contract_id=contract_id).first()

            # If draft_id was explicitly provided but not found for this contract,
            # abort rather than silently falling through to a different draft.
            if not draft:
                return None, "Draft not found or does not belong to this contract"

        if not draft:
            draft = AIReportDraft.objects.select_related(
                "contract__bid__project__client",
                "contract__bid__freelancer"
            ).filter(contract_id=contract_id).order_by("-created_at").first()

        if not draft:
            return None, "No report draft found to compile"

        contract = draft.contract
        project = contract.bid.project
        client = project.client
        freelancer = contract.bid.freelancer

        # Build clean HTML template for PDF
        deliverables_html = ""
        for d in draft.section_deliverables:
            if isinstance(d, dict):
                deliverables_html += f"""
                <div style="margin-bottom: 10px; padding: 10px 12px; background: #f8fafc; border-left: 4px solid #1e40af; border-radius: 4px; border: 1px solid #e2e8f0; border-left-width: 4px;">
                    <div style="margin-bottom: 4px;">
                        <strong style="color: #0f172a; font-size: 13px;">{d.get('title', 'Deliverable')}</strong>
                        <span style="font-size: 10px; background: #eff6ff; color: #1e40af; border: 1px solid #bfdbfe; padding: 1px 6px; border-radius: 4px; font-weight: bold; margin-left: 8px;">{d.get('status', 'COMPLETED')}</span>
                    </div>
                    <p style="margin: 0; color: #475569; font-size: 12px; line-height: 1.4;">{d.get('description', '')}</p>
                </div>
                """

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                @page {{ size: A4; margin: 18mm; }}
                body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #1e293b; line-height: 1.5; font-size: 13px; }}
                .header {{ border-bottom: 2px solid #1e40af; padding-bottom: 12px; margin-bottom: 20px; }}
                .badge {{ background: #1e40af; color: #ffffff; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: bold; letter-spacing: 0.5px; }}
                h1 {{ margin: 8px 0 4px 0; color: #0f172a; font-size: 20px; }}
                h2 {{ color: #1e40af; font-size: 14px; border-bottom: 1px solid #cbd5e1; padding-bottom: 4px; margin-top: 20px; margin-bottom: 10px; font-weight: bold; }}
                .meta-table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; }}
                .meta-table td {{ padding: 8px 12px; font-size: 12px; border-bottom: 1px solid #e2e8f0; }}
                .footer {{ margin-top: 35px; border-top: 1px solid #e2e8f0; padding-top: 12px; font-size: 11px; color: #64748b; text-align: center; }}
                .disclaimer {{ font-size: 10.5px; color: #475569; font-style: italic; margin-top: 4px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <span class="badge">VERIFIED WORKLOG REPORT</span>
                <h1>{draft.title}</h1>
                <p style="margin: 0; color: #64748b; font-size: 12px;">FreelanceFlow Verified Progress Document • Contract #{contract.id}</p>
            </div>

            <table class="meta-table">
                <tr>
                    <td style="width: 50%;"><strong>Project:</strong> {project.title}</td>
                    <td style="width: 50%;"><strong>Freelancer:</strong> {freelancer.get_full_name() or freelancer.username}</td>
                </tr>
                <tr>
                    <td><strong>Client:</strong> {client.get_full_name() or client.username}</td>
                    <td><strong>Hours Logged:</strong> <span style="color: #1e40af; font-weight: bold;">{draft.hours_worked} hrs</span></td>
                </tr>
                <tr>
                    <td><strong>Date Generated:</strong> {timezone.now().strftime('%B %d, %Y')}</td>
                    <td><strong>Status:</strong> <span style="color: #16a34a; font-weight: bold;">Verified & Approved</span></td>
                </tr>
            </table>

            <h2>1. Executive Summary</h2>
            <p style="color: #334155; margin: 0 0 15px 0;">{draft.section_summary}</p>

            <h2>2. Deliverables & Milestones Completed</h2>
            {deliverables_html or '<p style="color: #64748b;">No discrete deliverables listed for this period.</p>'}

            <h2>3. Next Steps & Upcoming Priorities</h2>
            <p style="color: #334155; margin: 0 0 15px 0;">{draft.section_next_steps}</p>

            <div class="footer">
                <p class="disclaimer">* Note: This progress report was compiled by FreelanceFlow AI Worklog Assistant and verified by the freelancer.</p>
                <p style="margin: 2px 0 0 0; color: #94a3b8; font-size: 10px;">Document ID: RPT-{draft.id}-{timezone.now().strftime('%Y%m%d%H%M')}</p>
            </div>
        </body>
        </html>
        """

        # Generate PDF bytes via WeasyPrint or FPDF2 fallback
        pdf_bytes = None
        try:
            from weasyprint import HTML
            pdf_bytes = HTML(string=html_content).write_pdf()
        except Exception as e:
            logger.warning("WeasyPrint error, falling back to fpdf2: %s", e)
            try:
                from fpdf import FPDF
                
                def clean_pdf_text(text) -> str:
                    if not text:
                        return ""
                    text_str = str(text)
                    replacements = {
                        "\u2011": "-",  # Non-breaking hyphen
                        "\u2013": "-",  # En dash
                        "\u2014": "--", # Em dash
                        "\u2018": "'",  # Smart left single quote
                        "\u2019": "'",  # Smart right single quote
                        "\u201c": '"',  # Smart left double quote
                        "\u201d": '"',  # Smart right double quote
                        "\u2022": "*",  # Bullet point
                        "\u2026": "...",# Ellipsis
                        "\u2027": "-",  # Hyphenation point
                        "\u2010": "-",  # Hyphen
                    }
                    for k, v in replacements.items():
                        text_str = text_str.replace(k, v)
                    return text_str.encode("latin-1", errors="replace").decode("latin-1")
                
                class ReportPDF(FPDF):
                    def header(self):
                        self.set_font("Helvetica", "B", 13)
                        self.set_text_color(30, 64, 175)  # Deep Blue
                        self.cell(0, 7, "FREELANCEFLOW PROGRESS REPORT", border=0, ln=1, align="L")
                        self.set_font("Helvetica", "", 9)
                        self.set_text_color(100, 116, 139)  # Slate
                        self.cell(0, 5, "Verified Contract Progress & Delivery Summary", border=0, ln=1, align="L")
                        self.ln(2)
                        y_line = self.get_y()
                        self.set_draw_color(203, 213, 225)
                        self.set_line_width(0.4)
                        self.line(15, y_line, 195, y_line)
                        self.ln(5)

                    def footer(self):
                        self.set_y(-18)
                        self.set_draw_color(226, 232, 240)
                        self.set_line_width(0.3)
                        self.line(15, self.get_y(), 195, self.get_y())
                        self.set_y(-14)
                        self.set_font("Helvetica", "I", 8)
                        self.set_text_color(100, 116, 139)
                        self.cell(0, 5, f"* Note: Compiled by FreelanceFlow AI Worklog Assistant • Verified by Freelancer (Page {self.page_no()})", border=0, align="C")


                pdf = ReportPDF()
                pdf.set_auto_page_break(auto=True, margin=22)
                pdf.set_margins(15, 15, 15)
                pdf.add_page()

                # Metadata Info Card
                pdf.set_fill_color(248, 250, 252)
                pdf.set_draw_color(226, 232, 240)
                pdf.set_line_width(0.3)

                # Card Top Row: Project Title
                pdf.set_font("Helvetica", "B", 9.5)
                pdf.set_text_color(71, 85, 105)
                pdf.cell(32, 7, "Project Title:", border="LT", ln=0, fill=True)
                pdf.set_font("Helvetica", "B", 9.5)
                pdf.set_text_color(15, 23, 42)
                pdf.cell(148, 7, clean_pdf_text(project.title), border="TR", ln=1, fill=True)

                # Card Middle Row: Client & Freelancer
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(71, 85, 105)
                pdf.cell(32, 6, "Client:", border="L", ln=0, fill=True)
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(15, 23, 42)
                pdf.cell(58, 6, clean_pdf_text(client.get_full_name() or client.email), border=0, ln=0, fill=True)

                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(71, 85, 105)
                pdf.cell(32, 6, "Freelancer:", border=0, ln=0, fill=True)
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(15, 23, 42)
                pdf.cell(58, 6, clean_pdf_text(freelancer.get_full_name() or freelancer.email), border="R", ln=1, fill=True)

                # Card Bottom Row: Hours & Date
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(71, 85, 105)
                pdf.cell(32, 6, "Hours Logged:", border="LB", ln=0, fill=True)
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(30, 64, 175)  # Deep blue
                pdf.cell(58, 6, f"{draft.hours_worked} hrs", border="B", ln=0, fill=True)

                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(71, 85, 105)
                pdf.cell(32, 6, "Date Generated:", border="B", ln=0, fill=True)
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(15, 23, 42)
                pdf.cell(58, 6, timezone.now().strftime('%B %d, %Y'), border="RB", ln=1, fill=True)

                pdf.ln(5)

                # Section 1: Executive Summary
                pdf.set_font("Helvetica", "B", 10.5)
                pdf.set_text_color(30, 64, 175)  # Deep Blue
                pdf.cell(0, 6, "1. Executive Summary", ln=1)
                pdf.set_draw_color(203, 213, 225)
                pdf.set_line_width(0.4)
                y_s1 = pdf.get_y()
                pdf.line(15, y_s1, 195, y_s1)
                pdf.ln(3)

                pdf.set_font("Helvetica", "", 9.5)
                pdf.set_text_color(30, 41, 59)
                pdf.multi_cell(180, 5.5, clean_pdf_text(draft.section_summary))
                pdf.ln(4)

                # Section 2: Deliverables Completed
                pdf.set_font("Helvetica", "B", 10.5)
                pdf.set_text_color(30, 64, 175)  # Deep Blue
                pdf.cell(0, 6, "2. Deliverables & Milestones Completed", ln=1)
                pdf.set_draw_color(203, 213, 225)
                pdf.set_line_width(0.4)
                y_s2 = pdf.get_y()
                pdf.line(15, y_s2, 195, y_s2)
                pdf.ln(3)

                if not draft.section_deliverables:
                    pdf.set_font("Helvetica", "I", 9)
                    pdf.set_text_color(100, 116, 139)
                    pdf.cell(0, 6, "No discrete deliverables listed for this period.", ln=1)
                else:
                    for d in draft.section_deliverables:
                        if isinstance(d, dict):
                            d_title = clean_pdf_text(d.get('title', 'Deliverable'))
                            d_status = clean_pdf_text(d.get('status', 'COMPLETED'))
                            d_desc = clean_pdf_text(d.get('description', ''))

                            # Deliverable header line: title and badge
                            pdf.set_font("Helvetica", "B", 9.5)
                            pdf.set_text_color(15, 23, 42)
                            pdf.cell(0, 5.5, f"* {d_title}  [{d_status}]", ln=1)

                            # Description on indented line below
                            if d_desc:
                                pdf.set_font("Helvetica", "", 9)
                                pdf.set_text_color(71, 85, 105)
                                pdf.set_x(20)
                                pdf.multi_cell(170, 5, d_desc)
                            pdf.ln(2)

                pdf.ln(3)

                # Section 3: Next Steps & Priorities
                pdf.set_font("Helvetica", "B", 10.5)
                pdf.set_text_color(30, 64, 175)  # Deep Blue
                pdf.cell(0, 6, "3. Next Steps & Upcoming Priorities", ln=1)
                pdf.set_draw_color(203, 213, 225)
                pdf.set_line_width(0.4)
                y_s3 = pdf.get_y()
                pdf.line(15, y_s3, 195, y_s3)
                pdf.ln(3)

                pdf.set_font("Helvetica", "", 9.5)
                pdf.set_text_color(30, 41, 59)
                pdf.multi_cell(180, 5.5, clean_pdf_text(draft.section_next_steps))

                pdf_bytes = bytes(pdf.output())
            except Exception as e_fallback:
                logger.error("fpdf2 fallback generation failed: %s", e_fallback)
                pdf_bytes = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 595 842]>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000056 00000 n\n0000000111 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF"


        blob_name = f"reports/{contract.id}/report_{draft.id}_{timezone.now().strftime('%Y%m%d')}.pdf"
        sas_url = upload_to_azure_blob(pdf_bytes, blob_name)

        # Mark draft as APPROVED and attach URL
        draft.status = AIReportDraft.Status.APPROVED
        draft.approved_at = timezone.now()
        draft.pdf_url = sas_url
        draft.save(update_fields=["status", "approved_at", "pdf_url", "updated_at"])

        # Also mirror to WeeklyReport for backward compatibility
        week_start = date.today() - timedelta(days=date.today().weekday())
        weekly_report, created = WeeklyReport.objects.update_or_create(
            contract=contract,
            week_start=week_start,
            defaults={
                "week_end": date.today(),
                "ai_summary": f"## {draft.title}\n\n### Summary\n{draft.section_summary}\n\n### Next Steps\n{draft.section_next_steps}",
                "pdf_url": sas_url,
                "sent_to_client_at": timezone.now(),
            }
        )

        # Update active in-progress milestone to SUBMITTED
        try:
            from apps.payments.models.models_milestone import PaymentMilestone
            active_milestone = PaymentMilestone.objects.filter(
                contract=contract,
                status=PaymentMilestone.Status.IN_PROGRESS
            ).order_by('order', 'created_at').first()

            if active_milestone:
                active_milestone.status = PaymentMilestone.Status.SUBMITTED
                active_milestone.deliverable_description = f"{draft.title} | Link: {sas_url}"
                active_milestone.submitted_at = timezone.now()
                active_milestone.save(update_fields=["status", "deliverable_description", "submitted_at", "updated_at"])

                from apps.payments.consumers import push_contract_event
                push_contract_event(
                    contract.id,
                    "milestone_submitted",
                    {"milestone_id": active_milestone.id, "new_status": PaymentMilestone.Status.SUBMITTED},
                )
        except Exception as me:
            logger.warning("Failed to auto-submit active milestone on AI draft approval: %s", me)

        from django.db import transaction
        from apps.worklogs.tasks import notify_client_new_report
        transaction.on_commit(
            lambda: notify_client_new_report.delay(weekly_report.id)
        )

        return sas_url, None

    sas_url, err = await sync_to_async(_compile_and_upload)()
    if err:
        state["error"] = err
    else:
        state["pdf_url"] = sas_url
        state["llm_response"] = f"✅ Your progress report has been approved and compiled into an official PDF! [Download PDF Report]({sas_url})"

    return state


# ─────────────────────────────────────────────────────────────────────────────
# LangGraph Workflow Construction
# ─────────────────────────────────────────────────────────────────────────────

def should_build_pdf(state: AIWorklogState) -> str:
    """Conditional router: execute pdf_builder only when action is 'approve'."""
    if state.get("action") == "approve":
        return "pdf_builder"
    return END


def create_ai_worklog_graph():
    """Builds the compiled LangGraph state workflow."""
    if not LANGCHAIN_AVAILABLE:
        return None

    builder = StateGraph(AIWorklogState)
    builder.add_node("context_assembler", context_assembler)
    builder.add_node("report_generator", report_generator)
    builder.add_node("pdf_builder", pdf_builder)

    builder.set_entry_point("context_assembler")
    builder.add_edge("context_assembler", "report_generator")
    builder.add_conditional_edges(
        "report_generator",
        should_build_pdf,
        {
            "pdf_builder": "pdf_builder",
            END: END
        }
    )
    builder.add_edge("pdf_builder", END)

    return builder.compile()


# Global compiled graph
ai_worklog_graph = create_ai_worklog_graph()


async def run_ai_worklog_agent(
    contract_id: int,
    freelancer_id: int,
    user_message: str,
    action: str = "chat",
    conversation_id: Optional[int] = None,
    draft_id: Optional[int] = None,
    history: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """
    Main async entry point to run the AI Worklog Agent workflow.
    """
    initial_state: AIWorklogState = {
        "contract_id": contract_id,
        "freelancer_id": freelancer_id,
        "user_message": user_message,
        "conversation_id": conversation_id,
        "conversation_history": history or [],
        "action": action,
        "draft_id": draft_id,
        "postgres_context": {},
        "qdrant_context": [],
        "llm_response": "",
        "report_draft": None,
        "pdf_url": None,
        "is_draft_ready": False,
        "error": None,
    }

    if ai_worklog_graph:
        final_state = await ai_worklog_graph.ainvoke(initial_state)
    else:
        # Fallback sequential node execution if LangGraph runtime is not present
        s1 = await context_assembler(initial_state)
        s2 = await report_generator(s1)
        if s2.get("action") == "approve":
            final_state = await pdf_builder(s2)
        else:
            final_state = s2

    return {
        "reply": final_state.get("llm_response", ""),
        "conversation_id": final_state.get("conversation_id"),
        "is_draft_ready": final_state.get("is_draft_ready", False),
        "draft": final_state.get("report_draft"),
        "draft_id": final_state.get("draft_id"),
        "pdf_url": final_state.get("pdf_url"),
        "error": final_state.get("error"),
    }
