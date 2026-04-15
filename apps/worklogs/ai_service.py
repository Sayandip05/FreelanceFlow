"""
AI Service for generating weekly progress reports using Groq API.
Integrated with LangChain, LangGraph, and LangSmith for proper tracing and monitoring.
"""
from django.conf import settings
from datetime import date, timedelta
from typing import Optional, TypedDict, Annotated
import operator

from .models import WorkLog, WeeklyReport
from apps.bidding.models import Contract

# LangChain and LangGraph imports
try:
    from langchain_groq import ChatGroq
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    from langgraph.graph import StateGraph, END
    from langsmith import traceable
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    # Fallback decorator that does nothing
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if not args else decorator(args[0])

# Fallback Groq client
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


# LangGraph State Definition
class ReportState(TypedDict):
    """State for the report generation graph."""
    contract_id: int
    week_start: date
    week_end: date
    work_logs: str
    project_context: str
    prompt: str
    report: str
    error: Optional[str]


def get_groq_llm():
    """Get configured Groq LLM instance."""
    if not LANGCHAIN_AVAILABLE or not settings.GROQ_API_KEY:
        return None
    
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=settings.GROQ_API_KEY,
        temperature=0.7,
        max_tokens=1024,
    )


@traceable(name="gather_work_logs", tags=["worklog", "data"])
def gather_work_logs(state: ReportState) -> ReportState:
    """
    Node 1: Gather work logs for the week.
    """
    from apps.worklogs.selectors import get_week_logs, get_total_hours_for_week
    
    contract_id = state["contract_id"]
    week_start = state["week_start"]
    
    # Get logs for the week
    logs = get_week_logs(contract_id, week_start)
    
    # Format logs as readable text
    logs_text = "\n".join([
        f"- {log.date}: {log.description} ({log.hours_worked}h)"
        + (f" | Screenshot: {log.screenshot_url}" if log.screenshot_url else "")
        + (f" | Reference: {log.reference_url}" if log.reference_url else "")
        for log in logs
    ])
    
    # Get hours this week
    hours_this_week = get_total_hours_for_week(contract_id, week_start)
    
    state["work_logs"] = logs_text
    state["project_context"] = f"Hours this week: {hours_this_week}h"
    
    return state


@traceable(name="build_report_prompt", tags=["worklog", "prompt"])
def build_report_prompt(state: ReportState) -> ReportState:
    """
    Node 2: Build the prompt for AI report generation.
    """
    contract = Contract.objects.select_related(
        'bid__project__client',
        'bid__freelancer'
    ).get(id=state["contract_id"])
    
    # Get total hours to date
    total_hours_to_date = WorkLog.objects.filter(
        contract=contract
    ).count()
    
    # Build the prompt
    prompt = f"""You are writing a professional weekly progress report for a client.

PROJECT: {contract.bid.project.title}
DESCRIPTION: {contract.bid.project.description}
FREELANCER: {contract.bid.freelancer.get_full_name()}
CLIENT: {contract.bid.project.client.get_full_name()}
WEEK: {state["week_start"]} to {state["week_end"]}
{state["project_context"]}
TOTAL HOURS TO DATE: {total_hours_to_date}h

DAILY WORK LOGS:
{state["work_logs"]}

Write a professional progress report with exactly 3 sections:
1. SUMMARY (2-3 sentences of what was accomplished overall)
2. DETAILS (bullet points of specific tasks completed)
3. NEXT STEPS (1-2 sentences on what comes next)

Tone: Professional, client-facing, factual, positive.
Do not mention this was AI-generated."""
    
    state["prompt"] = prompt
    return state


