from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from apps.users.models import User, FreelancerProfile, ClientProfile

class FreelancerProfileSerializer(serializers.ModelSerializer):
    """Serializer for freelancer profiles."""
    
    class Meta:
        model = FreelancerProfile
        fields = [
            'bio',
            'skills',
            'hourly_rate',
            'city',
            'country',
            'address',
            'portfolio_website',
            'experience_level',
            'is_onboarded',
            'is_available',
            'total_earned',
            'average_rating',
            'total_reviews',
            'avatar',
            'banner_image',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['total_earned', 'average_rating', 'total_reviews', 'created_at', 'updated_at']


class ClientProfileSerializer(serializers.ModelSerializer):
    """Serializer for client profiles."""
    
    class Meta:
        model = ClientProfile
        fields = [
            'company_name',
            'bio',
            'city',
            'country',
            'industry',
            'company_size',
            'website',
            'is_onboarded',
            'total_spent',
            'average_rating',
            'total_reviews',
            'avatar',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['total_spent', 'average_rating', 'total_reviews', 'avatar', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user details."""
    freelancer_profile = FreelancerProfileSerializer(read_only=True)
    client_profile = ClientProfileSerializer(read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'role',
            'freelancer_profile',
            'client_profile',
            'avatar',
            'is_email_verified',
            'date_joined',
        ]
        read_only_fields = ['id', 'email', 'role', 'is_email_verified', 'date_joined']

    def get_avatar(self, obj):
        if obj.role == 'FREELANCER' and hasattr(obj, 'freelancer_profile'):
            return obj.freelancer_profile.avatar
        elif obj.role == 'CLIENT' and hasattr(obj, 'client_profile'):
            return obj.client_profile.avatar
        return ""


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'email',
            'password',
            'password_confirm',
            'role',
            'first_name',
            'last_name',
        ]
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        
        try:
            validate_password(attrs['password'])
        except DjangoValidationError as e:
            raise serializers.ValidationError(
                {"password": e.messages}
            )
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        
        return user


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""
    bio = serializers.CharField(required=False, allow_blank=True)
    skills = serializers.ListField(child=serializers.CharField(), required=False)
    hourly_rate = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False,
        allow_null=True,
        min_value=0,
        max_value=100000,
        error_messages={
            "max_value": "Hourly rate cannot exceed ₹1,00,000 / hr.",
            "min_value": "Hourly rate cannot be negative.",
        }
    )
    company_name = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(required=False, allow_blank=True)
    country = serializers.CharField(required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    portfolio_website = serializers.CharField(required=False, allow_blank=True)
    experience_level = serializers.CharField(required=False, allow_blank=True)
    is_onboarded = serializers.BooleanField(required=False)
    # Client-specific fields
    industry = serializers.CharField(required=False, allow_blank=True, max_length=500)
    company_size = serializers.CharField(required=False, allow_blank=True)
    website = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'bio',
            'skills',
            'hourly_rate',
            'company_name',
            'city',
            'country',
            'address',
            'portfolio_website',
            'experience_level',
            'is_onboarded',
            'industry',
            'company_size',
            'website',
        ]

    def validate_portfolio_website(self, value):
        if not value or not value.strip():
            return ""
        v = value.strip()
        if not (v.startswith("http://") or v.startswith("https://")):
            v = f"https://{v}"
        from django.core.validators import URLValidator
        validator = URLValidator()
        try:
            validator(v)
        except DjangoValidationError:
            raise serializers.ValidationError("Enter a valid URL (e.g. https://github.com/username or https://portfolio.com)")
        return v
    
    def update(self, instance, validated_data):
        # Extract profile fields
        profile_data = {
            'bio': validated_data.pop('bio', None),
            'skills': validated_data.pop('skills', None),
            'hourly_rate': validated_data.pop('hourly_rate', None),
            'company_name': validated_data.pop('company_name', None),
            'city': validated_data.pop('city', None),
            'country': validated_data.pop('country', None),
            'address': validated_data.pop('address', None),
            'portfolio_website': validated_data.pop('portfolio_website', None),
            'experience_level': validated_data.pop('experience_level', None),
            'is_onboarded': validated_data.pop('is_onboarded', None),
            'industry': validated_data.pop('industry', None),
            'company_size': validated_data.pop('company_size', None),
            'website': validated_data.pop('website', None),
        }
        
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update profile
        if instance.role == User.Roles.FREELANCER:
            profile, _ = FreelancerProfile.objects.get_or_create(user=instance)
            if profile_data['bio'] is not None:
                profile.bio = profile_data['bio']
            if profile_data['skills'] is not None:
                profile.skills = profile_data['skills']
            if profile_data['hourly_rate'] is not None:
                profile.hourly_rate = profile_data['hourly_rate']
            if profile_data['city'] is not None:
                profile.city = profile_data['city']
            if profile_data['country'] is not None:
                profile.country = profile_data['country']
            if profile_data['address'] is not None:
                profile.address = profile_data['address']
            if profile_data['portfolio_website'] is not None:
                profile.portfolio_website = profile_data['portfolio_website']
            if profile_data['experience_level'] is not None:
                profile.experience_level = profile_data['experience_level']
            if profile_data['is_onboarded'] is not None:
                profile.is_onboarded = profile_data['is_onboarded']
            profile.save()
            
        elif instance.role == User.Roles.CLIENT:
            profile, _ = ClientProfile.objects.get_or_create(user=instance)
            if profile_data['company_name'] is not None:
                profile.company_name = profile_data['company_name']
            if profile_data['bio'] is not None:
                profile.bio = profile_data['bio']
            if profile_data['city'] is not None:
                profile.city = profile_data['city']
            if profile_data['country'] is not None:
                profile.country = profile_data['country']
            if profile_data['industry'] is not None:
                profile.industry = profile_data['industry']
            if profile_data['company_size'] is not None:
                profile.company_size = profile_data['company_size']
            if profile_data['website'] is not None:
                profile.website = profile_data['website']
            if profile_data['is_onboarded'] is not None:
                profile.is_onboarded = profile_data['is_onboarded']
            profile.save()
        
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change."""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError(
                {"new_password_confirm": "Passwords do not match."}
            )
        
        try:
            validate_password(attrs['new_password'])
        except DjangoValidationError as e:
            raise serializers.ValidationError(
                {"new_password": e.messages}
            )
        
        return attrs



class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request."""
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation."""
    token = serializers.CharField(required=True)
    uid = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, write_only=True)
    new_password_confirm = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError(
                {"new_password_confirm": "Passwords do not match."}
            )
        
        try:
            validate_password(attrs['new_password'])
        except DjangoValidationError as e:
            raise serializers.ValidationError(
                {"new_password": e.messages}
            )
        
        return attrs


class EmailVerificationSerializer(serializers.Serializer):
    """Serializer for email verification."""
    token = serializers.CharField(required=True)
    uid = serializers.CharField(required=True)



class AvatarUploadSerializer(serializers.Serializer):
    """Serializer for avatar URL update."""
    avatar_url = serializers.URLField(required=True, max_length=500)


class BannerUploadSerializer(serializers.Serializer):
    """Serializer for banner URL update."""
    banner_url = serializers.URLField(required=True, max_length=500)


class ImageUploadSerializer(serializers.Serializer):
    """Serializer for direct image file uploads (multipart)."""
    image = serializers.ImageField(required=True)
    image_type = serializers.ChoiceField(
        choices=['avatar', 'banner'],
        required=True,
        help_text="Type of image: 'avatar' or 'banner'"
    )


class AvailabilityToggleSerializer(serializers.Serializer):
    """Serializer for freelancer availability toggle."""
    is_available = serializers.BooleanField(required=True)


class AccountDeactivationSerializer(serializers.Serializer):
    """Serializer for account deactivation."""
    password = serializers.CharField(required=True, write_only=True)
    confirmation = serializers.CharField(required=True)
    
    def validate_confirmation(self, value):
        if value != "DEACTIVATE":
            raise serializers.ValidationError(
                'Please type "DEACTIVATE" to confirm.'
            )
        return value
 
