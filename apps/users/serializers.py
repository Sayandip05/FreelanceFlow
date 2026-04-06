from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import User, FreelancerProfile, ClientProfile


class FreelancerProfileSerializer(serializers.ModelSerializer):
    """Serializer for freelancer profiles."""
    
    class Meta:
        model = FreelancerProfile
        fields = [
            'bio',
            'skills',
            'hourly_rate',
            'subscription_tier',
            'total_earned',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['total_earned', 'created_at', 'updated_at']


class ClientProfileSerializer(serializers.ModelSerializer):
    """Serializer for client profiles."""
    
    class Meta:
        model = ClientProfile
        fields = [
            'company_name',
            'total_spent',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['total_spent', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user details."""
    freelancer_profile = FreelancerProfileSerializer(read_only=True)
    client_profile = ClientProfileSerializer(read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
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
            'date_joined',
        ]
        read_only_fields = ['id', 'email', 'role', 'date_joined']


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
        allow_null=True
    )
    company_name = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'bio',
            'skills',
            'hourly_rate',
            'company_name',
        ]
    
    def update(self, instance, validated_data):
        # Extract profile fields
        profile_data = {
            'bio': validated_data.pop('bio', None),
            'skills': validated_data.pop('skills', None),
            'hourly_rate': validated_data.pop('hourly_rate', None),
            'company_name': validated_data.pop('company_name', None),
        }
        
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update profile
        if instance.role == User.Roles.FREELANCER:
            profile = instance.freelancer_profile
            if profile_data['bio'] is not None:
                profile.bio = profile_data['bio']
            if profile_data['skills'] is not None:
                profile.skills = profile_data['skills']
            if profile_data['hourly_rate'] is not None:
                profile.hourly_rate = profile_data['hourly_rate']
            profile.save()
            
        elif instance.role == User.Roles.CLIENT:
            profile = instance.client_profile
            if profile_data['company_name'] is not None:
                profile.company_name = profile_data['company_name']
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
