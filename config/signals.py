"""
Signal handlers for graceful shutdown.
Handles SIGTERM and SIGINT to ensure clean application shutdown.
"""
import signal
import sys
import logging
from typing import Any

logger = logging.getLogger(__name__)


class GracefulShutdown:
    """
    Handles graceful shutdown of the Django application.
    Closes database connections, cache connections, and cleans up resources.
    """
    
    def __init__(self):
        self.is_shutting_down = False
    
    def shutdown(self, signum: int, frame: Any) -> None:
        """
        Handle shutdown signal.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        if self.is_shutting_down:
            logger.warning("Shutdown already in progress, ignoring signal")
            return
        
        self.is_shutting_down = True
        signal_name = signal.Signals(signum).name
        logger.info(f"Received {signal_name} (signal {signum}), initiating graceful shutdown...")
        
        try:
            # Close all database connections
            self._close_database_connections()
            
            # Close cache connections
            self._close_cache_connections()
            
            # Close Elasticsearch connections
            self._close_elasticsearch_connections()
            
            # Flush any pending logs
            logging.shutdown()
            
            logger.info("Graceful shutdown completed successfully")
            
        except Exception as e:
            logger.error(f"Error during graceful shutdown: {e}", exc_info=True)
        finally:
            sys.exit(0)
    
    def _close_database_connections(self) -> None:
        """Close all database connections."""
        try:
            from django.db import connections
            
            for alias in connections:
                try:
                    conn = connections[alias]
                    if conn.connection is not None:
                        conn.close()
                        logger.info(f"Closed database connection: {alias}")
                except Exception as e:
                    logger.error(f"Error closing database connection {alias}: {e}")
        except Exception as e:
            logger.error(f"Error accessing database connections: {e}")
    
    def _close_cache_connections(self) -> None:
        """Close Redis cache connections."""
        try:
            from django.core.cache import caches
            from django.conf import settings
            
            for cache_alias in settings.CACHES.keys():
                try:
                    cache = caches[cache_alias]
                    if hasattr(cache, 'close'):
                        cache.close()
                        logger.info(f"Closed cache connection: {cache_alias}")
                except Exception as e:
                    logger.error(f"Error closing cache {cache_alias}: {e}")
        except Exception as e:
            logger.error(f"Error accessing cache connections: {e}")
    
    def _close_elasticsearch_connections(self) -> None:
        """Close Elasticsearch connections."""
        try:
            from django_elasticsearch_dsl.registries import registry
            
            for index in registry.get_indices():
                try:
                    # Close connections through the index
                    if hasattr(index, '_get_connection'):
                        conn = index._get_connection()
                        if hasattr(conn, 'close'):
                            conn.close()
                            logger.info(f"Closed Elasticsearch connection for index: {index._name}")
                except Exception as e:
                    logger.error(f"Error closing Elasticsearch connection: {e}")
        except ImportError:
            # Elasticsearch not installed
            pass
        except Exception as e:
            logger.error(f"Error accessing Elasticsearch connections: {e}")


# Create singleton instance
_shutdown_handler = GracefulShutdown()


def register_shutdown_handlers() -> None:
    """
    Register signal handlers for graceful shutdown.
    Call this in your Django app's ready() method or ASGI/WSGI startup.
    """
    signal.signal(signal.SIGTERM, _shutdown_handler.shutdown)
    signal.signal(signal.SIGINT, _shutdown_handler.shutdown)
    logger.info("Registered graceful shutdown handlers for SIGTERM and SIGINT")


def is_shutting_down() -> bool:
    """Check if application is currently shutting down."""
    return _shutdown_handler.is_shutting_down
