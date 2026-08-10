from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.throttling import AnonRateThrottle
from apps.users.models import User
from apps.users.serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    UserProfileUpdateSerializer,
    ChangePasswordSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    EmailVerificationSerializer,
    AvatarUploadSerializer,
    BannerUploadSerializer,
    ImageUploadSerializer,
    AvailabilityToggleSerializer,
    AccountDeactivationSerializer,
)
from apps.users.services import create_user, update_profile, change_password
from apps.users.selectors import get_user_by_id
from core.exceptions import ValidationError
class AuthRateThrottle(AnonRateThrottle):
    """Custom rate throttle for authentication endpoints."""
    scope = 'auth'
    rate = '5/minute'

    def get_rate(self):
        from django.conf import settings
        rates = getattr(settings, 'REST_FRAMEWORK', {}).get('DEFAULT_THROTTLE_RATES', {})
        return rates.get('auth', self.rate)


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
    queryset = User.objects.select_related('freelancer_profile', 'client_profile').all()
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
        from apps.users.services import send_password_reset_email
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
        from apps.users.services import reset_password
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
        from apps.users.services import verify_email
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
        from apps.users.services import send_verification_email
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
        from apps.users.services import update_avatar
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


class UploadImageView(generics.GenericAPIView):
    """
    POST /api/users/upload-image/
    Upload avatar or banner image directly to Azure Blob Storage.
    Accepts multipart/form-data with fields:
      - image: file
      - image_type: 'avatar' | 'banner'
    Returns the public URL and updated user object.
    """
    serializer_class = ImageUploadSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = []

    def get_parsers(self):
        from rest_framework.parsers import MultiPartParser, FormParser
        return [MultiPartParser(), FormParser()]

    def post(self, request, *args, **kwargs):
        import uuid
        import os
        from pathlib import Path
        from django.conf import settings
        from apps.users.services import update_avatar

        serializer = ImageUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        image_file = serializer.validated_data['image']
        image_type = serializer.validated_data['image_type']  # 'avatar' or 'banner'
        user = request.user

        # Generate unique file name
        ext = os.path.splitext(image_file.name)[1].lower() or '.jpg'
        unique_name = f"{uuid.uuid4().hex}{ext}"
        relative_path = f"{image_type}s/{user.id}/{unique_name}"

        # ── Try Azure Blob Storage first ──────────────────────────────────
        connection_string = getattr(settings, 'AZURE_STORAGE_CONNECTION_STRING', '')
        container_name = getattr(settings, 'AZURE_CONTAINER_NAME', 'media')

        if connection_string:
            try:
                from azure.storage.blob import BlobServiceClient, ContentSettings
                blob_service = BlobServiceClient.from_connection_string(connection_string)
                container_client = blob_service.get_container_client(container_name)
                content_settings = ContentSettings(content_type=image_file.content_type)
                container_client.upload_blob(
                    name=relative_path,
                    data=image_file.read(),
                    overwrite=True,
                    content_settings=content_settings,
                )
                account_name = blob_service.account_name
                image_url = f"https://{account_name}.blob.core.windows.net/{container_name}/{relative_path}"
            except Exception as exc:
                return Response(
                    {"detail": f"Azure upload failed: {str(exc)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        else:
            # ── Local fallback: save to MEDIA_ROOT ───────────────────────
            try:
                media_root = Path(settings.MEDIA_ROOT)
                save_dir = media_root / f"{image_type}s" / str(user.id)
                save_dir.mkdir(parents=True, exist_ok=True)
                save_path = save_dir / unique_name

                with open(save_path, 'wb') as dest:
                    for chunk in image_file.chunks():
                        dest.write(chunk)

                # Build a URL the frontend can reach:  http://localhost:8000/media/avatars/1/abc.jpg
                backend_url = getattr(settings, 'BACKEND_URL', 'http://localhost:8000').rstrip('/')
                media_url = settings.MEDIA_URL.rstrip('/')
                image_url = f"{backend_url}{media_url}/{image_type}s/{user.id}/{unique_name}"
            except Exception as exc:
                return Response(
                    {"detail": f"Local file save failed: {str(exc)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        # Persist URL to profile
        if image_type == 'avatar':
            update_avatar(user=user, avatar_url=image_url)
        else:
            # banner — freelancer only for now
            if user.role == User.Roles.FREELANCER:
                profile = user.freelancer_profile
                profile.banner_image = image_url
                profile.save(update_fields=['banner_image'])

        user.refresh_from_db()
        return Response(
            {
                "message": f"{image_type.capitalize()} uploaded successfully.",
                "url": image_url,
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
        from apps.users.services import toggle_freelancer_availability
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
        from apps.users.services import deactivate_account
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
        from apps.users.services import reactivate_account
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
 
 
