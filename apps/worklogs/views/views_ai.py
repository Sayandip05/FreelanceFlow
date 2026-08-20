"""
API Views for AI Worklog & Weekly Report System.
Supports async agent execution, context bundle assembly, and draft approval.
"""
from rest_framework import views, permissions, status
from rest_framework.response import Response
from asgiref.sync import async_to_sync
from apps.bidding.models import Contract
from apps.worklogs.serializers.serializers_ai import (
    AIContextBundleSerializer,
    AIChatRequestSerializer,
    AIApproveRequestSerializer,
    AIConversationSerializer,
    AIDraftSerializer,
)
from apps.worklogs.selectors_ai import get_ai_context_bundle, get_contract_ai_history
from apps.worklogs.services.ai_service import run_ai_worklog_agent


class AIContextView(views.APIView):
    """
    GET /api/worklogs/ai/context/?contract={id}
    Returns complete context bundle for the split-screen AI workspace:
    Contract details, deliverables, stats, past PDF reports, active draft, Qdrant status.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        contract_id = request.query_params.get("contract") or request.query_params.get("contract_id")
        if not contract_id:
            return Response(
                {"error": "contract query parameter is required", "code": "validation_error"},
                status=status.HTTP_400_BAD_REQUEST,
            )


        try:
            contract_id = int(contract_id)
        except ValueError:
            return Response(
                {"error": "Invalid contract ID", "code": "validation_error"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        bundle = get_ai_context_bundle(contract_id, request.user.id)
        if not bundle:
            return Response(
                {"error": "Contract not found or access denied", "code": "not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = AIContextBundleSerializer(bundle)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AIChatView(views.APIView):
    """
    POST /api/worklogs/ai/chat/
    Invokes the 3-node LangGraph agent:
    Runs context_assembler (PG + Qdrant) -> report_generator (Groq LLaMA 3.3 70B).
    Returns conversational reply and structured draft if drafted.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = AIChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        contract_id = serializer.validated_data["contract"]
        message = serializer.validated_data["message"]
        conversation_id = serializer.validated_data.get("conversation_id")

        # Verify contract access
        try:
            contract = Contract.objects.select_related("bid__freelancer").get(id=contract_id)
        except Contract.DoesNotExist:
            return Response(
                {"error": "Contract not found", "code": "not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if contract.bid.freelancer_id != request.user.id:
            return Response(
                {"error": "Only the assigned freelancer may use the AI Worklog Assistant", "code": "forbidden"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Run async agent
        agent_result = async_to_sync(run_ai_worklog_agent)(
            contract_id=contract_id,
            freelancer_id=request.user.id,
            user_message=message,
            action="chat",
            conversation_id=conversation_id,
        )

        if agent_result.get("error"):
            return Response(
                {"error": agent_result["error"], "code": "agent_error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({
            "reply": agent_result.get("reply"),
            "conversation_id": agent_result.get("conversation_id"),
            "is_draft_ready": agent_result.get("is_draft_ready", False),
            "draft": agent_result.get("draft"),
            "draft_id": agent_result.get("draft_id"),
        }, status=status.HTTP_200_OK)


class AIApproveDraftView(views.APIView):
    """
    POST /api/worklogs/ai/approve/
    Triggers the pdf_builder node:
    Compiles WeasyPrint HTML->PDF, uploads to Azure Blob Storage, returns SAS URL.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = AIApproveRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        contract_id = serializer.validated_data["contract"]
        draft_id = serializer.validated_data.get("draft_id")

        try:
            contract = Contract.objects.select_related("bid__freelancer").get(id=contract_id)
        except Contract.DoesNotExist:
            return Response(
                {"error": "Contract not found", "code": "not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if contract.bid.freelancer_id != request.user.id:
            return Response(
                {"error": "Permission denied", "code": "forbidden"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Run async agent with action="approve"
        agent_result = async_to_sync(run_ai_worklog_agent)(
            contract_id=contract_id,
            freelancer_id=request.user.id,
            user_message="Approve and generate official PDF report",
            action="approve",
            draft_id=draft_id,
        )

        if agent_result.get("error"):
            return Response(
                {"error": agent_result["error"], "code": "compilation_error"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({
            "success": True,
            "message": "Report approved and compiled successfully",
            "pdf_url": agent_result.get("pdf_url"),
            "draft_id": agent_result.get("draft_id"),
            "reply": agent_result.get("reply"),
        }, status=status.HTTP_200_OK)


class AIHistoryView(views.APIView):
    """
    GET /api/worklogs/ai/history/?contract={id}
    Returns conversation transcripts and past report drafts for a contract.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        contract_id = request.query_params.get("contract")
        if not contract_id:
            return Response(
                {"error": "contract query parameter is required", "code": "validation_error"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            contract_id = int(contract_id)
        except ValueError:
            return Response(
                {"error": "Invalid contract ID", "code": "validation_error"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        history = get_contract_ai_history(contract_id, request.user.id)
        return Response({
            "conversations": AIConversationSerializer(history["conversations"], many=True).data,
            "drafts": AIDraftSerializer(history["drafts"], many=True).data,
        }, status=status.HTTP_200_OK)
