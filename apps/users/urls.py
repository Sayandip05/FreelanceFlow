from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView,
    LoginView,
    ProfileView,
    ChangePasswordView,
    UserDetailView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    EmailVerificationView,
    ResendVerificationEmailView,
    UpdateAvatarView,
    ToggleAvailabilityView,
    DeactivateAccountView,
    ReactivateAccountView,
)


urlpatterns = [
    # Authentication
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    # Profile
    path("me/", ProfileView.as_view(), name="profile"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("avatar/", UpdateAvatarView.as_view(), name="update-avatar"),
    path("availability/", ToggleAvailabilityView.as_view(), name="toggle-availability"),
    # Password Reset
    path("password-reset/", PasswordResetRequestView.as_view(), name="password-reset"),
    path(
        "password-reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    # Email Verification
    path("verify-email/", EmailVerificationView.as_view(), name="verify-email"),
    path(
        "resend-verification/",
        ResendVerificationEmailView.as_view(),
        name="resend-verification",
    ),
    # Account Management
    path("deactivate/", DeactivateAccountView.as_view(), name="deactivate-account"),
    path("reactivate/", ReactivateAccountView.as_view(), name="reactivate-account"),
    # User details
    path("<int:pk>/", UserDetailView.as_view(), name="user-detail"),
]
