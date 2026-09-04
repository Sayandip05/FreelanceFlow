import logging
import secrets
from typing import Dict, Any, Tuple
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger(__name__)
User = get_user_model()

OTP_TTL_SECONDS = 300  # 5 minutes
COOLDOWN_TTL_SECONDS = 30  # 30 seconds
MAX_ATTEMPTS = 5


def generate_otp() -> str:
    """Generate a cryptographically secure 6-digit numeric OTP."""
    return str(secrets.randbelow(900000) + 100000)


def _get_cooldown_remaining(cooldown_key: str) -> int:
    """Get remaining seconds on a cooldown key if supported by the cache backend."""
    try:
        ttl = cache.ttl(cooldown_key)
        if ttl is not None and ttl > 0:
            return ttl
    except Exception:
        pass
    if cache.get(cooldown_key):
        return COOLDOWN_TTL_SECONDS
    return 0


def _send_otp_email(to_email: str, otp_code: str, flow: str, first_name: str = "") -> None:
    """Render and dispatch the OTP notification email."""
    if flow == "registration":
        template = "emails/email_verification.html"
        subject = "Verify Your FreelanceFlow Account - OTP Code"
    else:
        template = "emails/password_reset.html"
        subject = "Reset Your FreelanceFlow Password - OTP Code"

    display_name = first_name or to_email.split("@")[0]
    frontend_url = getattr(settings, "FRONTEND_URL", "https://freelanceflow.debabrata.site")

    context = {
        "otp": otp_code,
        "otp_code": otp_code,
        "user_name": display_name,
        "user": {
            "first_name": display_name,
            "username": display_name,
        },
        "validity_minutes": 5,
        "frontend_url": frontend_url,
        "verification_url": frontend_url,
        "reset_url": frontend_url,
    }


    try:
        html_content = render_to_string(template, context)
        send_mail(
            subject=subject,
            message=f"Your FreelanceFlow OTP code is: {otp_code}. It expires in 5 minutes.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            html_message=html_content,
            fail_silently=False,
        )
    except Exception as e:
        logger.error(f"Failed to send OTP email to {to_email}: {e}")
        raise ValidationError({"detail": "Failed to send verification email. Please try again later."})


# ==========================================
# Registration Flow
# ==========================================

def initiate_registration_otp(
    email: str,
    password: str,
    role: str = "CLIENT",
    first_name: str = "",
    last_name: str = ""
) -> Dict[str, Any]:
    """
    Validate user uniqueness, verify cooldown, generate 6-digit OTP,
    store payload in Redis for 5 minutes, and send email.
    """
    email = email.lower().strip()
    role = role.upper().strip()

    if User.objects.filter(email=email).exists():
        raise ValidationError({"email": "An account with this email already exists."})

    cooldown_key = f"otp:cooldown:reg:{email}"
    cooldown_left = _get_cooldown_remaining(cooldown_key)
    if cooldown_left > 0:
        raise ValidationError({
            "detail": f"Please wait {cooldown_left} seconds before requesting a new OTP.",
            "cooldown_remaining": cooldown_left,
        })

    otp = generate_otp()
    reg_key = f"otp:reg:{email}"

    data = {
        "otp": otp,
        "payload": {
            "email": email,
            "password": password,
            "role": role,
            "first_name": first_name.strip(),
            "last_name": last_name.strip(),
        },
        "attempts": 0,
    }

    cache.set(reg_key, data, timeout=OTP_TTL_SECONDS)
    cache.set(cooldown_key, True, timeout=COOLDOWN_TTL_SECONDS)

    _send_otp_email(to_email=email, otp_code=otp, flow="registration", first_name=first_name)

    return {
        "message": "Verification OTP sent to your email.",
        "email": email,
        "expires_in": OTP_TTL_SECONDS,
        "cooldown": COOLDOWN_TTL_SECONDS,
    }


