from django.db import transaction
from apps.notifications.models import Notification
from apps.notifications.tasks import send_notification_email


def create_notification(
    recipient,
    title: str,
    body: str,
    notification_type: str | None = None,
    **kwargs
) -> Notification:
    """Create a new in-app notification."""
    notification_type = notification_type or kwargs.get("type")
    
    if not notification_type:
        raise ValueError("notification_type is required.")
    
    with transaction.atomic():
        notification = Notification.objects.create(
            recipient=recipient,
            title=title,
            body=body,
            type=notification_type
        )
    return notification


def mark_notification_as_read(notification_id: int, user) -> Notification | None:
    """Mark a notification as read."""
    try:
        notification = Notification.objects.get(id=notification_id, recipient=user)
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return notification
    except Notification.DoesNotExist:
        return None


def mark_all_as_read(user) -> int:
    """Mark all notifications as read for a user. Returns count updated."""
    return Notification.objects.filter(recipient=user, is_read=False).update(is_read=True)


def delete_notification(notification_id: int, user) -> bool:
    """Delete a notification. Returns True if deleted."""
    try:
        notification = Notification.objects.get(id=notification_id, recipient=user)
        notification.delete()
        return True
    except Notification.DoesNotExist:
        return False


# Convenience functions for common notification types

def notify_bid_submitted(project_owner, project_title: str, freelancer_name: str):
    """Notify client that a freelancer submitted a bid."""
    return create_notification(
        recipient=project_owner,
        title=f"New bid on '{project_title}'",
        body=f"{freelancer_name} submitted a bid on your project.",
        notification_type=Notification.Type.BID_SUBMITTED
    )


def notify_bid_accepted(freelancer, project_title: str):
    """Notify freelancer that their bid was accepted."""
    return create_notification(
        recipient=freelancer,
        title=f"Bid accepted on '{project_title}'",
        body=f"Congratulations! Your bid on '{project_title}' was accepted. The contract is now active.",
        notification_type=Notification.Type.BID_ACCEPTED
    )


def notify_escrow_created(freelancer, project_title: str, amount: float):
    """Notify freelancer that client has funded escrow."""
    return create_notification(
        recipient=freelancer,
        title=f"Escrow funded for '{project_title}'",
        body=f"Client has funded ${amount:,.2f} in escrow for your project. You can start working!",
        notification_type=Notification.Type.ESCROW_CREATED
    )


def notify_log_submitted(client, project_title: str, date_str: str):
    """Notify client that freelancer submitted a work log."""
    return create_notification(
        recipient=client,
        title=f"Work log submitted for '{project_title}'",
        body=f"A work log for {date_str} has been submitted for your review.",
        notification_type=Notification.Type.LOG_SUBMITTED
    )


def notify_report_ready(user, project_title: str, week_str: str):
    """Notify user that weekly report is ready."""
    return create_notification(
        recipient=user,
        title=f"Weekly report ready for '{project_title}'",
        body=f"Your weekly report for {week_str} is now available.",
        notification_type=Notification.Type.REPORT_READY
    )


def notify_payment_released(freelancer, project_title: str, amount: float):
    """Notify freelancer that payment was released."""
    return create_notification(
        recipient=freelancer,
        title=f"Payment released for '{project_title}'",
        body=f"${amount:,.2f} has been released to your account.",
        notification_type=Notification.Type.PAYMENT_RELEASED
    )


def notify_proof_ready(client, project_title: str):
    """Notify client that delivery proof is ready."""
    return create_notification(
        recipient=client,
        title=f"Project delivered: '{project_title}'",
        body=f"The freelancer has submitted the final delivery proof for your project.",
        notification_type=Notification.Type.PROOF_READY
    )


def notify_message_received(recipient, sender_name: str):
    """Notify user of new message."""
    return create_notification(
        recipient=recipient,
        title=f"New message from {sender_name}",
        body=f"You have received a new message.",
        notification_type=Notification.Type.MESSAGE_RECEIVED
    )
