import time
import logging
import json
from typing import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.core.cache import cache

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    """
    Logs every API request with timing information.
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        start_time = time.perf_counter()

        response = self.get_response(request)

        duration = (time.perf_counter() - start_time) * 1000

        log_data = {
            "method": request.method,
            "path": request.path,
            "status": response.status_code,
            "duration_ms": round(duration, 2),
            "user_id": request.user.id if request.user.is_authenticated else None,
            "ip": self.get_client_ip(request),
        }

        if response.status_code >= 500:
            logger.error(json.dumps(log_data))
        elif response.status_code >= 400:
            logger.warning(json.dumps(log_data))
        else:
            logger.info(json.dumps(log_data))

        response["X-Response-Time"] = f"{round(duration, 2)}ms"
        return response

    @staticmethod
    def get_client_ip(request: HttpRequest) -> str:
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")


class SecurityHeadersMiddleware:
    """
    Adds security headers to every response.
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        response = self.get_response(request)

        response["X-Content-Type-Options"] = "nosniff"
        response["X-XSS-Protection"] = "1; mode=block"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"

        if settings.DEBUG:
            response["Access-Control-Allow-Origin"] = "*"
        else:
            response["Access-Control-Allow-Origin"] = ", ".join(
                settings.CORS_ALLOWED_ORIGINS
            )

        return response


class RateLimitMiddleware:
    """
    Simple in-memory rate limiting using Redis.
    Rate limits: 100/hour anonymous, 1000/hour authenticated
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        if self._is_api_request(request):
            client_id = self._get_client_id(request)
            cache_key = f"rate_limit:{client_id}:{request.path}"

            if not self._check_rate_limit(cache_key):
                return JsonResponse(
                    {
                        "error": "Rate limit exceeded",
                        "code": "RATE_LIMITED",
                        "retry_after": 3600,
                    },
                    status=429,
                )

        return self.get_response(request)

    def _is_api_request(self, request: HttpRequest) -> bool:
        return request.path.startswith("/api/")

    def _get_client_id(self, request: HttpRequest) -> str:
        if request.user.is_authenticated:
            return f"user:{request.user.id}"
        ip = request.META.get("REMOTE_ADDR", "")
        return f"ip:{ip}"

    def _check_rate_limit(self, cache_key: str) -> bool:
        limit = 1000 if cache_key.startswith("rate_limit:user:") else 100

        count = cache.get(cache_key, 0)
        if count >= limit:
            return False

        cache.set(cache_key, count + 1, 3600)
        return True


class CacheControlMiddleware:
    """
    Adds cache control headers based on request type.
    """

    CACHE_EXCLUSIONS = ["/api/", "/admin/", "/ws/"]

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        response = self.get_response(request)

        should_cache = not any(
            request.path.startswith(path) for path in self.CACHE_EXCLUSIONS
        )

        if should_cache and request.method == "GET":
            response["Cache-Control"] = "public, max-age=300"
        else:
            response["Cache-Control"] = "no-cache, no-store, must-revalidate"

        return response


class CORSCustomMiddleware:
    """
    Handles CORS with custom configuration.
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        response = self.get_response(request)

        origin = request.META.get("HTTP_ORIGIN")
        if origin:
            allowed = settings.CORS_ALLOWED_ORIGINS
            if settings.DEBUG or origin in allowed:
                response["Access-Control-Allow-Origin"] = origin
                response["Access-Control-Allow-Methods"] = (
                    "GET, POST, PUT, PATCH, DELETE, OPTIONS"
                )
                response["Access-Control-Allow-Headers"] = (
                    "Authorization, Content-Type, X-CSRFToken"
                )
                response["Access-Control-Allow-Credentials"] = "true"

        return response
