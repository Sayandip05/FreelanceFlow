"""
System Announcement Services
"""
from django.db import transaction
from .models_extended import SystemAnnouncement


@transaction.atomic
def create_announcement(title, content, announcement_type='INFO', target_role=None, start_date=None, end_date=None):
    """Create system announcement"""
    return SystemAnnouncement.objects.create(
        title=title,
        content=content,
        type=announcement_type,
        target_role=target_role,
        start_date=start_date,
        end_date=end_date,
        is_active=True
    )


def get_active_announcements(user_role=None):
    """Get active announcements"""
    from django.utils import timezone
    now = timezone.now()
    
    queryset = SystemAnnouncement.objects.filter(
        is_active=True,
        start_date__lte=now
    ).filter(
        models.Q(end_date__isnull=True) | models.Q(end_date__gte=now)
    )
    
    if user_role:
        queryset = queryset.filter(
            models.Q(target_role=user_role) | models.Q(target_role__isnull=True)
        )
    
    return queryset.order_by('-start_date')
