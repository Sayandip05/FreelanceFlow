"""
Google OAuth2 Authentication Views

Flow:
  1. Frontend redirects user to GET /api/users/auth/google/?role=CLIENT|FREELANCER
     → This view builds the Google OAuth2 URL and returns it (or redirects).

  2. Google redirects back to GET /api/users/auth/google/callback/?code=...&state=...
     → Exchange code for Google token, fetch user profile, create/get User,
       issue JWT pair, redirect frontend to /auth/google/callback?access=...&refresh=...&role=...
"""
import logging
import requests

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import HttpResponseRedirect
from urllib.parse import urlencode

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()
logger = logging.getLogger(__name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


class OAuthRateThrottle(AnonRateThrottle):
    """Rate throttle for OAuth initialization and callback endpoints (10 requests per minute)."""
    rate = "10/minute"


def _get_google_credentials():
    client_id = getattr(settings, "GOOGLE_CLIENT_ID", "")
    client_secret = getattr(settings, "GOOGLE_CLIENT_SECRET", "")
    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
    redirect_uri = f"{getattr(settings, 'BACKEND_URL', 'http://localhost:8000')}/api/users/auth/google/callback/"
    return client_id, client_secret, redirect_uri, frontend_url


class GoogleOAuthInitView(APIView):
    """
    GET /api/users/auth/google/?role=CLIENT|FREELANCER&mode=login|register

    Returns:
        { "auth_url": "<Google OAuth URL>" }

    The frontend should redirect the user to this URL.
    The `role:mode` param is encoded in `state` and echoed back after the callback.
    """
    permission_classes = [AllowAny]
    throttle_classes = [OAuthRateThrottle]

    def get(self, request):
        client_id, _, redirect_uri, _ = _get_google_credentials()
        role = request.query_params.get("role", "CLIENT").upper()
        mode = request.query_params.get("mode", "login").lower()
        if role not in ("CLIENT", "FREELANCER"):
            role = "CLIENT"
        if mode not in ("login", "register"):
            mode = "login"

        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "state": f"{role}:{mode}",   # piggyback role and mode through OAuth state
            "prompt": "select_account",
        }
        auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
        return Response({"auth_url": auth_url})


class GoogleOAuthCallbackView(APIView):
    """
    GET /api/users/auth/google/callback/?code=...&state=ROLE:MODE

    Exchanges the Google auth code for tokens, fetches the user profile,
    checks if user exists (redirects to signup if trying to login without account),
    creates user on registration, issues a JWT pair, and redirects to frontend.
    """
    permission_classes = [AllowAny]
    throttle_classes = [OAuthRateThrottle]

    def get(self, request):
        client_id, client_secret, redirect_uri, frontend_url = _get_google_credentials()
        code = request.query_params.get("code")
        state_raw = request.query_params.get("state") or "CLIENT:login"
        if ":" in state_raw:
            role_part, mode_part = state_raw.split(":", 1)
            role = role_part.upper()
            mode = mode_part.lower()
        else:
            role = state_raw.upper()
            mode = "login"

        error = request.query_params.get("error")
        frontend_callback = f"{frontend_url}/auth/google/callback"

        if error or not code:
            return HttpResponseRedirect(f"{frontend_callback}?error=oauth_failed")

        # ── Step 1: Exchange code for Google tokens ──────────────────────────
        try:
            token_resp = requests.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
                timeout=10,
            )
            token_resp.raise_for_status()
            google_tokens = token_resp.json()
        except Exception as exc:
            logger.error("Google token exchange failed: %s", exc)
            return HttpResponseRedirect(f"{frontend_callback}?error=token_exchange_failed")

        # ── Step 2: Fetch user info from Google ──────────────────────────────
        access_token = google_tokens.get("access_token")
        try:
            user_info_resp = requests.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            )
            user_info_resp.raise_for_status()
            user_info = user_info_resp.json()
        except Exception as exc:
            logger.error("Google userinfo fetch failed: %s", exc)
            return HttpResponseRedirect(f"{frontend_callback}?error=userinfo_failed")

        email = user_info.get("email")
        if not email:
            return HttpResponseRedirect(f"{frontend_callback}?error=no_email")

        if role not in ("CLIENT", "FREELANCER"):
            role = "CLIENT"

        # ── Step 3: Check existence / Get or create local User ─────────────────
        user = User.objects.filter(email=email).first()

        # If user is trying to LOG IN, but no account exists in DB:
        if mode == "login" and not user:
            logger.info("Google OAuth login attempted for uncreated account: %s", email)
            err_params = urlencode({
                "error": "please_signup_first",
                "email": email,
                "role": role,
            })
            return HttpResponseRedirect(f"{frontend_callback}?{err_params}")

        # If user does not exist and mode is register, create user
        if not user:
            try:
                with transaction.atomic():
                    user = User.objects.create(
                        email=email,
                        first_name=user_info.get("given_name", ""),
                        last_name=user_info.get("family_name", ""),
                        role=role,
                        is_active=True,
                    )
                    user.set_unusable_password()
                    user.save(update_fields=["password"])
                    logger.info("New user registered via Google OAuth: %s (role=%s)", email, role)
            except Exception as exc:
                logger.error("User creation failed for %s: %s", email, exc)
                return HttpResponseRedirect(f"{frontend_callback}?error=user_creation_failed")
        else:
            logger.info("Existing user authenticated via Google OAuth: %s", email)

        # ── Step 4: Issue JWT tokens ──────────────────────────────────────────
        refresh = RefreshToken.for_user(user)
        access_jwt = str(refresh.access_token)
        refresh_jwt = str(refresh)

        # ── Step 5: Redirect to frontend with tokens ──────────────────────────
        params = urlencode({
            "access": access_jwt,
            "refresh": refresh_jwt,
            "role": user.role,
        })
        return HttpResponseRedirect(f"{frontend_callback}?{params}")
