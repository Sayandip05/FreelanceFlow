"""
Middleware for handling graceful shutdown.
Rejects new requests when application is shutting down.
"""
from django.http import HttpResponse
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class GracefulShutdownMiddleware:
    """
    Middleware that rejects new requests during graceful shutdown.
    Returns 503 Service Unavailable when shutdown is in progress.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if application is shutting down
        try:
            from config.signals import is_shutting_down
            
            if is_shutting_down():
                logger.warning(f"Rejecting request to {request.path} - application is shutting down")
                return HttpResponse(
                    "Service is shutting down. Please try again in a moment.",
                    status=503,
                    content_type="text/plain"
                )
        except ImportError:
            # Signals module not available, continue normally
            pass
        
        response = self.get_response(request)
        return response
    
    def process_exception(self, request, exception):
        """Handle exceptions during shutdown."""
        try:
            from config.signals import is_shutting_down
            
            if is_shutting_down():
                logger.error(f"Exception during shutdown for {request.path}: {exception}")
                return HttpResponse(
                    "Service is shutting down.",
                    status=503,
                    content_type="text/plain"
                )
        except ImportError:
            pass
        
        return None
