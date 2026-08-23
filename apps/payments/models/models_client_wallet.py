from django.db import models
from django.conf import settings
from apps.payments.models.models_milestone import PaymentMilestone

class ClientWallet(models.Model):
    """
    Client wallet to hold pre-funded platform balance.
    """
    client = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="client_wallet"
    )
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "client_wallets"

    def __str__(self):
        return f"Client Wallet: {self.client.email} - Balance: {self.balance}"


class ClientDeposit(models.Model):
    """
    Records requests by clients to pre-fund their platform wallet via Razorpay.
    """
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="client_deposits"
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
    razorpay_order_id = models.CharField(
        max_length=255,
        blank=True,
        default=""
    )
    razorpay_payment_id = models.CharField(
        max_length=255,
        blank=True,
        default=""
    )
    auto_fund_milestone = models.ForeignKey(
        PaymentMilestone,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="linked_deposits",
        help_text="If set, this milestone will be funded automatically once deposit succeeds."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "client_deposits"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Deposit #{self.id} - {self.client.email} - {self.amount} ({self.status})"
