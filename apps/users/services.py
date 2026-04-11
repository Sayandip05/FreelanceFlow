from django.db import transaction
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import User, FreelancerProfile, ClientProfile
from core.exceptions import ValidationError, BusinessError


def create_user(
    email: str,
    password: str,
    role: str,
    first_name: str = "",
    last_name: str = "",
    **extra_fields
) -> User:
    """
    Create a new user with the given email and password.
    
    Args:
        email: User's email address
        password: User's password
        role: Either 'CLIENT' or 'FREELANCER'
        first_name: Optional first name
        last_name: Optional last name
    
    Returns:
        Created User instance
    
    Raises:
        ValidationError: If validation fails
    """
    if not email:
        raise ValidationError("Email is required.", field="email")
    
    if not password:
        raise ValidationError("Password is required.", field="password")
    
    if role not in [User.Roles.CLIENT, User.Roles.FREELANCER]:
        raise ValidationError("Invalid role.", field="role")
    
    # Check if email already exists
    if User.objects.filter(email=email).exists():
        raise ValidationError("Email already registered.", field="email")
    
    # Validate password
    try:
        validate_password(password)
    except DjangoValidationError as e:
        raise ValidationError(str(e.messages[0]), field="password")
    
    with transaction.atomic():
        user = User.objects.create_user(
            email=email,
            password=password,
            role=role,
            first_name=first_name,
            last_name=last_name,
            **extra_fields
        )
        
        # Profile is created via signal
        return user


def update_profile(user: User, data: dict) -> User:
    """
    Update user profile information.
    
    Args:
        user: User instance to update
        data: Dictionary of fields to update
    
    Returns:
        Updated User instance
    """
    allowed_user_fields = ['first_name', 'last_name']
    
    with transaction.atomic():
        # Update user fields
        for field in allowed_user_fields:
            if field in data:
                setattr(user, field, data[field])
        user.save()
        
        # Update profile based on role
        if user.role == User.Roles.FREELANCER:
            profile = user.freelancer_profile
            if 'bio' in data:
                profile.bio = data['bio']
            if 'skills' in data:
                profile.skills = data['skills']
            if 'hourly_rate' in data:
                profile.hourly_rate = data['hourly_rate']
            profile.save()
            
        elif user.role == User.Roles.CLIENT:
            profile = user.client_profile
            if 'company_name' in data:
                profile.company_name = data['company_name']
            profile.save()
        
        return user


def update_subscription_tier(user: User, tier: str) -> FreelancerProfile:
    """
    Update freelancer's subscription tier.
    
    Args:
        user: Freelancer user
        tier: Either 'FREE' or 'PRO'
    
    Returns:
        Updated FreelancerProfile
    """
    if user.role != User.Roles.FREELANCER:
        raise BusinessError("Only freelancers can have subscription tiers.")
    
    if tier not in [FreelancerProfile.SubscriptionTier.FREE, FreelancerProfile.SubscriptionTier.PRO]:
        raise ValidationError("Invalid subscription tier.", field="tier")
    
    profile = user.freelancer_profile
    profile.subscription_tier = tier
    profile.save()
    
    return profile


def change_password(user: User, old_password: str, new_password: str) -> User:
    """
    Change user's password.
    
    Args:
        user: User instance
        old_password: Current password
        new_password: New password
    
    Returns:
        Updated User instance
    """
    if not user.check_password(old_password):
        raise ValidationError("Current password is incorrect.", field="old_password")
    
    try:
        validate_password(new_password)
    except DjangoValidationError as e:
        raise ValidationError(str(e.messages[0]), field="new_password")
    
    user.set_password(new_password)
    user.save()
    
    return user



