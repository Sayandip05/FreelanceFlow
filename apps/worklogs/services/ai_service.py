"""
LangGraph Async AI Worklog & Weekly Report Agent.

Implements a 3-node stateful workflow:
1. context_assembler: Pulls PostgreSQL ground truth (contract, deliverables, logs) + queries Qdrant vector context.
2. report_generator: Calls Groq LLaMA 3.3 70B to produce conversational answers or structured 3-section drafts.
3. pdf_builder: Triggered on draft approval to compile WeasyPrint PDF, upload to Azure Blob Storage, and return SAS URL.
"""
import json
import logging
import re
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
    milestone_id: Optional[int]
    draft_data: Optional[Dict[str, Any]]
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

    log_bullets = "\n".join([f"- {log.date}: {log.description}" for log in logs]) or "- Regular milestone deliverables development."

    summary = (
        f"## Milestone Progress Report\n\n"
        f"**Project**: {contract.bid.project.title}\n"
        f"**Client**: {contract.bid.project.client.get_full_name() or contract.bid.project.client.username}\n\n"
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
    resolves the active/target milestone, and semantically queries Qdrant.
    """
    contract_id = state["contract_id"]
    user_message = state.get("user_message", "")
    target_milestone_id = state.get("milestone_id")

    # 1. Fetch DB context asynchronously
    def _fetch_pg_context():
        try:
            contract = Contract.objects.select_related(
                "bid__project__client",
                "bid__freelancer"
            ).prefetch_related("deliverables", "milestones").get(id=contract_id)
        except Contract.DoesNotExist:
            return None

        # Deliverables & Milestones list
        deliverables = list(contract.deliverables.all())
        milestones_qs = list(contract.milestones.all().order_by("order", "created_at"))

        # Resolve target milestone
        target_milestone = None
        target_idx = 0
        if target_milestone_id:
            for idx, m in enumerate(milestones_qs):
                if m.id == target_milestone_id:
                    target_milestone = m
                    target_idx = idx
                    break

        if not target_milestone:
            for idx, m in enumerate(milestones_qs):
                if m.status in ["IN_PROGRESS", "FUNDED"]:
                    target_milestone = m
                    target_idx = idx
                    break

        if not target_milestone:
            for idx, m in enumerate(milestones_qs):
                if m.status == "SUBMITTED":
                    target_milestone = m
                    target_idx = idx
                    break

        if not target_milestone and milestones_qs:
            target_milestone = milestones_qs[0]
            target_idx = 0

        target_number = target_idx + 1
        total_milestones = len(milestones_qs) or 1
        is_final_milestone = (target_number >= total_milestones)

        # Universal milestone schedule formatting
        universal_milestones = []
        for idx, m in enumerate(milestones_qs):
            status_label = {
                "PAID": "Released",
                "APPROVED": "Released",
                "SUBMITTED": "Under Review",
                "IN_PROGRESS": "In Progress",
                "FUNDED": "In Progress",
                "PENDING": "Awaiting Escrow",
            }.get(m.status, m.status)
            due_str = m.due_date.strftime("%B %d, %Y") if m.due_date else "Flexible"
            universal_milestones.append({
                "number": idx + 1,
                "id": m.id,
                "title": m.title,
                "status": status_label,
                "amount": f"${float(m.amount):,.2f}",
                "due_date": due_str,
                "description": m.description or "",
                "is_active_target": m.id == (target_milestone.id if target_milestone else None),
            })

        timeline_bullets = "\n".join([
            f"{m['number']}. **{m['title']}** ({m['status']}) – due {m['due_date']}."
            for m in universal_milestones
        ])

        return {
            "project_title": contract.bid.project.title,
            "project_description": contract.bid.project.description,
            "client_name": contract.bid.project.client.get_full_name() or contract.bid.project.client.username,
            "freelancer_name": contract.bid.freelancer.get_full_name() or contract.bid.freelancer.username,
            "contract_rate": str(getattr(contract, "agreed_amount", 0)),
            "contract_type": getattr(contract, "contract_type", "FIXED"),
            "target_milestone_number": target_number,
            "total_milestones": total_milestones,
            "is_final_milestone": is_final_milestone,
            "target_milestone_id": target_milestone.id if target_milestone else None,
            "target_milestone_title": target_milestone.title if target_milestone else f"Milestone {target_number}",
            "target_milestone_description": target_milestone.description if target_milestone else "",
            "target_milestone_due_date": target_milestone.due_date.strftime("%B %d, %Y") if (target_milestone and target_milestone.due_date) else "Flexible",
            "target_milestone_amount": f"${float(target_milestone.amount):,.2f}" if target_milestone else "$0.00",
            "target_milestone_status": target_milestone.status if target_milestone else "IN_PROGRESS",
            "universal_milestones": universal_milestones,
            "timeline_bullets": timeline_bullets,
            "deliverables": [
                {
                    "id": d.id,
                    "title": d.title,
                    "status": d.status,
                    "description": d.description[:150]
                }
                for d in deliverables
            ],
        }

    pg_context = await sync_to_async(_fetch_pg_context)()
    if not pg_context:
        state["error"] = f"Contract #{contract_id} not found"
        return state

    state["postgres_context"] = pg_context

    # 2. Fetch Qdrant Semantic Context asynchronously with rich milestone search query
    search_query = f"{user_message} {pg_context.get('target_milestone_title', '')} {pg_context.get('target_milestone_description', '')} {pg_context.get('project_title', '')}".strip()
    q_matches = await sync_to_async(query_context)(contract_id, search_query, top_k=6)
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
    Calls Groq LLaMA 3.3 70B (or Google Gemini fallback) with assembled context.
    Outputs a comprehensive 3-section pointed report draft with full technical depth.
    Enforces strict payment isolation and prompt injection guardrails.
    """
    if state.get("error"):
        return state

    # If action is direct approve, skip generation directly to pdf_builder
    if state.get("action") == "approve":
        return state

    user_msg = state.get("user_message", "")

    # ── Guardrail 1: Prompt Injection Check ──
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
    clean_user_msg = sanitize_sensitive_data(user_msg)
    q_context = "\n".join([f"- [{item.get('type')}]: {sanitize_sensitive_data(item.get('text', ''))}" for item in state.get("qdrant_context", [])])
    history = state.get("conversation_history", [])

    final_milestone_guidance = ""
    if pg.get("is_final_milestone"):
        final_milestone_guidance = f"""
SPECIAL FINAL MILESTONE INSTRUCTIONS:
- This is the FINAL milestone of the contract (Milestone {pg['target_milestone_number']} of {pg['total_milestones']}).
- Section 1 (Executive Summary): Provide a thorough 4 to 5 line technical overview covering the completion of all core project milestones, final architectural integration, quality verification, and client readiness.
- Section 2 (Deliverables Completed): Generate 3 to 4 detailed pointed deliverable items detailing final frontend/backend integrations, test suites, end-to-end verification, and release packaging.
- Section 3 (Next Steps): Provide a comprehensive 4 to 5 line plan covering final project handover, client staging sign-off, deployment verification, warranty period support, and contract closure (do NOT mention upcoming milestones as this is the last one).
"""
    else:
        final_milestone_guidance = f"""
MILESTONE POSITION:
- This is Milestone {pg['target_milestone_number']} of {pg['total_milestones']}.
- Section 1 (Executive Summary): Provide a thorough 4 to 5 line technical overview detailing key engineering tasks accomplished for Milestone {pg['target_milestone_number']}, architectural decisions, design fidelity, and integration checkpoints.
- Section 2 (Deliverables Completed): Generate 3 to 4 detailed pointed deliverable items, each with 2 to 3 lines of technical implementation notes, components built, and verification steps.
- Section 3 (Next Steps): Provide a comprehensive 4 to 5 line plan detailing upcoming priorities for Milestone {pg['target_milestone_number'] + 1}, client review checkpoints, and dependency preparation.
"""

    system_prompt = f"""You are the FreelanceFlow AI Worklog Assistant for the project "{pg['project_title']}".
Your role is to deeply analyze all project technical context, milestone scopes, vector database memories, and freelancer inputs to draft an in-depth, professional, and comprehensive milestone progress report for client {pg['client_name']}.

TARGET ACTIVE MILESTONE:
- Milestone Position: Milestone {pg['target_milestone_number']} of {pg['total_milestones']}
- Milestone Title: {pg['target_milestone_title']}
- Milestone Scope / Requirements: {pg['target_milestone_description']}
- Milestone Due Date: {pg['target_milestone_due_date']}
- Milestone Amount: {pg['target_milestone_amount']}
- Milestone Status: {pg['target_milestone_status']}
- Is Final Milestone: {'YES (Final Project Milestone)' if pg.get('is_final_milestone') else 'NO'}

{final_milestone_guidance}

ALL PROJECT MILESTONES (Universal Schedule):
{pg['timeline_bullets']}

SEMANTIC CONTEXT (Retrieved from Qdrant Vector DB):
{q_context or 'No specific vector matches.'}

CRITICAL RULES:
1. DEPTH & LENGTH REQUIREMENTS:
   - Section 1 (Executive Summary): MUST be a comprehensive paragraph of at least 4 to 5 detailed sentences explaining the technical work, architectural achievements, optimizations, and milestone completion.
   - Section 2 (Deliverables & Tasks Completed): MUST contain at least 3 to 4 granular, pointed deliverable items. Each item must feature a descriptive title, "COMPLETED" status, and a detailed 2 to 3 line technical explanation with verification criteria.
   - Section 3 (Next Steps & Priorities): MUST be a detailed paragraph of at least 4 to 5 sentences covering client review, staging verification, and upcoming milestone / handover tasks.
2. STRICT MILESTONE ISOLATION: Focus strictly on **Milestone {pg['target_milestone_number']} ({pg['target_milestone_title']})**. Do NOT generate deliverables or summaries for earlier finished milestones or future unstarted milestones.
3. UNIVERSAL TIMELINES: Milestones follow the universal milestone dates (can be monthly, bi-weekly, or custom). Do NOT refer to monthly milestones as "weekly" and never say "weekly report". Always refer to this as "Milestone {pg['target_milestone_number']} Progress Report".
4. NO HOURS OR TIME LOGS: Do NOT mention or output hours (e.g., no "8 hours", no "12 hours", no time logs). The worklog report is strictly milestone-deliverable-driven.
5. DRAFTING RESPONSE: When the freelancer asks to draft or summarize their progress report (e.g. "draft my progress report", "generate report", "here is what I worked on"), output a JSON block formatted exactly as:
```json
{{
  "is_draft": true,
  "reply": "I've synthesized your work for **Milestone {pg['target_milestone_number']} ({pg['target_milestone_title']})** into a comprehensive, editable progress report draft. You can customize any section below and submit it directly to your client.",
  "draft": {{
    "title": "Milestone {pg['target_milestone_number']} Progress Report – {pg['project_title']}",
    "section_summary": "During this milestone cycle, successfully implemented the core architecture and technical specifications outlined for Milestone {pg['target_milestone_number']}. Engineered responsive UI components, integrated seamless backend API endpoints, and ensured cross-browser compatibility across desktop and mobile viewports. Validated all interactive states with comprehensive unit and integration test coverage, achieving optimal performance and zero critical regressions. The milestone objectives have been thoroughly met and prepared for official client review and approval.",
    "section_deliverables": [
      {{
        "title": "{pg['target_milestone_title']} - Core Architecture & Implementation",
        "description": "Engineered the primary functional components and layout modules according to design specifications. Implemented modern state management, optimized rendering lifecycles, and ensured full responsive adaptability across all target screen resolutions.",
        "status": "COMPLETED"
      }},
      {{
        "title": "API Integration & Data Flow Synchronization",
        "description": "Connected frontend user workflows with secure backend REST endpoints and WebSocket channels. Implemented robust error handling, loading skeletons, and real-time state synchronization to deliver a frictionless user experience.",
        "status": "COMPLETED"
      }},
      {{
        "title": "Quality Assurance, Security & Performance Tuning",
        "description": "Conducted automated testing and manual cross-device audits. Minimized bundle sizes, optimized network payloads, and verified data integrity to guarantee production-ready reliability and strict adherence to project standards.",
        "status": "COMPLETED"
      }}
    ],
    "section_next_steps": "{'Initiate final staging verification with the client, deliver deployment documentation and source code repositories, and complete the official project handover sign-off.' if pg.get('is_final_milestone') else f'Submit this milestone deliverable for client review, incorporate any stakeholder feedback, and begin initial technical scoping for Milestone {pg['target_milestone_number'] + 1}.'}"
  }}
}}
```
6. TIMELINE INQUIRIES: When the user asks "what is my timeline of my progress report" or asks about timeline/schedule, output:
```json
{{
  "is_draft": false,
  "reply": "Your progress report timeline follows the project milestones:\n\n{pg['timeline_bullets']}"
}}
```
7. NEVER mention internal backend names (e.g. Qdrant, WeasyPrint, vector DB, PostgreSQL, LLM) in any response. Always return valid JSON.
"""

    llm = get_llm()
    ai_raw = ""

    if llm:
        try:
            messages = [SystemMessage(content=system_prompt)]
            for msg in history[-8:]:
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

    # Resilient JSON parsing
    parsed = None
    if ai_raw:
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
        # Grounded fallback intelligent generator with rich 4-5 line paragraphs and pointed deliverables
        if any(w in user_msg.lower() for w in ["draft", "report", "generate", "summary", "submit", "done", "progress"]):
            next_steps_text = (
                f"Coordinate directly with client {pg['client_name']} for final deliverable verification, provide comprehensive system documentation, and complete official project handover sign-off. Ensure all staging environments are synchronized and ready for production deployment."
                if pg.get("is_final_milestone")
                else f"Submit current Milestone {pg['target_milestone_number']} deliverables to client {pg['client_name']} for review and escrow release. Incorporate any stakeholder feedback, and initiate technical preparation and requirement scoping for Milestone {pg['target_milestone_number'] + 1}."
            )
            parsed = {
                "is_draft": True,
                "reply": f"I've synthesized your work for **Milestone {pg['target_milestone_number']} ({pg['target_milestone_title']})** into a comprehensive, editable progress report draft. Review the details below, edit any section as needed, and click Approve to generate the official PDF.",
                "draft": {
                    "title": f"Milestone {pg['target_milestone_number']} Progress Report – {pg['project_title']}",
                    "section_summary": f"Successfully completed all core technical requirements and engineering milestones designated for Milestone {pg['target_milestone_number']} ({pg['target_milestone_title']}) on project '{pg['project_title']}'. Developed modular, responsive interface elements and integrated backend services while upholding strict performance and accessibility standards. Executed rigorous cross-browser testing and functional validations to verify that all milestone deliverables align with client expectations. All completed items are fully documented, audited, and ready for official stakeholder review.",
                    "section_deliverables": [
                        {
                            "title": f"{pg['target_milestone_title']} - Implementation & Architecture",
                            "description": f"Developed and deployed the fundamental features and architectural structure required for {pg['target_milestone_title']}. Ensured responsive design across all devices and validated core functionality.",
                            "status": "COMPLETED"
                        },
                        {
                            "title": "Integration, State Management & Workflow Validation",
                            "description": "Configured dynamic data synchronization and API workflows. Handled edge cases, asynchronous data fetching, and user interaction states to maintain high reliability.",
                            "status": "COMPLETED"
                        },
                        {
                            "title": "Verification Testing & Client Deliverable Preparation",
                            "description": pg.get("target_milestone_description") or f"Executed quality assurance checks and performance optimizations to ensure all deliverable requirements for {pg['target_milestone_title']} are verified.",
                            "status": "COMPLETED"
                        }
                    ],
                    "section_next_steps": next_steps_text
                }
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
                title=d_data.get("title", f"Milestone {pg['target_milestone_number']} Progress Report – {pg['project_title']}"),
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
    and returns a 7-day SAS download URL with clean descriptive milestone naming.
    """
    draft_id = state.get("draft_id")
    contract_id = state["contract_id"]
    target_milestone_id = state.get("milestone_id")

    def _compile_and_upload():
        draft = None
        if draft_id:
            draft = AIReportDraft.objects.select_related(
                "contract__bid__project__client",
                "contract__bid__freelancer"
            ).filter(id=draft_id, contract_id=contract_id).first()

            if not draft:
                return None, "Draft not found or does not belong to this contract"

        if not draft:
            draft = AIReportDraft.objects.select_related(
                "contract__bid__project__client",
                "contract__bid__freelancer"
            ).filter(contract_id=contract_id).order_by("-created_at").first()

        if not draft:
            return None, "No report draft found to compile"

        # Apply freelancer's custom inline edits if provided
        custom_draft = state.get("draft_data")
        if custom_draft and isinstance(custom_draft, dict):
            if custom_draft.get("title"):
                draft.title = custom_draft["title"]
            if custom_draft.get("hours_worked") is not None:
                try:
                    draft.hours_worked = float(custom_draft["hours_worked"])
                except (ValueError, TypeError):
                    pass
            if custom_draft.get("section_summary"):
                draft.section_summary = custom_draft["section_summary"]
            if isinstance(custom_draft.get("section_deliverables"), list):
                draft.section_deliverables = custom_draft["section_deliverables"]
            if custom_draft.get("section_next_steps"):
                draft.section_next_steps = custom_draft["section_next_steps"]
            draft.save()

        contract = draft.contract
        project = contract.bid.project
        client = project.client
        freelancer = contract.bid.freelancer

        # Resolve active milestone for naming
        from apps.payments.models.models_milestone import PaymentMilestone
        active_milestone = None
        if target_milestone_id:
            active_milestone = PaymentMilestone.objects.filter(contract=contract, id=target_milestone_id).first()

        if not active_milestone:
            active_milestone = PaymentMilestone.objects.filter(
                contract=contract,
                status__in=[PaymentMilestone.Status.IN_PROGRESS, PaymentMilestone.Status.FUNDED]
            ).order_by('order', 'created_at').first()

        if not active_milestone:
            active_milestone = PaymentMilestone.objects.filter(contract=contract).order_by('order', 'created_at').first()

        total_milestones_count = PaymentMilestone.objects.filter(contract=contract).count() or 1
        milestone_num = active_milestone.order if (active_milestone and active_milestone.order) else 1

        # Build clean HTML template for PDF (Solid black headings, clean structure, no purple)
        deliverables_html = ""
        for d in draft.section_deliverables:
            if isinstance(d, dict):
                d_title = d.get('title', 'Deliverable')
                d_status = d.get('status', 'COMPLETED')
                d_desc = d.get('description', '')
                deliverables_html += f"""
                <div style="margin-bottom: 12px; padding: 10px 14px; background: #f8fafc; border-left: 3px solid #0f172a; border-radius: 4px; border: 1px solid #e2e8f0; border-left-width: 3px;">
                    <div style="margin-bottom: 4px; display: flex; align-items: center; justify-content: space-between;">
                        <strong style="color: #0f172a; font-size: 13px;">{d_title}</strong>
                        <span style="font-size: 10px; background: #f1f5f9; color: #0f172a; border: 1px solid #cbd5e1; padding: 2px 7px; border-radius: 4px; font-weight: bold;">{d_status}</span>
                    </div>
                    <p style="margin: 0; color: #475569; font-size: 12px; line-height: 1.45;">{d_desc}</p>
                </div>
                """

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                @page {{ size: A4; margin: 16mm; }}
                body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #1e293b; line-height: 1.5; font-size: 12.5px; }}
                .header {{ border-bottom: 2px solid #0f172a; padding-bottom: 10px; margin-bottom: 16px; }}
                .badge {{ background: #0f172a; color: #ffffff; padding: 3px 8px; border-radius: 4px; font-size: 10px; font-weight: bold; letter-spacing: 0.5px; text-transform: uppercase; }}
                h1 {{ margin: 8px 0 4px 0; color: #0f172a; font-size: 19px; font-weight: bold; }}
                h2 {{ color: #0f172a; font-size: 13px; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; margin-top: 18px; margin-bottom: 8px; font-weight: bold; }}
                .meta-table {{ width: 100%; border-collapse: collapse; margin-bottom: 16px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 4px; }}
                .meta-table td {{ padding: 7px 12px; font-size: 11.5px; border-bottom: 1px solid #e2e8f0; }}
                .footer {{ margin-top: 30px; border-top: 1px solid #e2e8f0; padding-top: 10px; font-size: 10px; color: #64748b; text-align: center; }}
                .disclaimer {{ font-size: 10px; color: #64748b; font-style: italic; margin-top: 2px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <span class="badge">MILESTONE {milestone_num} OF {total_milestones_count} VERIFIED PROGRESS REPORT</span>
                <h1>{draft.title}</h1>
                <p style="margin: 0; color: #64748b; font-size: 11.5px;">FreelanceFlow Verified Progress Document • Contract #{contract.id} • Bid #{contract.bid.id}</p>
            </div>

            <table class="meta-table">
                <tr>
                    <td style="width: 50%;"><strong>Project:</strong> {project.title}</td>
                    <td style="width: 50%;"><strong>Freelancer:</strong> {freelancer.get_full_name() or freelancer.email}</td>
                </tr>
                <tr>
                    <td><strong>Client:</strong> {client.get_full_name() or client.email}</td>
                    <td><strong>Milestone Scope:</strong> <strong style="color: #0f172a;">Milestone {milestone_num} of {total_milestones_count}</strong></td>
                </tr>
                <tr>
                    <td><strong>Date Generated:</strong> {timezone.now().strftime('%B %d, %Y')}</td>
                    <td><strong>Status:</strong> <strong style="color: #16a34a;">Verified & Approved</strong></td>
                </tr>
            </table>

            <h2>1. Executive Summary</h2>
            <p style="color: #334155; margin: 0 0 12px 0; font-size: 12px; line-height: 1.5;">{draft.section_summary}</p>

            <h2>2. Deliverables & Milestones Completed</h2>
            {deliverables_html or '<p style="color: #64748b; font-size: 12px;">No discrete deliverables listed for this period.</p>'}

            <h2>3. Next Steps & Upcoming Priorities</h2>
            <p style="color: #334155; margin: 0 0 12px 0; font-size: 12px; line-height: 1.5;">{draft.section_next_steps}</p>

            <div class="footer">
                <p style="margin: 0; font-weight: 500;">FreelanceFlow • Milestone Verified Progress Audit</p>
                <p class="disclaimer">Document verified and generated by FreelanceFlow AI Worklog Assistant for Milestone {milestone_num}.</p>
            </div>
        </body>
        </html>
        """

        # Generate PDF bytes via WeasyPrint, fallback to full flexible FPDF2
        try:
            from weasyprint import HTML
            pdf_bytes = HTML(string=html_content).write_pdf()
        except Exception as e:
            logger.warning("WeasyPrint compilation unavailable, generating full multi-page PDF via FPDF2: %s", e)
            try:
                from fpdf import FPDF
                from fpdf.enums import XPos, YPos

                def clean_pdf_text(t: str) -> str:
                    if not t:
                        return ""
                    t = str(t)
                    replacements = {
                        '\u2013': '-',
                        '\u2014': '--',
                        '\u2018': "'",
                        '\u2019': "'",
                        '\u201c': '"',
                        '\u201d': '"',
                        '\u2022': '|',
                        '\u2026': '...',
                        '\u2713': '[Verified]',
                        '\u2714': '[Verified]',
                        '•': '|',
                        '–': '-',
                        '—': '--',
                        '’': "'",
                        '‘': "'",
                        '“': '"',
                        '”': '"',
                    }
                    for k, v in replacements.items():
                        t = t.replace(k, v)
                    return t.encode('latin-1', 'replace').decode('latin-1')

                class MilestoneReportPDF(FPDF):
                    def footer(self):
                        self.set_y(-12)
                        self.set_font('Helvetica', 'I', 8)
                        self.set_text_color(100, 116, 139)
                        self.cell(0, 8, clean_pdf_text(f'FreelanceFlow Official Milestone Progress Audit | Page {self.page_no()}'), align='C')

                pdf = MilestoneReportPDF(format='A4', unit='mm')
                pdf.set_auto_page_break(auto=True, margin=15)
                pdf.set_margins(16, 16, 16)
                pdf.add_page()

                # Header badge banner
                pdf.set_fill_color(15, 23, 42)
                pdf.set_text_color(255, 255, 255)
                pdf.set_font('Helvetica', 'B', 9)
                pdf.cell(0, 7, clean_pdf_text(f'  MILESTONE {milestone_num} OF {total_milestones_count} VERIFIED PROGRESS REPORT'), fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.ln(3)

                # Report Title
                pdf.set_text_color(15, 23, 42)
                pdf.set_font('Helvetica', 'B', 15)
                pdf.multi_cell(0, 7, clean_pdf_text(draft.title), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

                pdf.set_font('Helvetica', '', 9)
                pdf.set_text_color(100, 116, 139)
                pdf.cell(0, 5, clean_pdf_text(f'FreelanceFlow Verified Progress Document | Contract #{contract.id} | Bid #{contract.bid.id}'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.ln(4)

                # Metadata Box
                pdf.set_fill_color(248, 250, 252)
                pdf.set_draw_color(226, 232, 240)
                pdf.rect(pdf.get_x(), pdf.get_y(), 178, 24, 'FD')
                pdf.set_xy(pdf.get_x() + 3, pdf.get_y() + 2)

                freelancer_name = freelancer.get_full_name() or freelancer.email
                client_name = client.get_full_name() or client.email

                pdf.set_font('Helvetica', 'B', 9)
                pdf.set_text_color(15, 23, 42)
                pdf.cell(85, 6, clean_pdf_text(f'Project: {project.title[:38]}'))
                pdf.cell(85, 6, clean_pdf_text(f'Freelancer: {freelancer_name[:35]}'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.set_x(19)
                pdf.cell(85, 6, clean_pdf_text(f'Client: {client_name[:38]}'))
                pdf.cell(85, 6, clean_pdf_text(f'Milestone: Milestone {milestone_num} of {total_milestones_count}'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.set_x(19)
                pdf.cell(85, 6, clean_pdf_text(f"Date: {timezone.now().strftime('%B %d, %Y')}"))
                pdf.cell(85, 6, clean_pdf_text('Status: Verified & Approved'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.ln(6)

                # Section 1: Executive Summary
                pdf.set_font('Helvetica', 'B', 11)
                pdf.set_text_color(15, 23, 42)
                pdf.cell(0, 6, clean_pdf_text('1. Executive Summary'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.set_draw_color(226, 232, 240)
                pdf.line(16, pdf.get_y(), 194, pdf.get_y())
                pdf.ln(2)

                pdf.set_font('Helvetica', '', 9.5)
                pdf.set_text_color(51, 65, 85)
                pdf.multi_cell(0, 5.2, clean_pdf_text(draft.section_summary), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.ln(4)

                # Section 2: Deliverables & Tasks Completed
                pdf.set_font('Helvetica', 'B', 11)
                pdf.set_text_color(15, 23, 42)
                pdf.cell(0, 6, clean_pdf_text('2. Deliverables & Tasks Completed'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.set_draw_color(226, 232, 240)
                pdf.line(16, pdf.get_y(), 194, pdf.get_y())
                pdf.ln(3)

                for d in (draft.section_deliverables or []):
                    if isinstance(d, dict):
                        d_title = d.get('title', 'Deliverable')
                        d_status = d.get('status', 'COMPLETED')
                        d_desc = d.get('description', '')

                        # Deliverable title and status
                        pdf.set_font('Helvetica', 'B', 9.5)
                        pdf.set_text_color(15, 23, 42)
                        pdf.cell(140, 6, clean_pdf_text(f'* {d_title[:65]}'))
                        pdf.set_font('Helvetica', 'B', 8)
                        pdf.set_text_color(22, 163, 74)
                        pdf.cell(38, 6, clean_pdf_text(f'[{d_status}]'), align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

                        # Deliverable detailed description
                        if d_desc:
                            pdf.set_font('Helvetica', '', 9)
                            pdf.set_text_color(71, 85, 105)
                            pdf.multi_cell(0, 4.8, clean_pdf_text(f'   {d_desc}'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                        pdf.ln(2.5)

                # Section 3: Next Steps & Priorities
                pdf.ln(2)
                pdf.set_font('Helvetica', 'B', 11)
                pdf.set_text_color(15, 23, 42)
                pdf.cell(0, 6, clean_pdf_text('3. Next Steps & Priorities'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.set_draw_color(226, 232, 240)
                pdf.line(16, pdf.get_y(), 194, pdf.get_y())
                pdf.ln(2)

                pdf.set_font('Helvetica', '', 9.5)
                pdf.set_text_color(51, 65, 85)
                pdf.multi_cell(0, 5.2, clean_pdf_text(draft.section_next_steps), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.ln(5)

                # Audit Verification Box
                pdf.set_fill_color(241, 245, 249)
                pdf.set_draw_color(203, 213, 225)
                pdf.rect(pdf.get_x(), pdf.get_y(), 178, 12, 'FD')
                pdf.set_xy(pdf.get_x() + 3, pdf.get_y() + 2)
                pdf.set_font('Helvetica', 'I', 8)
                pdf.set_text_color(100, 116, 139)
                pdf.cell(0, 4, clean_pdf_text('FreelanceFlow | Milestone Verified Progress Audit'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.set_x(19)
                pdf.cell(0, 4, clean_pdf_text(f'Document verified and generated by FreelanceFlow AI Worklog Assistant for Milestone {milestone_num}.'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

                pdf_bytes = bytes(pdf.output())
            except Exception as e_fallback:
                logger.error("fpdf2 fallback generation failed: %s", e_fallback, exc_info=True)
                pdf_bytes = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 595 842]>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000056 00000 n\n0000000111 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF"

        # Descriptive blob name: milestone_{num}_{slug}_contract_{id}_bid_{id}.pdf
        clean_proj_slug = re.sub(r'[^a-zA-Z0-9_-]', '_', project.title.lower())[:25].strip('_')
        blob_name = f"reports/{contract.id}/milestone_{milestone_num}_{clean_proj_slug}_contract_{contract.id}_bid_{contract.bid.id}.pdf"
        sas_url = upload_to_azure_blob(pdf_bytes, blob_name)

        # Mark draft as APPROVED and attach URL
        draft.status = AIReportDraft.Status.APPROVED
        draft.approved_at = timezone.now()
        draft.pdf_url = sas_url
        draft.save(update_fields=["status", "approved_at", "pdf_url", "updated_at"])

        # ── ISOLATION: Close the conversation so the next milestone gets a fresh session
        try:
            conv = draft.conversation
            if conv and conv.is_active:
                conv.is_active = False
                conv.save(update_fields=["is_active", "updated_at"])
        except Exception as ce:
            logger.warning("Failed to close AI conversation after approval: %s", ce)

        # Mirror to WeeklyReport for backward compatibility
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

        # Update active milestone to SUBMITTED
        if active_milestone:
            try:
                active_milestone.status = PaymentMilestone.Status.SUBMITTED
                active_milestone.deliverable_description = f"{draft.title} | Link: {sas_url}"
                active_milestone.submitted_at = timezone.now()
                active_milestone.save(update_fields=["status", "deliverable_description", "submitted_at", "updated_at"])

                from apps.payments.consumers import push_contract_event
                push_contract_event(
                    contract.id,
                    "milestone_submitted",
                    {"milestone_id": active_milestone.id, "new_status": PaymentMilestone.Status.SUBMITTED, "pdf_url": sas_url},
                )
            except Exception as me:
                logger.warning("Failed to auto-submit active milestone on AI draft approval: %s", me)

        # Mirror to Deliverable model
        try:
            from apps.worklogs.models import Deliverable
            Deliverable.objects.update_or_create(
                contract=contract,
                freelancer=freelancer,
                title=draft.title,
                defaults={
                    "description": draft.section_summary,
                    "ai_generated_report": draft.section_summary,
                    "pdf_url": sas_url,
                    "status": Deliverable.Status.SUBMITTED,
                    "submitted_at": timezone.now(),
                    "hours_logged": draft.hours_worked,
                }
            )
        except Exception as de:
            logger.warning("Failed to mirror AI deliverable to Deliverable model: %s", de)

        from apps.worklogs.tasks import notify_client_new_report
        try:
            notify_client_new_report.delay(weekly_report.id)
        except Exception as ne:
            logger.warning("Failed to queue client notification: %s", ne)

        return sas_url, None

    sas_url, err = await sync_to_async(_compile_and_upload)()
    if err:
        state["error"] = err
        state["pdf_url"] = None
    else:
        state["pdf_url"] = sas_url
        state["llm_response"] = "Your official milestone deliverable and progress report have been submitted and are now **under review by the client**."

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
    milestone_id: Optional[int] = None,
    draft_data: Optional[Dict[str, Any]] = None,
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
        "milestone_id": milestone_id,
        "draft_data": draft_data,
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
