"""
Test factory helpers for the users app.

These are lightweight helper functions (not factory_boy) to keep the
dependency list minimal. Every test that needs a User should import
from here so fixture creation is consistent and DRY.
"""
from apps.users.models import User, FreelancerProfile, ClientProfile


def make_freelancer(
    email: str = "freelancer@test.com",
    password: str = "StrongPass#123",
    first_name: str = "Alice",
    last_name: str = "Dev",
    **kwargs,
) -> User:
    """Create and return a freelancer user (triggers profile creation via signal)."""
    user = User.objects.create_user(
        email=email,
        password=password,
        role=User.Roles.FREELANCER,
        first_name=first_name,
        last_name=last_name,
        **kwargs,
    )
    return user


def make_client(
    email: str = "client@test.com",
    password: str = "StrongPass#123",
    first_name: str = "Bob",
    last_name: str = "Client",
    **kwargs,
) -> User:
    """Create and return a client user (triggers profile creation via signal)."""
    user = User.objects.create_user(
        email=email,
        password=password,
        role=User.Roles.CLIENT,
        first_name=first_name,
        last_name=last_name,
        **kwargs,
    )
    return user
