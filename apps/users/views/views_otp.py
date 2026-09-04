from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from apps.users.serializers.serializers_otp import (
    RegisterOtpInitiateSerializer,
    RegisterOtpVerifySerializer,
    ResendOtpSerializer,
    PasswordResetOtpInitiateSerializer,
    PasswordResetOtpVerifySerializer,
)
from apps.users.services.otp_service import (
    initiate_registration_otp,
    verify_registration_otp,
    resend_registration_otp,
    initiate_password_reset_otp,
    validate_password_reset_otp,
    verify_password_reset_otp,
    resend_password_reset_otp,
)



class RegisterOtpInitiateView(APIView):
    """Initiate registration by validating input and sending a 6-digit OTP."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterOtpInitiateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        result = initiate_registration_otp(
            email=data["email"],
            password=data["password"],
            role=data.get("role", "CLIENT"),
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
        )
        return Response(result, status=status.HTTP_200_OK)


class RegisterOtpVerifyView(APIView):
    """Verify registration OTP and create user with JWT tokens."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterOtpVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user, tokens = verify_registration_otp(
            email=data["email"],
            otp=data["otp"],
        )

        return Response({
            "message": "Account created and verified successfully.",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "is_email_verified": user.is_email_verified,
            },
            "tokens": tokens,
        }, status=status.HTTP_201_CREATED)


class RegisterOtpResendView(APIView):
    """Resend registration OTP after cooldown expiration."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResendOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = resend_registration_otp(email=serializer.validated_data["email"])
        return Response(result, status=status.HTTP_200_OK)


class PasswordResetOtpInitiateView(APIView):
    """Initiate password reset by sending a 6-digit OTP."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetOtpInitiateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = initiate_password_reset_otp(email=serializer.validated_data["email"])
        return Response(result, status=status.HTTP_200_OK)


class PasswordResetOtpValidateView(APIView):
    """Validate that the password reset OTP is correct before prompting for new password."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterOtpVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        result = validate_password_reset_otp(
            email=data["email"],
            otp=data["otp"],
        )
        return Response(result, status=status.HTTP_200_OK)


class PasswordResetOtpVerifyView(APIView):
    """Verify password reset OTP and set new password."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetOtpVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        result = verify_password_reset_otp(
            email=data["email"],
            otp=data["otp"],
            new_password=data["new_password"],
        )
        return Response(result, status=status.HTTP_200_OK)


class PasswordResetOtpResendView(APIView):
    """Resend password reset OTP after cooldown expiration."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResendOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = resend_password_reset_otp(email=serializer.validated_data["email"])
        return Response(result, status=status.HTTP_200_OK)
