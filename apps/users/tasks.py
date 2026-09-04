from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import User


@shared_task
def send_welcome_email_task(user_id: int):
    """
    Send beautiful responsive HTML welcome email to newly registered user.
    """
    try:
        user = User.objects.get(id=user_id)
        action_url = f"{settings.FRONTEND_URL}/freelancer/onboarding" if user.role == User.Roles.FREELANCER else f"{settings.FRONTEND_URL}/client/onboarding"
        
        context = {
            "user_name": user.first_name or user.email.split("@")[0],
            "is_freelancer": user.role == User.Roles.FREELANCER,
            "action_url": action_url,
            "frontend_url": settings.FRONTEND_URL,
        }
        
        subject = "Welcome to FreelanceFlow! ⚡"
        html_content = render_to_string("emails/welcome_email.html", context)
        text_content = strip_tags(html_content)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=True)
    except User.DoesNotExist:
        pass
