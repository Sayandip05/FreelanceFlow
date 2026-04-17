from rest_framework.throttling import UserRateThrottle
from django.core.cache import cache


class TieredRateThrottle(UserRateThrottle):
    """
    Rate throttle that varies based on user's subscription tier.
    
    Free users: 30 requests per minute
    Pro users: 300 requests per minute
    """
    
    def get_cache_key(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return None
        
        tier = self._get_user_tier(request.user)
        return f"throttle_{tier}_{request.user.pk}"
    
    def get_rate(self):
        # This is called before we have access to the request
        # We'll override allow_request instead
        return "30/minute"
    
    def allow_request(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return True
        
        tier = self._get_user_tier(request.user)
        
        # Set rate based on tier
        if tier == "PRO":
            self.rate = "300/minute"
        else:
            self.rate = "30/minute"
        
        self.num_requests, self.duration = self.parse_rate(self.rate)
        
        return super().allow_request(request, view)
    
    def _get_user_tier(self, user):
        """Get user's subscription tier."""
        if hasattr(user, 'freelancer_profile'):
            return getattr(user.freelancer_profile, 'subscription_tier', 'FREE')
        return 'FREE'


class LoginRateThrottle(UserRateThrottle):
    """
    Strict rate limit for login attempts to prevent brute force.
    """
    rate = "5/minute"
