from rest_framework import serializers

from .models import WorkLog, WeeklyReport, DeliveryProof, Deliverable
from apps.users.serializers import UserSerializer
from apps.bidding.serializers import ContractSerializer


class WorkLogSerializer(serializers.ModelSerializer):
    """Serializer for work logs."""
    freelancer = UserSerializer(read_only=True)
    contract = ContractSerializer(read_only=True)
    is_approved = serializers.BooleanField(read_only=True)
    is_pending = serializers.BooleanField(read_only=True)
    screenshot = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = WorkLog
        fields = [
            'id',
            'contract',
            'freelancer',
            'date',
            'description',
            'hours_worked',
            'screenshot',
            'screenshot_url',
            'reference_url',
            'status',
            'is_approved',
            'is_pending',
            'ai_generated_summary',
            'client_notes',
            'approved_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['approved_at', 'approved_by']


class WorkLogCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating work logs."""
    
    class Meta:
        model = WorkLog
        fields = [
            'date',
            'description',
            'hours_worked',
            'screenshot_url',
            'reference_url',
        ]
    
    def validate_hours_worked(self, value):
        if value <= 0 or value > 24:
            raise serializers.ValidationError("Hours must be between 0 and 24.")
        return value
    
    def validate_description(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Description must be at least 10 characters."
            )
        return value


class WorkLogUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating work logs."""
    
    class Meta:
        model = WorkLog
        fields = [
            'description',
            'hours_worked',
            'screenshot_url',
            'reference_url',
        ]
    
    def validate_hours_worked(self, value):
        if value is not None and (value <= 0 or value > 24):
            raise serializers.ValidationError("Hours must be between 0 and 24.")
        return value


class WeeklyReportSerializer(serializers.ModelSerializer):
    """Serializer for weekly reports."""
    contract = ContractSerializer(read_only=True)
    total_hours = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = WeeklyReport
        fields = [
            'id',
            'contract',
            'week_start',
            'week_end',
            'ai_summary',
            'pdf_url',
            'total_hours',
            'sent_to_client_at',
            'created_at',
        ]


class DeliveryProofSerializer(serializers.ModelSerializer):
    """Serializer for delivery proofs."""
    contract = ContractSerializer(read_only=True)
    
    class Meta:
        model = DeliveryProof
        fields = [
            'id',
            'contract',
            'pdf_url',
            'generated_at',
            'total_hours',
            'total_logs_count',
            'total_deliverables',
            'approved_deliverables',
            'report_id',
        ]


class DeliverableSerializer(serializers.ModelSerializer):
    """Serializer for deliverables."""
    freelancer = UserSerializer(read_only=True)
    contract = ContractSerializer(read_only=True)
    reviewed_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Deliverable
        fields = [
            'id',
            'contract',
            'freelancer',
            'title',
            'description',
            'ai_generated_report',
            'attached_files',
            'status',
            'hours_logged',
            'submitted_at',
            'reviewed_at',
            'reviewed_by',
            'client_feedback',
            'payment_released',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['submitted_at', 'reviewed_at', 'reviewed_by']


class DeliverableCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating deliverables."""
    ai_chat_transcript = serializers.ListField(
        child=serializers.DictField(),
        required=True,
        help_text="Full chat conversation with AI"
    )
    attached_files = serializers.ListField(
        child=serializers.URLField(),
        required=False,
        default=list
    )
    
    class Meta:
        model = Deliverable
        fields = [
            'title',
            'description',
            'ai_chat_transcript',
            'ai_generated_report',
            'hours_logged',
            'attached_files',
        ]


class DeliverableApprovalSerializer(serializers.Serializer):
    """Serializer for approving/rejecting deliverables."""
    action = serializers.ChoiceField(
        choices=['approve', 'reject', 'request_revision'],
        required=True
    )
    feedback = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Client feedback (required for reject/revision)"
    )


class AIChatMessageSerializer(serializers.Serializer):
    """Serializer for AI chat messages."""
    message = serializers.CharField(required=True)
    chat_history = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list,
        help_text="Previous chat messages"
    )


class AIChatResponseSerializer(serializers.Serializer):
    """Serializer for AI chat responses."""
    message = serializers.CharField()
    report_ready = serializers.BooleanField()
    report_data = serializers.DictField(required=False, allow_null=True)


class FileUploadSerializer(serializers.Serializer):
    """Serializer for file uploads."""
    file = serializers.FileField(required=True)
    description = serializers.CharField(required=False, allow_blank=True)