def verify_registration_otp(email: str, otp: str) -> Tuple[Any, Dict[str, str]]:
    """
    Verify the submitted registration OTP, enforce max 5 attempts,
    create the user in PostgreSQL with is_email_verified=True, and issue JWT.
    """
    email = email.lower().strip()
    otp = str(otp).strip()
    reg_key = f"otp:reg:{email}"

    data = cache.get(reg_key)
    if not data:
        raise ValidationError({"detail": "OTP has expired or is invalid. Please request a new OTP."})

    if data.get("attempts", 0) >= MAX_ATTEMPTS:
        cache.delete(reg_key)
        raise ValidationError({"detail": "Too many failed attempts. This OTP has been invalidated. Please request a new OTP."})

    if str(data.get("otp")) != otp:
        data["attempts"] = data.get("attempts", 0) + 1
        # preserve remaining ttl
        try:
            ttl = cache.ttl(reg_key)
            ttl = ttl if (ttl and ttl > 0) else OTP_TTL_SECONDS
        except Exception:
            ttl = OTP_TTL_SECONDS
        cache.set(reg_key, data, timeout=ttl)
        remaining = MAX_ATTEMPTS - data["attempts"]
        raise ValidationError({
            "detail": f"Invalid OTP. {remaining} attempt{'s' if remaining != 1 else ''} remaining.",
            "attempts_remaining": remaining,
        })

    # OTP is valid
    payload = data["payload"]
    if User.objects.filter(email=email).exists():
        cache.delete(reg_key)
        raise ValidationError({"email": "An account with this email already exists."})

    user = User.objects.create_user(
        email=payload["email"],
        password=payload["password"],
        role=payload.get("role", "CLIENT"),
        first_name=payload.get("first_name", ""),
        last_name=payload.get("last_name", ""),
        is_email_verified=True,
    )

    # Invalidate cache
    cache.delete(reg_key)
    cache.delete(f"otp:cooldown:reg:{email}")

    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    tokens = {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }

    return user, tokens


def resend_registration_otp(email: str) -> Dict[str, Any]:
    """
    Regenerate and resend OTP for an ongoing registration session after cooldown.
    """
    email = email.lower().strip()
    reg_key = f"otp:reg:{email}"
    cooldown_key = f"otp:cooldown:reg:{email}"

    cooldown_left = _get_cooldown_remaining(cooldown_key)
    if cooldown_left > 0:
        raise ValidationError({
            "detail": f"Please wait {cooldown_left} seconds before requesting a new OTP.",
            "cooldown_remaining": cooldown_left,
        })

    data = cache.get(reg_key)
    if not data:
        raise ValidationError({"detail": "No pending registration session found. Please fill out the registration form again."})

    new_otp = generate_otp()
    data["otp"] = new_otp
    data["attempts"] = 0

    cache.set(reg_key, data, timeout=OTP_TTL_SECONDS)
    cache.set(cooldown_key, True, timeout=COOLDOWN_TTL_SECONDS)

    payload = data.get("payload", {})
    first_name = payload.get("first_name", "")
    _send_otp_email(to_email=email, otp_code=new_otp, flow="registration", first_name=first_name)

    return {
        "message": "A new verification OTP has been sent to your email.",
        "email": email,
        "expires_in": OTP_TTL_SECONDS,
        "cooldown": COOLDOWN_TTL_SECONDS,
    }


# ==========================================
# Password Reset Flow
# ==========================================

def initiate_password_reset_otp(email: str) -> Dict[str, Any]:
    """
    Initiate forgot password flow by generating 6-digit OTP for registered user.
    """
    email = email.lower().strip()
    user = User.objects.filter(email=email).first()
    if not user:
        raise ValidationError({"email": "No account found with this email address."})

    cooldown_key = f"otp:cooldown:pwd:{email}"
    cooldown_left = _get_cooldown_remaining(cooldown_key)
    if cooldown_left > 0:
        raise ValidationError({
            "detail": f"Please wait {cooldown_left} seconds before requesting a new OTP.",
            "cooldown_remaining": cooldown_left,
        })

    otp = generate_otp()
    pwd_key = f"otp:pwd:{email}"

    data = {
        "otp": otp,
        "user_id": str(user.id),
        "attempts": 0,
    }

    cache.set(pwd_key, data, timeout=OTP_TTL_SECONDS)
    cache.set(cooldown_key, True, timeout=COOLDOWN_TTL_SECONDS)

    _send_otp_email(to_email=email, otp_code=otp, flow="password_reset", first_name=user.first_name)

    return {
        "message": "Password reset OTP sent to your email.",
        "email": email,
        "expires_in": OTP_TTL_SECONDS,
        "cooldown": COOLDOWN_TTL_SECONDS,
    }


