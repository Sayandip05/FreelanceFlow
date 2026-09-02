"""
Serializers for AI Worklog & Weekly Report System.
"""
from rest_framework import serializers
from apps.worklogs.models import AIConversation, AIReportDraft, QdrantCollection, Deliverable


class AIDraftSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIReportDraft
        fields = [
            "id",
            "title",
            "section_summary",
            "section_deliverables",
            "section_next_steps",
            "hours_worked",
            "status",
            "pdf_url",
            "approved_at",
            "created_at",
        ]


class AIConversationSerializer(serializers.ModelSerializer):
    drafts = AIDraftSerializer(many=True, read_only=True)

    class Meta:
        model = AIConversation
        fields = [
            "id",
            "contract",
            "freelancer",
            "week_start",
            "week_end",
            "messages",
            "is_active",
            "drafts",
            "created_at",
            "updated_at",
        ]


class AIChatRequestSerializer(serializers.Serializer):
    contract = serializers.IntegerField(required=True)
    message = serializers.CharField(required=True, allow_blank=False)
    conversation_id = serializers.IntegerField(required=False, allow_null=True)


class AIApproveRequestSerializer(serializers.Serializer):
    contract = serializers.IntegerField(required=True)
    draft_id = serializers.IntegerField(required=False, allow_null=True)


class AIContextDeliverableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deliverable
        fields = [
            "id",
            "title",
            "description",
            "status",
            "hours_logged",
            "submitted_at",
            "reviewed_at",
            "created_at",
        ]


class AIContextBundleSerializer(serializers.Serializer):
    contract = serializers.DictField()
    deliverables = AIContextDeliverableSerializer(many=True)
    milestones = serializers.ListField(child=serializers.DictField(), required=False, default=list)
    stats = serializers.DictField()
    previous_reports = serializers.ListField()
    active_draft = AIDraftSerializer(allow_null=True)
    qdrant_status = serializers.DictField()
    conversation = AIConversationSerializer(allow_null=True)
