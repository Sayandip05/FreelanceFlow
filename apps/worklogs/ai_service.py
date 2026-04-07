"""
AI Service for generating weekly progress reports using Anthropic API.
"""
import anthropic
from django.conf import settings
from datetime import date, timedelta

from .models import WorkLog, WeeklyReport
from apps.bidding.models import Contract


def build_prompt(contract_id: int, week_start: date, week_end: date) -> str:
    """
    Build a prompt for the AI based on contract and work logs.
    
    Args:
        contract_id: Contract ID
        week_start: Start of week (Monday)
        week_end: End of week (Sunday)
    
    Returns:
        Formatted prompt string
    """
    from apps.worklogs.selectors import get_week_logs, get_total_hours_for_week
    
    contract = Contract.objects.select_related(
        'bid__project__client',
        'bid__freelancer'
    ).get(id=contract_id)
    
    # Get logs for the week
    logs = get_week_logs(contract_id, week_start)
    
    # Format logs as readable text
    logs_text = "\n".join([
        f"- {log.date}: {log.description} ({log.hours_worked}h)"
        + (f" | Screenshot: {log.screenshot_url}" if log.screenshot_url else "")
        + (f" | Reference: {log.reference_url}" if log.reference_url else "")
        for log in logs
    ])
    
    # Get total hours to date
    total_hours_to_date = WorkLog.objects.filter(
        contract=contract
    ).count()
    
    # Get hours this week
    hours_this_week = get_total_hours_for_week(contract_id, week_start)
    
    # Build the prompt
    prompt = f"""You are writing a professional weekly progress report for a client.

PROJECT: {contract.bid.project.title}
DESCRIPTION: {contract.bid.project.description}
FREELANCER: {contract.bid.freelancer.get_full_name()}
CLIENT: {contract.bid.project.client.get_full_name()}
WEEK: {week_start} to {week_end}
HOURS THIS WEEK: {hours_this_week}h
TOTAL HOURS TO DATE: {total_hours_to_date}h

DAILY WORK LOGS:
{logs_text}

Write a professional progress report with exactly 3 sections:
1. SUMMARY (2-3 sentences of what was accomplished overall)
2. DETAILS (bullet points of specific tasks completed)
3. NEXT STEPS (1-2 sentences on what comes next)

Tone: Professional, client-facing, factual, positive.
Do not mention this was AI-generated."""
    
    return prompt


def call_ai(prompt: str) -> str:
    """
    Call Anthropic API to generate report.
    
    Args:
        prompt: The formatted prompt
    
    Returns:
        Generated report text
    """
    if not settings.ANTHROPIC_API_KEY:
        # Return placeholder if no API key configured
        return """SUMMARY
This week focused on making significant progress toward project completion.

DETAILS
- Worked on project tasks
- Made progress on deliverables
- Continued development work

NEXT STEPS
Will continue working on remaining tasks to complete the project."""
    
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text


def generate_weekly_report(
    contract_id: int,
    week_start: date,
) -> WeeklyReport:
    """
    Generate AI weekly report for a contract.
    
    Args:
        contract_id: Contract ID
        week_start: Start of week (Monday)
    
    Returns:
        Created WeeklyReport instance
    """
    week_end = week_start + timedelta(days=6)
    
    # Build prompt
    prompt = build_prompt(contract_id, week_start, week_end)
    
    # Call AI
    ai_summary = call_ai(prompt)
    
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
