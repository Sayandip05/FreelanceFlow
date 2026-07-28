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
from .views_extended import (
    ActivityLogViewSet,
    OnlineStatusViewSet,
)
from .views_google_oauth import GoogleOAuthInitView, GoogleOAuthCallbackView
