from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from asgiref.sync import sync_to_async

from .models import WorkLog, WeeklyReport, DeliveryProof, Deliverable
from .serializers import (
    WorkLogSerializer,
    WorkLogCreateSerializer,
    WorkLogUpdateSerializer,
    WeeklyReportSerializer,
    DeliveryProofSerializer,
    DeliverableSerializer,
    DeliverableCreateSerializer,
    DeliverableApprovalSerializer,
    AIChatMessageSerializer,
    AIChatResponseSerializer,
    FileUploadSerializer,
)
from .services import (
    create_worklog,
    update_worklog,
    delete_worklog,
    generate_delivery_proof,
    create_deliverable_draft,
    submit_deliverable_for_review,
    approve_deliverable,
    reject_deliverable,
    update_deliverable_draft,
    process_ai_chat_message,
    generate_deliverable_from_chat,
)
from .selectors import (
    get_worklog_by_id,
    get_contract_worklogs,
    get_contract_weekly_reports,
    get_delivery_proof_by_contract,
)
from .permissions import (
    IsWorkLogFreelancer,
    IsContractParticipant,
    IsContractFreelancer,
    IsContractClient,
)
from apps.bidding.models import Contract
from core.exceptions import ValidationError


class WorkLogViewSet(viewsets.ModelViewSet):
    """
    ViewSet for WorkLog operations.
    
    Endpoints:
    - GET /api/worklogs/ - List work logs
    - POST /api/worklogs/ - Create work log (freelancer only)
    - GET /api/worklogs/{id}/ - Get work log detail
    - PATCH /api/worklogs/{id}/ - Update work log (freelancer only)
    - DELETE /api/worklogs/{id}/ - Delete work log (freelancer only)
    """
    
    def get_queryset(self):
        user = self.request.user
        contract_id = self.request.query_params.get('contract')
        
        if contract_id:
            queryset = get_contract_worklogs(contract_id)
            if user.role == 'FREELANCER':
                return queryset.filter(freelancer=user)
            return queryset.filter(contract__bid__project__client=user)
        
        if user.role == 'FREELANCER':
            return WorkLog.objects.filter(freelancer=user)
        
        return WorkLog.objects.filter(
            contract__bid__project__client=user
        )
    
    def get_serializer_class(self):
        if self.action == 'create':
            return WorkLogCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return WorkLogUpdateSerializer
        return WorkLogSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsWorkLogFreelancer()]
        return [permissions.IsAuthenticated(), IsContractParticipant()]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        contract_id = request.query_params.get('contract')
        if not contract_id:
            return Response(
                {"error": "Contract ID required.", "code": "validation_error"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            log = create_worklog(
                freelancer=request.user,
                contract_id=int(contract_id),
                log_date=serializer.validated_data['date'],
                description=serializer.validated_data['description'],
                hours_worked=serializer.validated_data['hours_worked'],
                screenshot_url=serializer.validated_data.get('screenshot_url', ''),
                reference_url=serializer.validated_data.get('reference_url', ''),
            )
            
            return Response(
                WorkLogSerializer(log).data,
                status=status.HTTP_201_CREATED,
            )
        except ValidationError as e:
            return Response(
                {"error": e.message, "code": e.code, "field": e.field},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        log = self.get_object()
        serializer = self.get_serializer(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        try:
            updated_log = update_worklog(
                log=log,
                freelancer=request.user,
                description=serializer.validated_data.get('description'),
                hours_worked=serializer.validated_data.get('hours_worked'),
                screenshot_url=serializer.validated_data.get('screenshot_url'),
                reference_url=serializer.validated_data.get('reference_url'),
            )
            
            return Response(
                WorkLogSerializer(updated_log).data,
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response(
                {"error": e.message, "code": e.code, "field": e.field},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    def destroy(self, request, *args, **kwargs):
        log = self.get_object()
        
        try:
            delete_worklog(log, request.user)
            return Response(
                {"message": "Work log deleted successfully."},
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response(
                {"error": e.message, "code": e.code, "field": e.field},
                status=status.HTTP_400_BAD_REQUEST,
            )


class WeeklyReportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for WeeklyReport operations (read-only).
    """
    serializer_class = WeeklyReportSerializer
    permission_classes = [permissions.IsAuthenticated, IsContractParticipant]
    
    def get_queryset(self):
        contract_id = self.request.query_params.get('contract')
        
        if contract_id:
            queryset = get_contract_weekly_reports(contract_id)
            if self.request.user.role == 'FREELANCER':
                return queryset.filter(contract__bid__freelancer=self.request.user)
            return queryset.filter(contract__bid__project__client=self.request.user)
        
        user = self.request.user
        
        if user.role == 'FREELANCER':
            return WeeklyReport.objects.filter(
                contract__bid__freelancer=user
            )
        
        return WeeklyReport.objects.filter(
            contract__bid__project__client=user
        )


class DeliveryProofViewSet(viewsets.ViewSet):
    """
    ViewSet for DeliveryProof operations.
    """
    permission_classes = [permissions.IsAuthenticated, IsContractParticipant]
    
    def retrieve(self, request, pk=None):
        """Get delivery proof for a contract."""
        proof = get_delivery_proof_by_contract(pk)
        
        if not proof:
            return Response(
                {"error": "Delivery proof not found.", "code": "not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        self.check_object_permissions(request, proof)
        serializer = DeliveryProofSerializer(proof)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        """Generate delivery proof for a contract."""
        try:
            contract = Contract.objects.get(id=pk)
            if request.user not in [contract.bid.freelancer, contract.bid.project.client]:
                return Response(
                    {"error": "You are not part of this contract.", "code": "permission_denied"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            proof = generate_delivery_proof(pk)
            return Response(
                DeliveryProofSerializer(proof).data,
                status=status.HTTP_201_CREATED,
            )
        except Contract.DoesNotExist:
            return Response(
                {"error": "Contract not found.", "code": "not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValidationError as e:
            return Response(
                {"error": e.message, "code": e.code, "field": e.field},
                status=status.HTTP_400_BAD_REQUEST,
            )


class DeliverableViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Deliverable operations.
    
    Endpoints:
    - GET /api/worklogs/deliverables/ - List deliverables
    - POST /api/worklogs/deliverables/ - Create deliverable draft
    - GET /api/worklogs/deliverables/{id}/ - Get deliverable detail
    - PATCH /api/worklogs/deliverables/{id}/ - Update deliverable draft
    - POST /api/worklogs/deliverables/{id}/submit/ - Submit for review
    - POST /api/worklogs/deliverables/{id}/approve/ - Approve (client only)
    - POST /api/worklogs/deliverables/{id}/reject/ - Reject (client only)
    """
    
    def get_queryset(self):
        user = self.request.user
        contract_id = self.request.query_params.get('contract')
        
        queryset = Deliverable.objects.all()
        
        if contract_id:
            queryset = queryset.filter(contract_id=contract_id)
        
        if user.role == 'FREELANCER':
            queryset = queryset.filter(freelancer=user)
        else:
            queryset = queryset.filter(contract__bid__project__client=user)
        
        return queryset.select_related('contract', 'freelancer', 'reviewed_by')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DeliverableCreateSerializer
        return DeliverableSerializer
    
    def get_permissions(self):
        if self.action in ['approve', 'reject']:
            return [permissions.IsAuthenticated(), IsContractClient()]
        elif self.action in ['submit', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsContractFreelancer()]
        return [permissions.IsAuthenticated(), IsContractParticipant()]
    
    def create(self, request, *args, **kwargs):
        """Create a deliverable from AI chat."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        contract_id = request.query_params.get('contract')
        if not contract_id:
            return Response(
                {"error": "Contract ID required.", "code": "validation_error"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            deliverable = create_deliverable_draft(
                freelancer=request.user,
                contract_id=int(contract_id),
                title=serializer.validated_data['title'],
                description=serializer.validated_data['description'],
                ai_chat_transcript=serializer.validated_data.get('ai_chat_transcript', []),
                ai_generated_report=serializer.validated_data.get('ai_generated_report', ''),
                hours_logged=serializer.validated_data.get('hours_logged', 0),
                attached_files=serializer.validated_data.get('attached_files', []),
            )
            
            return Response(
                DeliverableSerializer(deliverable).data,
                status=status.HTTP_201_CREATED,
            )
        except ValidationError as e:
            return Response(
                {"error": e.message, "code": e.code, "field": e.field},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit deliverable for client review."""
        deliverable = self.get_object()
        
        try:
            deliverable = submit_deliverable_for_review(deliverable, request.user)
            return Response(
                DeliverableSerializer(deliverable).data,
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response(
                {"error": e.message, "code": e.code, "field": e.field},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve deliverable (client only)."""
        deliverable = self.get_object()
        serializer = DeliverableApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            deliverable = approve_deliverable(
                deliverable=deliverable,
                client=request.user,
                feedback=serializer.validated_data.get('feedback', '')
            )
            return Response(
                DeliverableSerializer(deliverable).data,
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response(
                {"error": e.message, "code": e.code, "field": e.field},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject or request revision for deliverable (client only)."""
        deliverable = self.get_object()
        serializer = DeliverableApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action_type = serializer.validated_data.get('action', 'reject')
        feedback = serializer.validated_data.get('feedback', '')
        
        try:
            deliverable = reject_deliverable(
                deliverable=deliverable,
                client=request.user,
                feedback=feedback,
                request_revision=(action_type == 'request_revision')
            )
            return Response(
                DeliverableSerializer(deliverable).data,
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response(
                {"error": e.message, "code": e.code, "field": e.field},
                status=status.HTTP_400_BAD_REQUEST,
            )


class AIChatViewSet(viewsets.ViewSet):
    """
    ViewSet for AI Chat operations (Async for non-blocking AI calls).
    
    Endpoints:
    - POST /api/worklogs/ai-chat/message/ - Send message to AI (async)
    - POST /api/worklogs/ai-chat/generate-deliverable/ - Generate deliverable from chat (async)
    """
    permission_classes = [permissions.IsAuthenticated, IsContractFreelancer]
    
    @action(detail=False, methods=['post'])
    async def message(self, request):
        """Send a message to the AI assistant (async, non-blocking)."""
        serializer = AIChatMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        contract_id = request.query_params.get('contract')
        if not contract_id:
            return Response(
                {"error": "Contract ID required.", "code": "validation_error"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            # Async database query
            contract = await sync_to_async(Contract.objects.get)(id=int(contract_id))
            
            # Verify freelancer is assigned
            if contract.bid.freelancer != request.user:
                return Response(
                    {"error": "Not assigned to this contract.", "code": "permission_denied"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            
            # Async AI call (non-blocking)
            response = await sync_to_async(process_ai_chat_message)(
                contract_id=int(contract_id),
                message=serializer.validated_data['message'],
                chat_history=serializer.validated_data.get('chat_history', []),
                project_name=contract.bid.project.title,
            )
            
            return Response(response, status=status.HTTP_200_OK)
            
        except Contract.DoesNotExist:
            return Response(
                {"error": "Contract not found.", "code": "not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )
    
    @action(detail=False, methods=['post'])
    async def generate_deliverable(self, request):
        """Generate a deliverable from the complete chat conversation (async, non-blocking)."""
        contract_id = request.query_params.get('contract')
        if not contract_id:
            return Response(
                {"error": "Contract ID required.", "code": "validation_error"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        chat_transcript = request.data.get('chat_transcript', [])
        attached_files = request.data.get('attached_files', [])
        
        if not chat_transcript:
            return Response(
                {"error": "Chat transcript required.", "code": "validation_error"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            # Async database query
            contract = await sync_to_async(Contract.objects.get)(id=int(contract_id))
            
            # Verify freelancer is assigned
            if contract.bid.freelancer != request.user:
                return Response(
                    {"error": "Not assigned to this contract.", "code": "permission_denied"},
                    status=status.HTTP_403_FORBIDDEN,
                )
            
            # Async AI call (non-blocking)
            deliverable = await sync_to_async(generate_deliverable_from_chat)(
                chat_transcript=chat_transcript,
                project_name=contract.bid.project.title,
                contract_id=int(contract_id),
                freelancer=request.user,
                attached_files=attached_files,
            )
            
            return Response(
                DeliverableSerializer(deliverable).data,
                status=status.HTTP_201_CREATED,
            )
            
        except Contract.DoesNotExist:
            return Response(
                {"error": "Contract not found.", "code": "not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValidationError as e:
            return Response(
                {"error": e.message, "code": e.code, "field": e.field},
                status=status.HTTP_400_BAD_REQUEST,
            )


class FileUploadViewSet(viewsets.ViewSet):
    """
    ViewSet for file uploads (screenshots, attachments).
    
    Endpoints:
    - POST /api/worklogs/upload/ - Upload a file
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    @action(detail=False, methods=['post'])
    def upload(self, request):
        """Upload a file and return the URL."""
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        file_obj = serializer.validated_data['file']
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf']
        if file_obj.content_type not in allowed_types:
            return Response(
                {"error": "Invalid file type. Allowed: JPG, PNG, GIF, PDF", "code": "validation_error"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Validate file size (max 10MB)
        if file_obj.size > 10 * 1024 * 1024:
            return Response(
                {"error": "File too large. Max size: 10MB", "code": "validation_error"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Save file and generate URL
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        import os
        from django.utils.text import get_valid_filename
        
        # Sanitize filename to prevent path traversal
        safe_filename = get_valid_filename(os.path.basename(file_obj.name))
        file_path = f"worklogs/uploads/{request.user.id}/{safe_filename}"
        saved_path = default_storage.save(file_path, ContentFile(file_obj.read()))
        file_url = default_storage.url(saved_path)
        
        return Response({
            "url": file_url,
            "filename": file_obj.name,
            "size": file_obj.size,
        }, status=status.HTTP_201_CREATED)
