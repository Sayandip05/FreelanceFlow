# Generated migration for Razorpay integration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
    ]

    operations = [
        # Rename stripe_payment_intent_id to razorpay_order_id
        migrations.RenameField(
            model_name='payment',
            old_name='stripe_payment_intent_id',
            new_name='razorpay_order_id',
        ),
        # Update help text for razorpay_order_id
        migrations.AlterField(
            model_name='payment',
            name='razorpay_order_id',
            field=models.CharField(
                blank=True,
                help_text='Razorpay Order ID',
                max_length=255
            ),
        ),
        # Add razorpay_payment_id field
        migrations.AddField(
            model_name='payment',
            name='razorpay_payment_id',
            field=models.CharField(
                blank=True,
                help_text='Razorpay Payment ID',
                max_length=255
            ),
        ),
        # Rename stripe_event_id to razorpay_event_id
        migrations.RenameField(
            model_name='paymentevent',
            old_name='stripe_event_id',
            new_name='razorpay_event_id',
        ),
    ]
