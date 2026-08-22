from django.db import models
from django.conf import settings

class Wallet(models.Model):
    """
    Freelancer wallet to accumulate earnings prior to withdrawal.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wallet"
    )
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )
    withdrawn_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "freelancer_wallets"

    def __str__(self):
        return f"{self.user.email} - Balance: {self.balance}"


class WithdrawalRequest(models.Model):
    """
    Records requests by freelancers to withdraw money from their platform wallet to linked bank/UPI accounts.
    """
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    freelancer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="withdrawals"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    razorpay_payout_id = models.CharField(
        max_length=255,
        blank=True,
        default=""
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "withdrawal_requests"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Withdrawal request #{self.id} - {self.freelancer.email} - {self.amount} ({self.status})"
