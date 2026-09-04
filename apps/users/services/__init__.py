from django.core.mail import send_mail  # re-exported so tests can patch apps.users.services.send_mail
from .services import (
    create_user,
    update_profile,
    change_password,
    send_password_reset_email,
    reset_password,
    send_verification_email,
    verify_email,
    update_avatar,
    toggle_freelancer_availability,
    deactivate_account,
    reactivate_account,
)
from .services_activity import (
    log_activity,
    get_user_activity_log,
    get_recent_logins,
    get_security_events,
    get_payment_activities,
    get_activity_summary,
    ActivityAction,
)
from .services_status import (
    update_online_status,
    set_user_online,
    set_user_offline,
    update_last_seen,
    get_user_status,
    is_user_online,
    get_online_users,
    get_online_count,
    set_status_message,
    clear_status_message,
    cleanup_stale_online_status,
)
