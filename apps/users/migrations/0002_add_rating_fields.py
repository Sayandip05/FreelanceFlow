"""Add rating fields to user profiles."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='freelancerprofile',
            name='average_rating',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=3),
        ),
        migrations.AddField(
            model_name='freelancerprofile',
            name='total_reviews',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='clientprofile',
            name='average_rating',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=3),
        ),
        migrations.AddField(
            model_name='clientprofile',
            name='total_reviews',
            field=models.IntegerField(default=0),
        ),
    ]