def send_password_reset_email(email: str) -> bool:
    """
    Send password reset email to user.
    
    Args:
        email: User's email address
    
    Returns:
        True if email was sent
    """
    from django.core.mail import send_mail
    from django.conf import settings
    from django.utils.http import urlsafe_base64_encode
    from django.utils.encoding import force_bytes
    from .tokens import password_reset_token
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # Don't reveal if email exists or not
        return True
    
    # Generate token
    token = password_reset_token.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # Create reset link (frontend URL)
    reset_link = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"
    
    # Send email
    subject = "Password Reset Request - FreelanceFlow"
    message = f"""
    Hi {user.first_name or user.email},
    
    You requested a password reset for your FreelanceFlow account.
    
    Click the link below to reset your password:
    {reset_link}
    
    This link will expire in 24 hours.
    
    If you didn't request this, please ignore this email.
    
    Best regards,
    FreelanceFlow Team
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )
    
    return True


def reset_password(uid: str, token: str, new_password: str) -> User:
    """
    Reset user's password using token.
    
    Args:
        uid: Base64 encoded user ID
        token: Password reset token
        new_password: New password
    
    Returns:
        Updated User instance
    """
    from django.utils.http import urlsafe_base64_decode
    from django.utils.encoding import force_str
    from .tokens import password_reset_token
    
    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        raise ValidationError("Invalid reset link.", code="invalid_token")
    
    if not password_reset_token.check_token(user, token):
        raise ValidationError("Invalid or expired reset link.", code="invalid_token")
    
    try:
        validate_password(new_password)
    except DjangoValidationError as e:
        raise ValidationError(str(e.messages[0]), field="new_password")
    
    user.set_password(new_password)
    user.save()
    
    return user


def send_verification_email(user: User) -> bool:
    """
    Send email verification link to user.
    
    Args:
        user: User instance
    
    Returns:
        True if email was sent
    """
    from django.core.mail import send_mail
    from django.conf import settings
    from django.utils.http import urlsafe_base64_encode
    from django.utils.encoding import force_bytes
    from .tokens import account_activation_token
    
    # Generate token
    token = account_activation_token.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # Create verification link (frontend URL)
    verification_link = f"{settings.FRONTEND_URL}/verify-email?uid={uid}&token={token}"
    
    # Send email
    subject = "Verify Your Email - FreelanceFlow"
    message = f"""
    Hi {user.first_name or user.email},
    
    Welcome to FreelanceFlow! Please verify your email address to activate your account.
    
    Click the link below to verify:
    {verification_link}
    
    This link will expire in 24 hours.
    
    Best regards,
    FreelanceFlow Team
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
    
    return True


def verify_email(uid: str, token: str) -> User:
    """
    Verify user's email using token.
    
    Args:
        uid: Base64 encoded user ID
        token: Email verification token
    
    Returns:
        Updated User instance
    """
    from django.utils.http import urlsafe_base64_decode
    from django.utils.encoding import force_str
    from .tokens import account_activation_token
    
    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        raise ValidationError("Invalid verification link.", code="invalid_token")
    
    if not account_activation_token.check_token(user, token):
        raise ValidationError("Invalid or expired verification link.", code="invalid_token")
    
    if user.is_active:
        raise ValidationError("Email already verified.", code="already_verified")
    
    user.is_active = True
    user.save()
    
    return user



def update_avatar(user: User, avatar_url: str) -> User:
    """
    Update user's avatar/profile photo.
    
    Args:
        user: User instance
        avatar_url: URL of the uploaded avatar
    
    Returns:
        Updated User instance
    """
    if user.role == User.Roles.FREELANCER:
        profile = user.freelancer_profile
        profile.avatar = avatar_url
        profile.save()
    elif user.role == User.Roles.CLIENT:
        profile = user.client_profile
        profile.avatar = avatar_url
        profile.save()
    
    return user


def toggle_freelancer_availability(user: User, is_available: bool) -> FreelancerProfile:
    """
    Toggle freelancer's availability for new projects.
    
    Args:
        user: Freelancer user
        is_available: Whether freelancer is available
    
    Returns:
        Updated FreelancerProfile
    """
    if user.role != User.Roles.FREELANCER:
        raise BusinessError("Only freelancers can set availability.")
    
    profile = user.freelancer_profile
    profile.is_available = is_available
    profile.save()
    
    return profile


def deactivate_account(user: User, password: str) -> User:
    """
    Deactivate user account (soft delete).
    Requires password confirmation.
    
    Args:
        user: User instance
        password: User's password for confirmation
    
    Returns:
        Deactivated User instance
    """
    if not user.check_password(password):
        raise ValidationError("Incorrect password.", field="password")
    
    if user.is_deactivated:
        raise ValidationError("Account is already deactivated.")
    
    with transaction.atomic():
        user.is_deactivated = True
        user.deactivated_at = timezone.now()
        user.is_active = False  # Also disable login
        user.save()
        
        # Send confirmation email
        from django.core.mail import send_mail
        from django.conf import settings
        
        send_mail(
            subject="Account Deactivated - FreelanceFlow",
            message=f"""
Hi {user.first_name or user.email},

Your FreelanceFlow account has been deactivated.

If you wish to reactivate your account, please contact support.

Best regards,
FreelanceFlow Team
            """.strip(),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )
    
    return user


def reactivate_account(user: User) -> User:
    """
    Reactivate a deactivated account.
    
    Args:
        user: User instance
    
    Returns:
        Reactivated User instance
    """
    if not user.is_deactivated:
        raise ValidationError("Account is not deactivated.")
    
    user.is_deactivated = False
    user.deactivated_at = None
    user.is_active = True
    user.save()
    
    return user
