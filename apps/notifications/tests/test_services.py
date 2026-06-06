"""
Tests for apps.notifications.services.

Coverage:
- create_notification: success, missing type raises ValueError
- mark_notification_as_read: marks correct notification, returns None for wrong user
- mark_all_as_read: marks all unread for user, does not touch other user's notifications
- delete_notification: deletes own, returns False for other user's notification
"""
from django.test import TestCase

from apps.notifications.services import (
    create_notification,
    mark_notification_as_read,
    mark_all_as_read,
    delete_notification,
)
from apps.notifications.models import Notification
from apps.users.tests.factories import make_freelancer, make_client


class CreateNotificationTest(TestCase):

    def setUp(self):
        self.user = make_freelancer()

    def test_creates_notification_successfully(self):
        n = create_notification(
            recipient=self.user,
            title="Test Notification",
            body="This is the body.",
            notification_type=Notification.Type.BID_SUBMITTED,
        )
        self.assertIsNotNone(n.pk)
        self.assertFalse(n.is_read)

    def test_raises_without_notification_type(self):
        with self.assertRaises(ValueError):
            create_notification(
                recipient=self.user,
                title="Missing type",
                body="Body text.",
            )

    def test_accepts_type_via_kwargs(self):
        """create_notification also accepts type= as a kwarg alias."""
        n = create_notification(
            recipient=self.user,
            title="Kwarg Test",
            body="Body.",
            type=Notification.Type.BID_ACCEPTED,
        )
        self.assertIsNotNone(n.pk)


class MarkAsReadTest(TestCase):

    def setUp(self):
        self.user = make_freelancer(email="fl@notif.test")
        self.other_user = make_client(email="cl@notif.test")
        self.notification = create_notification(
            recipient=self.user,
            title="Unread",
            body="Body.",
            notification_type=Notification.Type.LOG_SUBMITTED,
        )

    def test_mark_notification_as_read(self):
        updated = mark_notification_as_read(self.notification.id, self.user)
        self.assertTrue(updated.is_read)

    def test_wrong_user_returns_none(self):
        result = mark_notification_as_read(self.notification.id, self.other_user)
        self.assertIsNone(result)

    def test_nonexistent_notification_returns_none(self):
        result = mark_notification_as_read(99999, self.user)
        self.assertIsNone(result)


class MarkAllAsReadTest(TestCase):

    def setUp(self):
        self.user = make_freelancer(email="fl@all.test")
        self.other_user = make_client(email="cl@all.test")
        for i in range(3):
            create_notification(
                recipient=self.user,
                title=f"Notif {i}",
                body="Body.",
                notification_type=Notification.Type.LOG_SUBMITTED,
            )
        create_notification(
            recipient=self.other_user,
            title="Other",
            body="Body.",
            notification_type=Notification.Type.BID_SUBMITTED,
        )

    def test_marks_all_unread_for_user(self):
        count = mark_all_as_read(self.user)
        self.assertEqual(count, 3)
        remaining = Notification.objects.filter(recipient=self.user, is_read=False).count()
        self.assertEqual(remaining, 0)

    def test_does_not_touch_other_user_notifications(self):
        mark_all_as_read(self.user)
        other_unread = Notification.objects.filter(recipient=self.other_user, is_read=False).count()
        self.assertEqual(other_unread, 1)

    def test_returns_zero_when_all_already_read(self):
        mark_all_as_read(self.user)
        count = mark_all_as_read(self.user)
        self.assertEqual(count, 0)


class DeleteNotificationTest(TestCase):

    def setUp(self):
        self.user = make_freelancer(email="fl@del.notif.test")
        self.other_user = make_client(email="cl@del.notif.test")
        self.notification = create_notification(
            recipient=self.user,
            title="To Delete",
            body="Body.",
            notification_type=Notification.Type.PAYMENT_RELEASED,
        )

    def test_owner_can_delete_notification(self):
        result = delete_notification(self.notification.id, self.user)
        self.assertTrue(result)
        self.assertFalse(Notification.objects.filter(id=self.notification.id).exists())

    def test_other_user_cannot_delete_notification(self):
        result = delete_notification(self.notification.id, self.other_user)
        self.assertFalse(result)
        self.assertTrue(Notification.objects.filter(id=self.notification.id).exists())
