"""Add avatar, availability, and deactivation fields."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_add_rating_fields'),
    ]

    operations = [
        # User model - deactivation fields
        migrations.AddField(
            model_name='user',
            name='is_deactivated',
            field=models.BooleanField(default=False, help_text='User has deactivated their account (soft delete)'),
        ),
        migrations.AddField(
            model_name='user',
            name='deactivated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        
        # FreelancerProfile - avatar and availability
        migrations.AddField(
            model_name='freelancerprofile',
            name='avatar',
            field=models.URLField(blank=True, help_text='Profile photo URL', max_length=500),
        ),
        migrations.AddField(
            model_name='freelancerprofile',
            name='is_available',
            field=models.BooleanField(default=True, help_text='Whether freelancer is available for new projects'),
        ),
        
        # ClientProfile - avatar
        migrations.AddField(
            model_name='clientprofile',
            name='avatar',
            field=models.URLField(blank=True, help_text='Profile photo URL', max_length=500),
        ),
    ]
