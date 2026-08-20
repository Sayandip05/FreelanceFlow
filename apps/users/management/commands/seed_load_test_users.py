"""
Management command: seed_load_test_users

Creates a pool of pre-verified test users for Locust performance testing.
These users bypass email verification and throttle limits.

Usage:
    python manage.py seed_load_test_users            # create 20 freelancers + 10 clients
    python manage.py seed_load_test_users --count 50 # create 50 of each
    python manage.py seed_load_test_users --reset    # delete existing + recreate
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import json
import os

User = get_user_model()

LOAD_TEST_PASSWORD = "LoadTest@123"
CREDENTIALS_FILE = "benchmarks/load_test_credentials.json"


class Command(BaseCommand):
    help = "Seed test users for Locust load testing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=20,
            help="Number of users to create per role (default: 20)",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing load test users before creating new ones",
        )

    def handle(self, *args, **options):
        count = options["count"]
        reset = options["reset"]

        if reset:
            deleted, _ = User.objects.filter(
                email__endswith="@loadtest.internal"
            ).delete()
            self.stdout.write(self.style.WARNING(f"Deleted {deleted} existing load test users."))

        freelancers = []
        clients = []
        errors = 0

        # ── Create freelancers ────────────────────────────────────────────
        for i in range(1, count + 1):
            email = f"freelancer{i:03d}@loadtest.internal"
            if not User.objects.filter(email=email).exists():
                User.objects.create_user(
                    email=email,
                    password=LOAD_TEST_PASSWORD,
                    first_name="Freelancer",
                    last_name=f"{i:03d}",
                    role=User.Roles.FREELANCER,
                    is_active=True,
                )
            freelancers.append({"email": email, "password": LOAD_TEST_PASSWORD, "role": "FREELANCER"})

        # ── Create clients ────────────────────────────────────────────────
        for i in range(1, count + 1):
            email = f"client{i:03d}@loadtest.internal"
            if not User.objects.filter(email=email).exists():
                User.objects.create_user(
                    email=email,
                    password=LOAD_TEST_PASSWORD,
                    first_name="Client",
                    last_name=f"{i:03d}",
                    role=User.Roles.CLIENT,
                    is_active=True,
                )
            clients.append({"email": email, "password": LOAD_TEST_PASSWORD, "role": "CLIENT"})

        # ── Save credentials JSON ─────────────────────────────────────────
        credentials = {"freelancers": freelancers, "clients": clients}
        os.makedirs("benchmarks", exist_ok=True)
        with open(CREDENTIALS_FILE, "w") as f:
            json.dump(credentials, f, indent=2)

        self.stdout.write(
            self.style.SUCCESS(
                f"\n[OK] Created {count} freelancer + {count} client load test users.\n"
                f"   Credentials saved to: {CREDENTIALS_FILE}\n"
                f"   Password for all: {LOAD_TEST_PASSWORD}\n"
            )
        )
