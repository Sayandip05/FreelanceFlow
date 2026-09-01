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
    UpdateBannerView,
    UploadImageView,
    ToggleAvailabilityView,
    DeactivateAccountView,
    ReactivateAccountView,
    FreelancerPayoutAccountView,
)
from .views_extended import (
    ActivityLogViewSet,
    OnlineStatusViewSet,
)
from .views_google_oauth import GoogleOAuthInitView, GoogleOAuthCallbackView
from .presence import UserPresenceView