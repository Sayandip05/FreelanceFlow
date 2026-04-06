from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User
from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    UserProfileUpdateSerializer,
    ChangePasswordSerializer,
)
from .services import create_user, update_profile, change_password
from .selectors import get_user_by_id
from core.exceptions import ValidationError


class RegisterView(generics.CreateAPIView):
    """
    POST /api/users/register/
    Register a new user (client or freelancer).
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
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
    pass


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
