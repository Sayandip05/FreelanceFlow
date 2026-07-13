"""
Shared test factories for projects, bidding, payments, and worklogs tests.

Provides a single `ProjectFactory` and related helpers so fixture
creation is consistent across the entire test suite.
"""
from datetime import date, timedelta
from apps.users.models import User
from apps.projects.models import Project, ProjectSkill
from apps.bidding.models import Bid, Contract
def make_freelancer(email="fl@proj.test", password="StrongPass#123"):
    return User.objects.create_user(
        email=email,
        password=password,
        role=User.Roles.FREELANCER,
        first_name="Alice",
        last_name="Dev",
    )


def make_client(email="cl@proj.test", password="StrongPass#123"):
    return User.objects.create_user(
        email=email,
        password=password,
        role=User.Roles.CLIENT,
        first_name="Bob",
        last_name="Client",
    )


def make_project(client, title="Test Project", budget=5000, status=Project.Status.OPEN, skills=None):
    project = Project.objects.create(
        client=client,
        title=title,
        description="A detailed project description for testing purposes.",
        budget=budget,
        deadline=date.today() + timedelta(days=30),
        status=status,
    )
    if skills:
        ProjectSkill.objects.bulk_create([
            ProjectSkill(project=project, skill_name=s) for s in skills
        ])
    return project


def make_bid(project, freelancer, amount=3000, status=Bid.Status.PENDING):
    return Bid.objects.create(
        project=project,
        freelancer=freelancer,
        amount=amount,
        cover_letter="This is a detailed cover letter with more than fifty characters.",
        status=status,
    )


def make_contract(bid, agreed_amount=None):
    return Contract.objects.create(
        bid=bid,
        agreed_amount=agreed_amount or bid.amount,
    )
