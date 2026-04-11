"""Token generators for password reset and email verification."""
from django.contrib.auth.tokens import PasswordResetTokenGenerator


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    """Token generator for email verification."""
    
    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{timestamp}{user.is_active}"


account_activation_token = AccountActivationTokenGenerator()
password_reset_token = PasswordResetTokenGenerator()
