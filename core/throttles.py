from rest_framework.throttling import UserRateThrottle
from django.core.cache import cache




class LoginRateThrottle(UserRateThrottle):
    """
    Strict rate limit for login attempts to prevent brute force.
    """
    rate = "5/minute"