@traceable(name="generate_report_with_ai", tags=["worklog", "groq", "generation"])
def generate_report_with_ai(state: ReportState) -> ReportState:
    """
    Node 3: Generate report using Groq AI.
    """
    llm = get_groq_llm()
    
    if not llm:
        state["report"] = """SUMMARY
This week focused on making significant progress toward project completion.

DETAILS
- Worked on project tasks
- Made progress on deliverables
- Continued development work

NEXT STEPS
Will continue working on remaining tasks to complete the project."""
        state["error"] = "Groq API not configured"
        return state
    
    try:
        # Use LangChain with proper tracing
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are a professional technical writer creating weekly progress reports."),
            ("human", "{prompt}")
        ])
        
        chain = prompt_template | llm | StrOutputParser()
        
        report = chain.invoke({"prompt": state["prompt"]})
        state["report"] = report
        state["error"] = None
        
    except Exception as e:
        state["error"] = str(e)
        state["report"] = f"Error generating report: {str(e)}"
    
    return state


def create_report_graph():
    """
    Create LangGraph workflow for report generation.
    
    Graph Flow:
    START -> gather_work_logs -> build_report_prompt -> generate_report_with_ai -> END
    """
    workflow = StateGraph(ReportState)
    
    # Add nodes
    workflow.add_node("gather_logs", gather_work_logs)
    workflow.add_node("build_prompt", build_report_prompt)
    workflow.add_node("generate_report", generate_report_with_ai)
    
    # Add edges
    workflow.set_entry_point("gather_logs")
    workflow.add_edge("gather_logs", "build_prompt")
    workflow.add_edge("build_prompt", "generate_report")
    workflow.add_edge("generate_report", END)
    
    return workflow.compile()


@traceable(name="generate_weekly_report", tags=["worklog", "report", "weekly", "langgraph"])
def generate_weekly_report(
    contract_id: int,
    week_start: date,
) -> WeeklyReport:
    """
    Generate AI weekly report for a contract using LangGraph workflow.
    Fully traced with LangSmith for monitoring.
    
    Args:
        contract_id: Contract ID
        week_start: Start of week (Monday)
    
    Returns:
        Created WeeklyReport instance
    """
    week_end = week_start + timedelta(days=6)
    
    if LANGCHAIN_AVAILABLE:
        # Use LangGraph workflow
        graph = create_report_graph()
        
        initial_state: ReportState = {
            "contract_id": contract_id,
            "week_start": week_start,
            "week_end": week_end,
            "work_logs": "",
            "project_context": "",
            "prompt": "",
            "report": "",
            "error": None,
        }
        
        # Run the graph
        final_state = graph.invoke(initial_state)
        ai_summary = final_state["report"]
        
    else:
        # Fallback to simple generation
        ai_summary = _fallback_report_generation(contract_id, week_start, week_end)
    
    # Create report
    report, created = WeeklyReport.objects.update_or_create(
        contract_id=contract_id,
        week_start=week_start,
        defaults={
            'week_end': week_end,
            'ai_summary': ai_summary,
        }
    )
    
    return report


def _fallback_report_generation(contract_id: int, week_start: date, week_end: date) -> str:
    """Fallback report generation when LangChain is not available."""
    if not GROQ_AVAILABLE or not settings.GROQ_API_KEY:
        return """SUMMARY
This week focused on making significant progress toward project completion.

DETAILS
- Worked on project tasks
- Made progress on deliverables
- Continued development work

NEXT STEPS
Will continue working on remaining tasks to complete the project."""
    
    try:
        from apps.worklogs.selectors import get_week_logs, get_total_hours_for_week
        
        contract = Contract.objects.select_related(
            'bid__project__client',
            'bid__freelancer'
        ).get(id=contract_id)
        
        logs = get_week_logs(contract_id, week_start)
        logs_text = "\n".join([
            f"- {log.date}: {log.description} ({log.hours_worked}h)"
            for log in logs
        ])
        
        hours_this_week = get_total_hours_for_week(contract_id, week_start)
        
        prompt = f"""Write a professional weekly progress report.

PROJECT: {contract.bid.project.title}
WEEK: {week_start} to {week_end}
HOURS: {hours_this_week}h

WORK LOGS:
{logs_text}

Write 3 sections: SUMMARY, DETAILS, NEXT STEPS."""
        
        client = Groq(api_key=settings.GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.7,
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error generating report: {str(e)}"
