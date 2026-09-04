from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from apps.notifications.selectors import get_notification_by_id


@shared_task(bind=True, max_retries=3)
def send_notification_email(self, notification_id: int):
    """
    Send responsive HTML email notification to user.
    Called asynchronously when in-app notification is created.
    """
    from apps.notifications.models import Notification
    try:
        notification = Notification.objects.select_related('recipient').get(id=notification_id)
        user = notification.recipient
        
        # Only send if user has email notifications enabled
        if hasattr(user, 'profile') and not user.profile.email_notifications:
            return

        context = {
            "title": notification.title,
            "body": notification.body,
            "user_name": user.first_name or user.email.split("@")[0],
            "action_url": getattr(notification, "action_url", "") or f"{settings.FRONTEND_URL}/dashboard",
            "frontend_url": settings.FRONTEND_URL,
        }
        html_content = render_to_string("emails/general_notification.html", context)
        text_content = strip_tags(html_content)
        
        email = EmailMultiAlternatives(
            subject=f"{notification.title} - FreelanceFlow",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=True)
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3)
def notify_freelancer_bid_accepted(self, contract_id: int):
    """
    Notify a freelancer that their bid was accepted and a contract was created.
    Called asynchronously by the bidding service after bid acceptance.
    """
    from apps.bidding.models import Contract
    from apps.notifications.services import create_notification
    try:
        contract = Contract.objects.select_related(
            'bid__freelancer', 'bid__project'
        ).get(id=contract_id)
        freelancer = contract.bid.freelancer
        project = contract.bid.project

        create_notification(
            recipient=freelancer,
            title="Contract Proposal Received!",
            body=(
                f"Congratulations! Your bid for \"{project.title}\" has been accepted. "
                f"A contract proposal has been created. Please review and accept the contract to begin working."
            ),
            notification_type="BID_ACCEPTED",
        )
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
