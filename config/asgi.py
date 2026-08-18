import os
import signal
import logging
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

logger = logging.getLogger(__name__)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

# Import routing after Django setup
django_asgi_app = get_asgi_application()

# Import all WebSocket routing modules
from apps.messaging import routing as chat_routing
from apps.notifications import routing as notif_routing
from apps.payments import routing as contract_routing

# Combine all WS URL patterns — single Daphne process handles everything
all_websocket_urlpatterns = (
    chat_routing.websocket_urlpatterns
    + notif_routing.websocket_urlpatterns
    + contract_routing.websocket_urlpatterns
)

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(all_websocket_urlpatterns)
    ),
})


# Graceful shutdown handler for ASGI/Daphne
async def cleanup_on_shutdown():
    """
    Cleanup function called during graceful shutdown.
    Closes WebSocket connections and cleans up resources.
    """
    logger.info("ASGI application shutting down, cleaning up resources...")
    
    try:
        # Close channel layer connections
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        
        if channel_layer and hasattr(channel_layer, 'flush'):
            await channel_layer.flush()
            logger.info("Flushed channel layer")
        
        # Close database connections
        from django.db import connections
        for conn in connections.all():
            conn.close()
        logger.info("Closed database connections")
        
        # Close cache connections
        from django.core.cache import cache
        if hasattr(cache, 'close'):
            cache.close()
        logger.info("Closed cache connections")
        
    except Exception as e:
        logger.error(f"Error during ASGI cleanup: {e}", exc_info=True)


def handle_sigterm(signum, frame):
    """Handle SIGTERM for graceful shutdown."""
    logger.info("Received SIGTERM, initiating graceful ASGI shutdown...")
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(cleanup_on_shutdown())
    except Exception as e:
        logger.error(f"Error scheduling cleanup: {e}")
    finally:
        raise SystemExit(0)


# Register signal handlers safely in main thread only
try:
    import threading
    if threading.current_thread() is threading.main_thread():
        signal.signal(signal.SIGTERM, handle_sigterm)
        signal.signal(signal.SIGINT, handle_sigterm)
except (ValueError, AttributeError):
    pass
 

