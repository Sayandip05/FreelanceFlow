"""Add refund and dispute fields to Payment model."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0002_razorpay_migration'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='refund_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='payment',
            name='razorpay_refund_id',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='payment',
            name='status',
            field=models.CharField(
                choices=[
                    ('PENDING', 'Pending'),
                    ('ESCROWED', 'Escrowed'),
                    ('RELEASED', 'Released'),
                    ('REFUNDED', 'Refunded'),
                    ('PARTIALLY_REFUNDED', 'Partially Refunded'),
                    ('FAILED', 'Failed')
                ],
                default='PENDING',
                max_length=20
            ),
        ),
    ]
