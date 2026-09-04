"""Email notification service."""
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
def send_notification_email(
    recipient_email: str,
    subject: str,
    template_name: str,
    context: dict,
) -> bool:
    """
    Send an email notification using a template.
    
    Args:
        recipient_email: Recipient's email address
        subject: Email subject
        template_name: Template name (without extension)
        context: Template context
    
    Returns:
        True if email was sent successfully
    """
    try:
        # Render HTML email
        html_content = render_to_string(
            f'emails/{template_name}.html',
            context
        )
        
        # Create plain text version
        text_content = strip_tags(html_content)
        
        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email]
        )
        
        # Attach HTML version
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        email.send(fail_silently=False)
        
        return True
        
    except Exception as e:
        # Log error
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
        return False


def send_simple_email(
    recipient_email: str,
    subject: str,
    message: str,
) -> bool:
    """
    Send a simple text email.
    
    Args:
        recipient_email: Recipient's email address
        subject: Email subject
        message: Email message
    
    Returns:
        True if email was sent successfully
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        return True
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
        return False


# Email notification templates for different events

def send_bid_received_email(client_email: str, project_title: str, freelancer_name: str):
    """Send email when client receives a new bid."""
    return send_notification_email(
        recipient_email=client_email,
        subject=f"New Proposal on '{project_title}' - FreelanceFlow",
        template_name="bid_received",
        context={
            "project_title": project_title,
            "freelancer_name": freelancer_name,
            "action_url": f"{settings.FRONTEND_URL}/client/home",
            "frontend_url": settings.FRONTEND_URL,
        }
    )


def send_bid_accepted_email(freelancer_email: str, project_title: str):
    """Send email when freelancer's bid is accepted."""
    return send_notification_email(
        recipient_email=freelancer_email,
        subject=f"Your Proposal Was Accepted! - FreelanceFlow",
        template_name="bid_accepted",
        context={
            "project_title": project_title,
            "action_url": f"{settings.FRONTEND_URL}/freelancer/contracts",
            "frontend_url": settings.FRONTEND_URL,
        }
    )


def send_payment_released_email(freelancer_email: str, amount: float, project_title: str):
    """Send email when payment is released to freelancer."""
    return send_notification_email(
        recipient_email=freelancer_email,
        subject=f"Payment Released: ₹{amount:.2f} - FreelanceFlow",
        template_name="payment_released",
        context={
            "amount": f"{amount:.2f}",
            "project_title": project_title,
            "action_url": f"{settings.FRONTEND_URL}/freelancer/dashboard",
            "frontend_url": settings.FRONTEND_URL,
        }
    )


def send_deliverable_submitted_email(client_email: str, deliverable_title: str, freelancer_name: str):
    """Send email when freelancer submits a deliverable."""
    return send_notification_email(
        recipient_email=client_email,
        subject=f"Deliverable Submitted: '{deliverable_title}' - FreelanceFlow",
        template_name="deliverable_submitted",
        context={
            "deliverable_title": deliverable_title,
            "freelancer_name": freelancer_name,
            "action_url": f"{settings.FRONTEND_URL}/client/home",
            "frontend_url": settings.FRONTEND_URL,
        }
    )


def send_deliverable_approved_email(freelancer_email: str, deliverable_title: str):
    """Send email when client approves a deliverable."""
    return send_notification_email(
        recipient_email=freelancer_email,
        subject=f"Deliverable Approved: '{deliverable_title}' - FreelanceFlow",
        template_name="deliverable_approved",
        context={
            "deliverable_title": deliverable_title,
            "action_url": f"{settings.FRONTEND_URL}/freelancer/contracts",
            "frontend_url": settings.FRONTEND_URL,
        }
    )


def send_review_received_email(user_email: str, rating: int, reviewer_name: str, review_text: str = ""):
    """Send email when user receives a review."""
    return send_notification_email(
        recipient_email=user_email,
        subject=f"New {rating}-Star Review Received - FreelanceFlow",
        template_name="review_received",
        context={
            "user_name": user_email.split("@")[0],
            "rating": rating,
            "reviewer_name": reviewer_name,
            "review_text": review_text,
            "action_url": f"{settings.FRONTEND_URL}/dashboard",
            "frontend_url": settings.FRONTEND_URL,
        }
    )


def send_contract_termination_request_email(
    recipient_email: str,
    requester_name: str,
    project_title: str,
    reason: str = ""
):
    """Send email when contract termination is requested."""
    return send_notification_email(
        recipient_email=recipient_email,
        subject=f"Important: Contract Cancellation Request for '{project_title}'",
        template_name="contract_termination",
        context={
            "requester_name": requester_name,
            "project_title": project_title,
            "reason": reason,
            "action_url": f"{settings.FRONTEND_URL}/dashboard",
            "frontend_url": settings.FRONTEND_URL,
        }
    )


def send_dispute_initiated_email(recipient_email: str, disputer_name: str):
    """Send email when payment dispute is initiated."""
    return send_simple_email(
        recipient_email=recipient_email,
        subject="Payment Dispute Initiated",
        message=f"""
Hi,

{disputer_name} has initiated a payment dispute.

Our support team will review the case and contact you shortly.

Best regards,
FreelanceFlow Team
        """.strip()
    )


def send_client_weekly_report_email(
    recipient_email: str,
    client_name: str,
    freelancer_name: str,
    project_title: str,
    week_start: str,
    week_end: str,
    total_hours: str,
    pdf_url: str,
    dashboard_url: str,
) -> bool:
    """
    Send automated email notification with Azure Blob SAS download link
    to the client when a weekly progress report PDF is ready.
    """
    subject = f"📄 Progress Report Ready: {project_title} ({week_start} to {week_end})"
    context = {
        "client_name": client_name,
        "freelancer_name": freelancer_name,
        "project_title": project_title,
        "week_start": week_start,
        "week_end": week_end,
        "total_hours": total_hours,
        "pdf_url": pdf_url,
        "dashboard_url": dashboard_url,
    }
    return send_notification_email(
        recipient_email=recipient_email,
        subject=subject,
        template_name="client_weekly_report",
        context=context,
    )

