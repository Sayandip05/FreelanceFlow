"""
Structured logging for the Users app.
"""
import logging

logger = logging.getLogger("apps.users")


def log_user_created(user):
    logger.info("User created: id=%s email=%s role=%s", user.id, user.email, user.role)


def log_user_login(user, ip_address=None):
    logger.info("User login: id=%s email=%s ip=%s", user.id, user.email, ip_address)


def log_user_login_failed(email, ip_address=None):
    logger.warning("Login failed: email=%s ip=%s", email, ip_address)


def log_profile_updated(user):
    logger.info("Profile updated: id=%s email=%s", user.id, user.email)


def log_password_changed(user):
    logger.info("Password changed: id=%s email=%s", user.id, user.email)
