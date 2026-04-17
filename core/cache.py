"""
Redis caching utilities for FreelanceFlow.

Caching Strategy:
- Project lists: 5 min TTL
- Project details: 10 min TTL
- User profiles: 15 min TTL
- Search results: 3 min TTL

Cache Invalidation:
- On create/update/delete of any cached object
- Use signal handlers or service layer hooks
"""

from functools import wraps
from typing import Any, Callable, Optional

from django.conf import settings
from django.core.cache import cache


class CacheKeys:
    """Centralized cache key definitions."""

    @staticmethod
    def project_list(page: int = 1) -> str:
        return f"projects:list:page:{page}"

    @staticmethod
    def project_detail(project_id: int) -> str:
        return f"projects:detail:{project_id}"

    @staticmethod
    def user_profile(user_id: int) -> str:
        return f"users:profile:{user_id}"

    @staticmethod
    def search_results(query: str, filters: dict = None) -> str:
        filter_str = "_".join(filters.values()) if filters else "all"
        return f"search:{query}:{filter_str}"

    @staticmethod
    def freelancer_stats(user_id: int) -> str:
        return f"freelancer:stats:{user_id}"

    @staticmethod
    def client_stats(user_id: int) -> str:
        return f"client:stats:{user_id}"

    @staticmethod
    def notification_count(user_id: int) -> str:
        return f"notifications:count:{user_id}"


class CacheService:
    """Service for managing cache operations."""

    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """Get value from cache."""
        return cache.get(key, default)

    @staticmethod
    def set(key: str, value: Any, ttl: int = 300) -> None:
        """Set value in cache with TTL in seconds."""
        cache.set(key, value, ttl)

    @staticmethod
    def delete(key: str) -> None:
        """Delete key from cache."""
        cache.delete(key)

    @staticmethod
    def delete_pattern(pattern: str) -> int:
        """Delete all keys matching pattern."""
        return cache.delete_pattern(pattern)

    @staticmethod
    def get_or_set(key: str, callable_fn: Callable, ttl: int = 300) -> Any:
        """Get from cache or execute callable and cache result."""
        value = cache.get(key)
        if value is not None:
            return value

        value = callable_fn()
        cache.set(key, value, ttl)
        return value

    @staticmethod
    def invalidate_project(project_id: int) -> None:
        """Invalidate all cache entries for a project."""
        CacheService.delete(CacheKeys.project_detail(project_id))
        CacheService.delete_pattern("projects:list:*")

    @staticmethod
    def invalidate_user(user_id: int) -> None:
        """Invalidate all cache entries for a user."""
        CacheService.delete(CacheKeys.user_profile(user_id))
        CacheService.delete_pattern(f"*:stats:{user_id}")
        CacheService.delete(CacheKeys.notification_count(user_id))

    @staticmethod
    def invalidate_search() -> None:
        """Invalidate all search cache entries."""
        CacheService.delete_pattern("search:*")


def cached(key_fn: Callable[[], str], ttl: int = 300):
    """
    Decorator to cache function results.

    Usage:
        @cached(lambda: CacheKeys.project_detail(123), ttl=600)
        def get_project(project_id):
            return Project.objects.get(id=project_id)
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = key_fn(*args, **kwargs)
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result

        return wrapper

    return decorator


def invalidate_on_save(model_class):
    """
    Signal handler decorator to invalidate cache on model save.

    Usage:
        @invalidate_on_save(Project)
        def handle_project_save(sender, instance, **kwargs):
            pass
    """

    def decorator(func: Callable) -> Callable:
        from django.db.models.signals import post_save

        post_save.connect(func, sender=model_class)
        return func

    return decorator