def validate_password_reset_otp(email: str, otp: str) -> Dict[str, Any]:
    """
    Validate that the password reset OTP is correct without consuming it yet,
    allowing the frontend to proceed to the new password step.
    """
    email = email.lower().strip()
    otp = str(otp).strip()
    pwd_key = f"otp:pwd:{email}"

    data = cache.get(pwd_key)
    if not data:
        raise ValidationError({"detail": "OTP has expired or is invalid. Please request a new OTP."})

    if data.get("attempts", 0) >= MAX_ATTEMPTS:
        cache.delete(pwd_key)
        raise ValidationError({"detail": "Too many failed attempts. This OTP has been invalidated. Please request a new OTP."})

    if str(data.get("otp")) != otp:
        data["attempts"] = data.get("attempts", 0) + 1
        try:
            ttl = cache.ttl(pwd_key)
            ttl = ttl if (ttl and ttl > 0) else OTP_TTL_SECONDS
        except Exception:
            ttl = OTP_TTL_SECONDS
        cache.set(pwd_key, data, timeout=ttl)
        remaining = MAX_ATTEMPTS - data["attempts"]
        raise ValidationError({
            "detail": f"Invalid OTP. {remaining} attempt{'s' if remaining != 1 else ''} remaining.",
            "attempts_remaining": remaining,
        })

    return {
        "message": "OTP verified successfully. Please choose your new password.",
        "valid": True,
    }


def verify_password_reset_otp(email: str, otp: str, new_password: str) -> Dict[str, str]:
    """
    Verify password reset OTP and update user's password.
    """
    email = email.lower().strip()
    otp = str(otp).strip()
    pwd_key = f"otp:pwd:{email}"

    data = cache.get(pwd_key)
    if not data:
        raise ValidationError({"detail": "OTP has expired or is invalid. Please request a new OTP."})

    if data.get("attempts", 0) >= MAX_ATTEMPTS:
        cache.delete(pwd_key)
        raise ValidationError({"detail": "Too many failed attempts. This OTP has been invalidated. Please request a new OTP."})

    if str(data.get("otp")) != otp:
        data["attempts"] = data.get("attempts", 0) + 1
        try:
            ttl = cache.ttl(pwd_key)
            ttl = ttl if (ttl and ttl > 0) else OTP_TTL_SECONDS
        except Exception:
            ttl = OTP_TTL_SECONDS
        cache.set(pwd_key, data, timeout=ttl)
        remaining = MAX_ATTEMPTS - data["attempts"]
        raise ValidationError({
            "detail": f"Invalid OTP. {remaining} attempt{'s' if remaining != 1 else ''} remaining.",
            "attempts_remaining": remaining,
        })

    # OTP is valid
    user = User.objects.filter(id=data["user_id"]).first()
    if not user:
        cache.delete(pwd_key)
        raise ValidationError({"detail": "User account no longer exists."})

    user.set_password(new_password)
    user.save()

    cache.delete(pwd_key)
    cache.delete(f"otp:cooldown:pwd:{email}")

    return {
        "message": "Password has been reset successfully. You can now log in with your new password."
    }


def resend_password_reset_otp(email: str) -> Dict[str, Any]:
    """
    Resend OTP for password reset after cooldown.
    """
    email = email.lower().strip()
    pwd_key = f"otp:pwd:{email}"
    cooldown_key = f"otp:cooldown:pwd:{email}"

    cooldown_left = _get_cooldown_remaining(cooldown_key)
    if cooldown_left > 0:
        raise ValidationError({
            "detail": f"Please wait {cooldown_left} seconds before requesting a new OTP.",
            "cooldown_remaining": cooldown_left,
        })

    user = User.objects.filter(email=email).first()
    if not user:
        raise ValidationError({"email": "No account found with this email address."})

    new_otp = generate_otp()
    data = {
        "otp": new_otp,
        "user_id": str(user.id),
        "attempts": 0,
    }

    cache.set(pwd_key, data, timeout=OTP_TTL_SECONDS)
    cache.set(cooldown_key, True, timeout=COOLDOWN_TTL_SECONDS)

    _send_otp_email(to_email=email, otp_code=new_otp, flow="password_reset", first_name=user.first_name)

    return {
        "message": "A new password reset OTP has been sent to your email.",
        "email": email,
        "expires_in": OTP_TTL_SECONDS,
        "cooldown": COOLDOWN_TTL_SECONDS,
    }
