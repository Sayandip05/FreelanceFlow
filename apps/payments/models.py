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
        RELEASED = "RELEASED", "Released"
        REFUNDED = "REFUNDED", "Refunded"
    
    contract = models.OneToOneField(
        Contract,
        on_delete=models.CASCADE,
        related_name="payment"
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "payments"
        ordering = ["-created_at"]
    
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
