from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.throttling import AnonRateThrottle

from .models import User
from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    UserProfileUpdateSerializer,
    ChangePasswordSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    EmailVerificationSerializer,
    AvatarUploadSerializer,
    AvailabilityToggleSerializer,
    AccountDeactivationSerializer,
)
from .services import create_user, update_profile, change_password
from .selectors import get_user_by_id
from core.exceptions import ValidationError


class AuthRateThrottle(AnonRateThrottle):
    """Custom rate throttle for authentication endpoints."""
    rate = '5/minute'


class RegisterView(generics.CreateAPIView):
    """
    POST /api/users/register/
    Register a new user (client or freelancer).
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthRateThrottle]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            user = create_user(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password'],
                role=serializer.validated_data['role'],
                first_name=serializer.validated_data.get('first_name', ''),
                last_name=serializer.validated_data.get('last_name', ''),
            )
            
            return Response(
                {
                    "message": "User registered successfully.",
                    "user": UserSerializer(user).data,
                },
                status=status.HTTP_201_CREATED,
            )
        except ValidationError as e:
            return Response(
                {"error": e.message, "code": e.code, "field": e.field},
                status=status.HTTP_400_BAD_REQUEST,
            )


class LoginView(TokenObtainPairView):
    """
    POST /api/users/login/
    Login with email and password to get JWT tokens.
    """
    throttle_classes = [AuthRateThrottle]


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    GET /api/users/me/
    PATCH /api/users/me/
    Get or update current user's profile.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def patch(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = UserProfileUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        updated_user = update_profile(user, serializer.validated_data)
        
        return Response(
            UserSerializer(updated_user).data,
            status=status.HTTP_200_OK,
        )


class ChangePasswordView(generics.GenericAPIView):
    """
    POST /api/users/change-password/
    Change user's password.
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AuthRateThrottle]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            change_password(
                user=request.user,
                old_password=serializer.validated_data['old_password'],
                new_password=serializer.validated_data['new_password'],
            )
            
            return Response(
                {"message": "Password changed successfully."},
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response(
                {"error": e.message, "code": e.code, "field": e.field},
                status=status.HTTP_400_BAD_REQUEST,
            )


class UserDetailView(generics.RetrieveAPIView):
    """
    GET /api/users/<id>/
    Get public profile of a specific user.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'pk'



class PasswordResetRequestView(generics.GenericAPIView):
    """
    POST /api/users/password-reset/
    Request password reset email.
    """
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthRateThrottle]
    
    def post(self, request, *args, **kwargs):
        from .services import send_password_reset_email
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        send_password_reset_email(serializer.validated_data['email'])
        
        return Response(
            {"message": "If the email exists, a password reset link has been sent."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(generics.GenericAPIView):
    """
    POST /api/users/password-reset/confirm/
    Confirm password reset with token.
    """
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthRateThrottle]
    
    def post(self, request, *args, **kwargs):
        from .services import reset_password
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            reset_password(
                uid=serializer.validated_data['uid'],
                token=serializer.validated_data['token'],
                new_password=serializer.validated_data['new_password'],
            )
            
            return Response(
                {"message": "Password reset successfully."},
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response(
                {"error": e.message, "code": e.code, "field": e.field},
                status=status.HTTP_400_BAD_REQUEST,
            )


class EmailVerificationView(generics.GenericAPIView):
    """
    POST /api/users/verify-email/
    Verify email with token.
    """
    serializer_class = EmailVerificationSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        from .services import verify_email
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            user = verify_email(
                uid=serializer.validated_data['uid'],
                token=serializer.validated_data['token'],
            )
            
            return Response(
                {
                    "message": "Email verified successfully.",
                    "user": UserSerializer(user).data,
                },
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response(
                {"error": e.message, "code": e.code, "field": e.field},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ResendVerificationEmailView(generics.GenericAPIView):
    """
    POST /api/users/resend-verification/
    Resend email verification link.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AuthRateThrottle]
    
    def post(self, request, *args, **kwargs):
        from .services import send_verification_email
        
        user = request.user
        
        if user.is_active:
            return Response(
                {"error": "Email already verified.", "code": "already_verified"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        send_verification_email(user)
        
        return Response(
            {"message": "Verification email sent."},
            status=status.HTTP_200_OK,
        )



class UpdateAvatarView(generics.GenericAPIView):
    """
    POST /api/users/avatar/
    Update user's profile photo.
    """
    serializer_class = AvatarUploadSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        from .services import update_avatar
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = update_avatar(
            user=request.user,
            avatar_url=serializer.validated_data['avatar_url']
        )
        
        return Response(
            {
                "message": "Avatar updated successfully.",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class ToggleAvailabilityView(generics.GenericAPIView):
    """
    POST /api/users/availability/
    Toggle freelancer availability.
    """
    serializer_class = AvailabilityToggleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        from .services import toggle_freelancer_availability
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            profile = toggle_freelancer_availability(
                user=request.user,
                is_available=serializer.validated_data['is_available']
            )
            
            return Response(
                {
                    "message": "Availability updated successfully.",
                    "is_available": profile.is_available,
                },
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response(
                {"error": e.message, "code": e.code, "field": e.field},
                status=status.HTTP_400_BAD_REQUEST,
            )


class DeactivateAccountView(generics.GenericAPIView):
    """
    POST /api/users/deactivate/
    Deactivate user account (soft delete).
    """
    serializer_class = AccountDeactivationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        from .services import deactivate_account
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            deactivate_account(
                user=request.user,
                password=serializer.validated_data['password']
            )
            
            return Response(
                {"message": "Account deactivated successfully."},
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response(
                {"error": e.message, "code": e.code, "field": e.field},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ReactivateAccountView(generics.GenericAPIView):
    """
    POST /api/users/reactivate/
    Reactivate a deactivated account.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        from .services import reactivate_account
        from django.contrib.auth import get_user_model
        
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {"error": "Email and password required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        User = get_user_model()
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid credentials."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        if not user.check_password(password):
            return Response(
                {"error": "Invalid credentials."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            reactivate_account(user)
            
            return Response(
                {"message": "Account reactivated successfully."},
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response(
                {"error": e.message, "code": e.code},
                status=status.HTTP_400_BAD_REQUEST,
            )
