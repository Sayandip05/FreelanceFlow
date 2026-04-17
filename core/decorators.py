"""Custom decorators for views."""
from functools import wraps
from django.views.decorators.csrf import csrf_exempt


def api_csrf_exempt(view_func):
    """
    Decorator to exempt API views from CSRF validation.
    Use this for API endpoints that use token authentication.
    """
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        return csrf_exempt(view_func)(*args, **kwargs)
    return wrapped_view
