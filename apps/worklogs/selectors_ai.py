"""
Selectors for AI Worklog System.
Strict ORM rule: select_related/prefetch_related on every queryset touching related models.
"""
from typing import Dict, Any, Optional
from django.db.models import Sum, Count, Q
from apps.bidding.models import Contract
from apps.worklogs.models import (
    WorkLog,
    Deliverable,
    WeeklyReport,
    AIConversation,
    AIReportDraft,
    QdrantCollection,
)


def get_ai_context_bundle(contract_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """
    Assembles complete context bundle for the split-screen AI workspace.
    Runs optimized query batch with select_related and prefetch_related.
    """
    try:
        contract = Contract.objects.select_related(
            "bid__project__client",
            "bid__freelancer"
        ).prefetch_related(
            "deliverables",
            "qdrant_collection"
        ).get(id=contract_id)
    except Contract.DoesNotExist:
        return None

    # Check permission: User must be freelancer or client of this contract
    is_freelancer = contract.bid.freelancer_id == user_id
    is_client = contract.bid.project.client_id == user_id
    if not (is_freelancer or is_client):
        return None

    project = contract.bid.project
    client = project.client
    freelancer = contract.bid.freelancer

    # 1. Deliverables list
    deliverables = list(contract.deliverables.all().order_by("-created_at"))

    # 2. Stats calculation
    total_hours = WorkLog.objects.filter(
        contract=contract
    ).aggregate(total=Sum("hours_worked"))["total"] or 0

    approved_deliv_count = sum(1 for d in deliverables if d.status == Deliverable.Status.APPROVED)
    total_deliv_count = len(deliverables)

    stats = {
        "total_hours_logged": float(total_hours),
        "total_deliverables": total_deliv_count,
        "approved_deliverables": approved_deliv_count,
        "completion_rate": int((approved_deliv_count / total_deliv_count * 100)) if total_deliv_count > 0 else 0,
    }

    # 3. Previous approved reports (both AIReportDraft & WeeklyReport)
    past_drafts = list(AIReportDraft.objects.filter(
        contract=contract,
        status=AIReportDraft.Status.APPROVED
    ).order_by("-created_at")[:10])

    past_weekly = list(WeeklyReport.objects.filter(
        contract=contract
    ).order_by("-week_start")[:10])

    previous_reports = []
    seen_urls = set()

    for d in past_drafts:
        if d.pdf_url and d.pdf_url not in seen_urls:
            seen_urls.add(d.pdf_url)
            previous_reports.append({
                "id": d.id,
                "title": d.title,
                "created_at": d.created_at.isoformat(),
                "pdf_url": d.pdf_url,
                "hours_worked": float(d.hours_worked),
                "type": "AI Progress Report"
            })

    for w in past_weekly:
        if w.pdf_url and w.pdf_url not in seen_urls:
            seen_urls.add(w.pdf_url)
            previous_reports.append({
                "id": w.id,
                "title": f"Weekly Report ({w.week_start} to {w.week_end})",
                "created_at": w.created_at.isoformat(),
                "pdf_url": w.pdf_url,
                "hours_worked": float(w.total_hours),
                "type": "Weekly Report"
            })

    # 4. Active Draft (pending approval)
    active_draft = AIReportDraft.objects.filter(
        contract=contract,
        status=AIReportDraft.Status.DRAFT
    ).order_by("-created_at").first()

    # 5. Qdrant status
    qdrant_obj = getattr(contract, "qdrant_collection", None)
    qdrant_status = {
        "is_initialized": bool(qdrant_obj and qdrant_obj.is_initialized),
        "collection_name": qdrant_obj.collection_name if qdrant_obj else f"contract_{contract.id}_fl_{freelancer.id}",
        "vectors_count": qdrant_obj.vectors_count if qdrant_obj else 0,
    }

    # 6. Latest conversation
    conversation = AIConversation.objects.filter(
        contract=contract,
        freelancer=freelancer,
        is_active=True
    ).order_by("-updated_at").first()

    return {
        "contract": {
            "id": contract.id,
            "title": project.title,
            "description": project.description,
            "client_name": client.get_full_name() or client.username,
            "client_avatar": getattr(client, "avatar_url", "") or "",
            "freelancer_name": freelancer.get_full_name() or freelancer.username,
            "rate": str(getattr(contract, "agreed_amount", 0)),
            "status": getattr(contract, "status", "ACTIVE"),
            "created_at": contract.created_at.isoformat() if hasattr(contract, "created_at") and contract.created_at else None,
        },
        "deliverables": deliverables,
        "stats": stats,
        "previous_reports": previous_reports,
        "active_draft": active_draft,
        "qdrant_status": qdrant_status,
        "conversation": conversation,
    }


def get_contract_ai_history(contract_id: int, user_id: int) -> Dict[str, Any]:
    """Retrieves conversation history and drafts for a contract."""
    conversations = list(AIConversation.objects.filter(
        contract_id=contract_id,
        freelancer_id=user_id
    ).prefetch_related("drafts").order_by("-created_at"))

    drafts = list(AIReportDraft.objects.filter(
        contract_id=contract_id,
        freelancer_id=user_id
    ).order_by("-created_at"))

    return {
        "conversations": conversations,
        "drafts": drafts,
    }
