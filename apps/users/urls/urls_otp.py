from django.urls import path
from apps.users.views.views_otp import (
    RegisterOtpInitiateView,
    RegisterOtpVerifyView,
    RegisterOtpResendView,
    PasswordResetOtpInitiateView,
    PasswordResetOtpVerifyView,
    PasswordResetOtpResendView,
)

otp_urlpatterns = [
    path("register/otp/", RegisterOtpInitiateView.as_view(), name="register-otp-initiate"),
    path("register/verify-otp/", RegisterOtpVerifyView.as_view(), name="register-otp-verify"),
    path("register/resend-otp/", RegisterOtpResendView.as_view(), name="register-otp-resend"),
    path("password-reset/otp/", PasswordResetOtpInitiateView.as_view(), name="password-reset-otp-initiate"),
    path("password-reset/verify-otp/", PasswordResetOtpVerifyView.as_view(), name="password-reset-otp-verify"),
    path("password-reset/resend-otp/", PasswordResetOtpResendView.as_view(), name="password-reset-otp-resend"),
]
