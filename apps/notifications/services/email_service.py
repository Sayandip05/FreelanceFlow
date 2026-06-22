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
    return send_simple_email(
        recipient_email=client_email,
        subject=f"New Bid on '{project_title}'",
        message=f"""
Hi,

You have received a new bid on your project '{project_title}' from {freelancer_name}.

Log in to FreelanceFlow to review the bid and freelancer profile.

Best regards,
FreelanceFlow Team
        """.strip()
    )


def send_bid_accepted_email(freelancer_email: str, project_title: str):
    """Send email when freelancer's bid is accepted."""
    return send_simple_email(
        recipient_email=freelancer_email,
        subject=f"Your Bid Was Accepted!",
        message=f"""
Hi,

Congratulations! Your bid on '{project_title}' has been accepted.

A contract has been created. Log in to FreelanceFlow to view details and start working.

Best regards,
FreelanceFlow Team
        """.strip()
    )


def send_payment_released_email(freelancer_email: str, amount: float, project_title: str):
    """Send email when payment is released to freelancer."""
    return send_simple_email(
        recipient_email=freelancer_email,
        subject="Payment Released",
        message=f"""
Hi,

Great news! Payment of ${amount:.2f} has been released for your work on '{project_title}'.

The funds will be transferred to your account within 2-3 business days.

Best regards,
FreelanceFlow Team
        """.strip()
    )


def send_deliverable_submitted_email(client_email: str, deliverable_title: str, freelancer_name: str):
    """Send email when freelancer submits a deliverable."""
    return send_simple_email(
        recipient_email=client_email,
        subject="New Deliverable Submitted",
        message=f"""
Hi,

{freelancer_name} has submitted a deliverable: '{deliverable_title}'.

Please log in to FreelanceFlow to review and approve the work.

Best regards,
FreelanceFlow Team
        """.strip()
    )


def send_deliverable_approved_email(freelancer_email: str, deliverable_title: str):
    """Send email when client approves a deliverable."""
    return send_simple_email(
        recipient_email=freelancer_email,
        subject="Deliverable Approved",
        message=f"""
Hi,

Your deliverable '{deliverable_title}' has been approved by the client!

Best regards,
FreelanceFlow Team
        """.strip()
    )


def send_review_received_email(user_email: str, rating: int, reviewer_name: str):
    """Send email when user receives a review."""
    return send_simple_email(
        recipient_email=user_email,
        subject="New Review Received",
        message=f"""
Hi,

{reviewer_name} has left you a {rating}-star review.

Log in to FreelanceFlow to view the review and respond if you'd like.

Best regards,
FreelanceFlow Team
        """.strip()
    )


def send_contract_termination_request_email(
    recipient_email: str,
    requester_name: str,
    project_title: str
):
    """Send email when contract termination is requested."""
    return send_simple_email(
        recipient_email=recipient_email,
        subject="Contract Termination Request",
        message=f"""
Hi,

{requester_name} has requested to terminate the contract for '{project_title}'.

Please log in to FreelanceFlow to review the request and respond.

Best regards,
FreelanceFlow Team
        """.strip()
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
