from django.db import models
from django.conf import settings
from apps.bidding.models import Contract


class Payment(models.Model):
    """
    Payment model for tracking all money movement.
    """
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ESCROWED = "ESCROWED", "Escrowed"
        PAYOUT_PENDING = "PAYOUT_PENDING", "Payout Pending"
        RELEASED = "RELEASED", "Released"
        PAYOUT_FAILED = "PAYOUT_FAILED", "Payout Failed"
        REFUNDED = "REFUNDED", "Refunded"
    
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name="payments"
    )
    milestone = models.OneToOneField(
        "payments.PaymentMilestone",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payment_record"
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    razorpay_order_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Razorpay Order ID"
    )
    razorpay_payment_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Razorpay Payment ID"
    )
    razorpay_payout_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="RazorpayX Payout ID"
    )
    razorpay_refund_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Razorpay Refund ID"
    )
    refund_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Amount refunded to client (if any)"
    )
    payout_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "payments"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=['contract', 'status'],
                name='payment_contract_status_idx'
            ),
            models.Index(
                fields=['razorpay_order_id'],
                name='payment_rzp_order_idx'
            ),
            models.Index(
                fields=['razorpay_payment_id'],
                name='payment_rzp_pay_idx'
            ),
        ]
    
    def __str__(self):
        return f"Payment {self.id} - {self.status}"


class Escrow(models.Model):
    """
    Escrow model for tracking held funds.
    """
    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name="escrow"
    )
    held_amount = models.DecimalField(max_digits=12, decimal_places=2)
    refund_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Amount refunded from escrow to client"
    )
    released_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = "escrows"
    
    def __str__(self):
        return f"Escrow for Payment {self.payment.id}"


class PlatformEarning(models.Model):
    """
    Platform earnings from each payment (revenue tracking).
    """
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name="platform_earnings"
    )
    cut_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    cut_amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "platform_earnings"
    
    def __str__(self):
        return f"Earning: {self.cut_amount} ({self.cut_percentage}%)"


class PaymentEvent(models.Model):
    """
    Payment event log for Razorpay webhook idempotency.
    """
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name="events"
    )
    razorpay_event_id = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=100)
    processed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "payment_events"
    
    def __str__(self):
        return f"Event: {self.razorpay_event_id}"
