"""
Two-Factor Authentication (2FA) Services
Handles TOTP-based 2FA enable/disable/verify operations
"""
import pyotp
import secrets
from django.db import transaction
from django.utils import timezone
from .models_extended import TwoFactorAuth


def generate_2fa_secret():
    """Generate a new TOTP secret key"""
    return pyotp.random_base32()


def generate_backup_codes(count=10):
    """Generate backup codes for 2FA recovery"""
    return [secrets.token_hex(4).upper() for _ in range(count)]


@transaction.atomic
def enable_2fa(user):
    """
    Enable 2FA for a user
    Returns: (secret_key, backup_codes, qr_code_url)
    """
    # Generate secret and backup codes
    secret_key = generate_2fa_secret()
    backup_codes = generate_backup_codes()
    
    # Create or update 2FA record
    two_fa, created = TwoFactorAuth.objects.update_or_create(
        user=user,
        defaults={
            'secret_key': secret_key,
            'is_enabled': False,  # Not enabled until verified
            'backup_codes': backup_codes
        }
    )
    
    # Generate QR code URL for authenticator apps
    totp = pyotp.TOTP(secret_key)
    qr_code_url = totp.provisioning_uri(
        name=user.email,
        issuer_name='FreelanceFlow'
    )
    
    return secret_key, backup_codes, qr_code_url


@transaction.atomic
def verify_and_enable_2fa(user, code):
    """
    Verify TOTP code and enable 2FA
    Returns: True if successful, False otherwise
    """
    try:
        two_fa = TwoFactorAuth.objects.get(user=user)
    except TwoFactorAuth.DoesNotExist:
        return False
    
    # Verify the code
    totp = pyotp.TOTP(two_fa.secret_key)
    if totp.verify(code, valid_window=1):
        two_fa.is_enabled = True
        two_fa.last_used_at = timezone.now()
        two_fa.save()
        return True
    
    return False


def verify_2fa_code(user, code):
    """
    Verify a 2FA code during login
    Returns: True if valid, False otherwise
    """
    try:
        two_fa = TwoFactorAuth.objects.get(user=user, is_enabled=True)
    except TwoFactorAuth.DoesNotExist:
        return False
    
    # Check TOTP code
    totp = pyotp.TOTP(two_fa.secret_key)
    if totp.verify(code, valid_window=1):
        two_fa.last_used_at = timezone.now()
        two_fa.save()
        return True
    
    # Check backup codes
    if code.upper() in two_fa.backup_codes:
        # Remove used backup code
        backup_codes = two_fa.backup_codes.copy()
        backup_codes.remove(code.upper())
        two_fa.backup_codes = backup_codes
        two_fa.last_used_at = timezone.now()
        two_fa.save()
        return True
    
    return False


@transaction.atomic
def disable_2fa(user):
    """Disable 2FA for a user"""
    try:
        two_fa = TwoFactorAuth.objects.get(user=user)
        two_fa.is_enabled = False
        two_fa.save()
        return True
    except TwoFactorAuth.DoesNotExist:
        return False


def is_2fa_enabled(user):
    """Check if 2FA is enabled for a user"""
    try:
        two_fa = TwoFactorAuth.objects.get(user=user)
        return two_fa.is_enabled
    except TwoFactorAuth.DoesNotExist:
        return False


@transaction.atomic
def regenerate_backup_codes(user):
    """Regenerate backup codes for a user"""
    try:
        two_fa = TwoFactorAuth.objects.get(user=user, is_enabled=True)
        backup_codes = generate_backup_codes()
        two_fa.backup_codes = backup_codes
        two_fa.save()
        return backup_codes
    except TwoFactorAuth.DoesNotExist:
        return None
