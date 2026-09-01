import json
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.users.models import User, FreelancerProfile, ClientProfile

class Command(BaseCommand):
    help = "Seeds users for load testing based on the credentials json file."

    def handle(self, *args, **options):
        from django.conf import settings
        credentials_path = os.path.join(
            settings.BASE_DIR,
            "benchmarks",
            "load_test_credentials.json",
        )

        if not os.path.exists(credentials_path):
            self.stdout.write(self.style.ERROR(f"Credentials file not found at {credentials_path}"))
            return

        with open(credentials_path) as f:
            data = json.load(f)

        freelancers = data.get("freelancers", [])
        clients = data.get("clients", [])

        self.stdout.write(f"Seeding {len(freelancers)} freelancers and {len(clients)} clients...")

        created_count = 0
        with transaction.atomic():
            # Seed Freelancers
            for index, item in enumerate(freelancers):
                email = item["email"]
                password = item["password"]
                
                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        "first_name": "Free",
                        "last_name": f"Lancer {index + 1}",
                        "role": User.Roles.FREELANCER,
                        "is_email_verified": True,
                    }
                )
                if created or not user.check_password(password):
                    user.set_password(password)
                    user.save()

                FreelancerProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        "bio": "Experienced freelancer seeded for Locust load testing.",
                        "skills": ["python", "django", "react", "javascript"],
                        "hourly_rate": 50.00,
                        "is_onboarded": True,
                    }
                )
                created_count += 1

            # Seed Clients
            for index, item in enumerate(clients):
                email = item["email"]
                password = item["password"]

                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        "first_name": "Cli",
                        "last_name": f"Ent {index + 1}",
                        "role": User.Roles.CLIENT,
                        "is_email_verified": True,
                    }
                )
                if created or not user.check_password(password):
                    user.set_password(password)
                    user.save()

                ClientProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        "company_name": f"LoadTest Corp {index + 1}",
                    }
                )
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {created_count} load test users."))
