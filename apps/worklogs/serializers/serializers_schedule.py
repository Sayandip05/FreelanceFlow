"""
Serializers for the ReportSchedule API.

Clients use these endpoints to configure how often they want a
progress report for each of their contracts.
"""
from datetime import date, timedelta
from rest_framework import serializers
from apps.worklogs.models import ReportSchedule
from apps.bidding.models import Contract


class ReportScheduleSerializer(serializers.ModelSerializer):
    """
    Read serializer — returned to both client and freelancer on GET.
    """
    project_title = serializers.SerializerMethodField()
    interval_label = serializers.SerializerMethodField()
    days_until_next_report = serializers.SerializerMethodField()

    class Meta:
        model = ReportSchedule
        fields = [
            "id",
            "contract",
            "project_title",
            "interval_days",
            "interval_label",
            "next_report_date",
            "days_until_next_report",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_project_title(self, obj) -> str:
        return obj.contract.bid.project.title

    def get_interval_label(self, obj) -> str:
        return ReportSchedule.Interval(obj.interval_days).label

    def get_days_until_next_report(self, obj) -> int:
        return obj.days_until_next_report


class ReportScheduleCreateSerializer(serializers.Serializer):
    """
    Write serializer — used when client creates or updates a schedule.

    Validates:
    - Only the contract's client can configure the schedule
    - interval_days must be 7, 14, or 30
    - Contract must be active
    """
    contract = serializers.PrimaryKeyRelatedField(
        queryset=Contract.objects.filter(is_active=True)
    )
    interval_days = serializers.ChoiceField(
        choices=ReportSchedule.Interval.choices,
        help_text="Report interval: 7 (weekly), 14 (biweekly), or 30 (monthly)",
    )
    is_active = serializers.BooleanField(default=True, required=False)

    def validate_contract(self, contract: Contract) -> Contract:
        """Ensure only the contract's client can manage the schedule."""
        request = self.context.get("request")
        if request and contract.bid.project.client != request.user:
            raise serializers.ValidationError(
                "Only the client of this contract can configure its report schedule."
            )
        return contract

    def create(self, validated_data: dict) -> ReportSchedule:
        """Create or update the schedule for this contract (upsert)."""
        contract = validated_data["contract"]
        interval_days = validated_data["interval_days"]
        is_active = validated_data.get("is_active", True)
        request = self.context.get("request")

        schedule, created = ReportSchedule.objects.update_or_create(
            contract=contract,
            defaults={
                "interval_days": interval_days,
                "next_report_date": date.today() + timedelta(days=interval_days),
                "is_active": is_active,
                "created_by": request.user if request else None,
            },
        )
        return schedule

    def update(self, instance: ReportSchedule, validated_data: dict) -> ReportSchedule:
        """Partial update — change interval or pause/resume."""
        if "interval_days" in validated_data:
            instance.interval_days = validated_data["interval_days"]
            # Recalculate next_report_date when interval changes
            instance.next_report_date = date.today() + timedelta(
                days=validated_data["interval_days"]
            )
        if "is_active" in validated_data:
            instance.is_active = validated_data["is_active"]
        instance.save()
        return instance
