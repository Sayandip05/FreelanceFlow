"""Extended payment models - Tax Documents, Multi-Currency."""
from django.db import models
from apps.users.models import User
from .models import Payment


class TaxDocument(models.Model):
    """
    Tax documents (1099, etc.) for freelancers.
    """
    
    class DocumentType(models.TextChoices):
        FORM_1099 = "1099", "Form 1099"
        W9 = "W9", "Form W-9"
        OTHER = "OTHER", "Other"
    
    freelancer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tax_documents"
    )
    document_type = models.CharField(
        max_length=20,
        choices=DocumentType.choices
    )
    tax_year = models.IntegerField()
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2)
    document_url = models.URLField(max_length=500)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "tax_documents"
        unique_together = ["freelancer", "tax_year", "document_type"]
        ordering = ["-tax_year"]
    
    def __str__(self):
        return f"{self.document_type} for {self.freelancer.email} - {self.tax_year}"


class CurrencyExchangeRate(models.Model):
    """
    Currency exchange rates for multi-currency support.
    """
    from_currency = models.CharField(max_length=3)  # USD, EUR, etc.
    to_currency = models.CharField(max_length=3)
    rate = models.DecimalField(max_digits=10, decimal_places=6)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "currency_exchange_rates"
        unique_together = ["from_currency", "to_currency"]
    
    def __str__(self):
        return f"{self.from_currency} to {self.to_currency}: {self.rate}"


class MultiCurrencyPayment(models.Model):
    """
    Payment with multi-currency support.
    """
    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name="multi_currency"
    )
    original_currency = models.CharField(max_length=3, default='USD')
    original_amount = models.DecimalField(max_digits=10, decimal_places=2)
    converted_currency = models.CharField(max_length=3, default='USD')
    converted_amount = models.DecimalField(max_digits=10, decimal_places=2)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=6)
    conversion_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "multi_currency_payments"
    
    def __str__(self):
        return f"Payment {self.payment.id} - {self.original_currency} to {self.converted_currency}"
