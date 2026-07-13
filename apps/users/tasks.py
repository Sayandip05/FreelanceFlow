from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import User


@shared_task
def send_welcome_email_task(user_id: int):
    """
    Send welcome email to newly registered user.
    """
    try:
        user = User.objects.get(id=user_id)
        
        subject = "Welcome to FreelanceFlow!"
        message = f"""
        Hi {user.first_name or user.email},

        Welcome to FreelanceFlow! We're excited to have you on board.

        {'As a freelancer, you can now browse projects and start bidding on opportunities that match your skills.' if user.role == User.Roles.FREELANCER else 'As a client, you can now post projects and find talented freelancers to bring your ideas to life.'}

        Get started by completing your profile and exploring the platform.

        Best regards,
        The FreelanceFlow Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )
    except User.DoesNotExist:
        pass
