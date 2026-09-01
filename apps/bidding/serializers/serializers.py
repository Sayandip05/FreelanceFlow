from rest_framework import serializers
from apps.bidding.models import Bid, Contract
from apps.users.serializers import UserSerializer
from apps.projects.serializers import ProjectListSerializer
from core.sanitizers import sanitize_html
class BidListSerializer(serializers.ModelSerializer):
    """Serializer for bid list view."""
    freelancer = UserSerializer(read_only=True)
    project = ProjectListSerializer(read_only=True)
    contract_id = serializers.SerializerMethodField()
    
    class Meta:
        model = Bid
        fields = [
            'id',
            'project',
            'freelancer',
            'amount',
            'cover_letter',
            'status',
            'contract_id',
            'created_at',
            'updated_at',
        ]

    def get_contract_id(self, obj):
        return obj.contract.id if hasattr(obj, 'contract') else None


class BidDetailSerializer(serializers.ModelSerializer):
    """Serializer for bid detail view."""
    freelancer = UserSerializer(read_only=True)
    project = ProjectListSerializer(read_only=True)
    contract_id = serializers.SerializerMethodField()
    
    class Meta:
        model = Bid
        fields = [
            'id',
            'project',
            'freelancer',
            'amount',
            'cover_letter',
            'status',
            'contract_id',
            'created_at',
            'updated_at',
        ]

    def get_contract_id(self, obj):
        return obj.contract.id if hasattr(obj, 'contract') else None


class BidCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating bids."""
    
    class Meta:
        model = Bid
        fields = ['project', 'amount', 'cover_letter']
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Bid amount must be greater than 0.")
        return value
    
    def validate_cover_letter(self, value):
        if len(value.strip()) < 20:
            raise serializers.ValidationError(
                "Please provide a short pitch (at least 20 characters) on why you're interested in this project."
            )
        # Sanitize cover letter to prevent XSS
        return sanitize_html(value, allow_basic_formatting=True)


class ContractSerializer(serializers.ModelSerializer):
    """Serializer for contracts. All financial and status fields are read-only."""
    project = ProjectListSerializer(read_only=True)
    freelancer = UserSerializer(read_only=True)
    client = UserSerializer(read_only=True)
    bid = BidDetailSerializer(read_only=True)
    milestones = serializers.SerializerMethodField()

    class Meta:
        model = Contract
        fields = [
            'id',
            'bid',
            'project',
            'freelancer',
            'client',
            'agreed_amount',
            'start_date',
            'end_date',
            'is_active',
            'status',
            'milestones',
        ]
        # All fields are read-only: contracts are mutated only via service
        # layer actions (accept_bid, accept_proposal, etc.), never via direct API write.
        read_only_fields = [
            'id', 'bid', 'agreed_amount', 'start_date', 'end_date', 'is_active', 'status',
        ]

    def get_milestones(self, obj):
        from apps.payments.serializers import PaymentMilestoneSerializer
        return PaymentMilestoneSerializer(obj.milestones.all(), many=True).data


class ContractListSerializer(serializers.ModelSerializer):
    """Serializer for contract list view. All financial and status fields are read-only."""
    project = ProjectListSerializer(read_only=True)
    freelancer = UserSerializer(read_only=True)
    client = UserSerializer(read_only=True)
    project_title = serializers.CharField(source='bid.project.title', read_only=True)
    freelancer_name = serializers.CharField(source='bid.freelancer.full_name', read_only=True)
    client_name = serializers.CharField(source='bid.project.client.full_name', read_only=True)

    class Meta:
        model = Contract
        fields = [
            'id',
            'project',
            'freelancer',
            'client',
            'project_title',
            'freelancer_name',
            'client_name',
            'agreed_amount',
            'start_date',
            'is_active',
            'status',
        ]
        read_only_fields = [
            'id', 'agreed_amount', 'start_date', 'is_active', 'status',
        ]
