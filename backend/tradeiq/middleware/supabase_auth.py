"""
Supabase JWT Authentication for Django REST Framework.

Verifies JWTs issued by Supabase (after Google Sign-In or any Supabase auth provider)
and maps them to local UserProfile instances.

Usage in settings.py:
    REST_FRAMEWORK = {
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "tradeiq.middleware.supabase_auth.SupabaseJWTAuthentication",
        ],
    }
"""

import logging

import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from behavior.models import UserProfile

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# SupabaseUser wrapper
# ---------------------------------------------------------------------------

class SupabaseUser:
    """
    Lightweight user wrapper returned by SupabaseJWTAuthentication.

    DRF expects ``request.user`` to be an object with ``is_authenticated``.
    This wrapper holds the local ``UserProfile`` plus the raw JWT claims
    so downstream views can access Supabase-specific data (role, provider, etc.).
    """

    def __init__(self, profile: UserProfile, claims: dict):
        self.profile = profile
        self.claims = claims
        self.id = profile.id
        self.email = profile.email
        self.pk = profile.pk

    # DRF checks
    is_authenticated = True
    is_active = True
    is_anonymous = False

    def __str__(self) -> str:
        return self.email


# ---------------------------------------------------------------------------
# DRF Authentication Class
# ---------------------------------------------------------------------------

class SupabaseJWTAuthentication(BaseAuthentication):
    """
    DRF authentication backend that validates Supabase-issued JWTs.

    Flow:
        1. Extract ``Authorization: Bearer <token>`` from the request.
        2. Decode & verify the JWT using the Supabase JWT secret (HS256).
        3. Check expiration, issuer, and required claims.
        4. Look up (or create) a ``UserProfile`` by email.
        5. Return ``(SupabaseUser, token_payload)`` as DRF expects.

    Environment variables (via settings):
        SUPABASE_JWT_SECRET  - The JWT secret from Supabase project settings.
        SUPABASE_URL         - e.g. https://<ref>.supabase.co (used as issuer).
    """

    keyword = "Bearer"

    # ------------------------------------------------------------------
    # Public API (called by DRF)
    # ------------------------------------------------------------------

    def authenticate(self, request):
        """
        Return a ``(user, auth)`` tuple if the request carries a valid
        Supabase JWT, or ``None`` if no Authorization header is present
        (allowing other authenticators or anonymous access).
        """
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header:
            return None  # No credentials -> let permission classes decide

        token = self._extract_token(auth_header)
        payload = self._decode_token(token)
        profile = self._get_or_create_profile(payload)

        return (SupabaseUser(profile, payload), payload)

    def authenticate_header(self, request):
        """
        Return a string for the ``WWW-Authenticate`` header on 401 responses.
        """
        return 'Bearer realm="tradeiq"'

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_token(self, auth_header: str) -> str:
        """Parse ``Authorization: Bearer <token>``."""
        parts = auth_header.split()

        if len(parts) == 0:
            raise AuthenticationFailed(
                detail="Authorization header is empty.",
                code="auth_header_empty",
            )

        if len(parts) == 1:
            raise AuthenticationFailed(
                detail="Authorization header must be: Bearer <token>.",
                code="auth_header_no_token",
            )

        if parts[0].lower() != "bearer":
            raise AuthenticationFailed(
                detail="Authorization header must start with 'Bearer'.",
                code="auth_header_invalid_prefix",
            )

        if len(parts) > 2:
            raise AuthenticationFailed(
                detail="Authorization header must not contain spaces in the token.",
                code="auth_header_spaces",
            )

        return parts[1]

    def _decode_token(self, token: str) -> dict:
        """Decode and verify the Supabase JWT."""
        secret = getattr(settings, "SUPABASE_JWT_SECRET", "")
        if not secret:
            logger.error("SUPABASE_JWT_SECRET is not configured.")
            raise AuthenticationFailed(
                detail="Server authentication is misconfigured.",
                code="auth_server_error",
            )

        # Build issuer URL for verification (optional but recommended).
        supabase_url = getattr(settings, "SUPABASE_URL", "")
        issuer = f"{supabase_url}/auth/v1" if supabase_url else None

        decode_options = {
            "verify_exp": True,
            "verify_signature": True,
            "require": ["sub", "exp", "iat"],
        }

        # If we don't have a SUPABASE_URL configured, skip issuer verification
        # to be more flexible during development.
        if not issuer:
            decode_options["verify_iss"] = False

        try:
            payload = jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                audience="authenticated",
                issuer=issuer if issuer else None,
                options=decode_options,
            )
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed(
                detail="Token has expired.",
                code="token_expired",
            )
        except jwt.InvalidIssuerError:
            raise AuthenticationFailed(
                detail="Token issuer is invalid.",
                code="token_invalid_issuer",
            )
        except jwt.InvalidSignatureError:
            raise AuthenticationFailed(
                detail="Token signature verification failed.",
                code="token_invalid_signature",
            )
        except jwt.DecodeError as exc:
            raise AuthenticationFailed(
                detail=f"Token is malformed: {exc}",
                code="token_malformed",
            )
        except jwt.InvalidTokenError as exc:
            raise AuthenticationFailed(
                detail=f"Token is invalid: {exc}",
                code="token_invalid",
            )

        # Ensure we have the claims we need.
        if "sub" not in payload:
            raise AuthenticationFailed(
                detail="Token is missing 'sub' claim.",
                code="token_missing_sub",
            )

        return payload

    def _get_or_create_profile(self, payload: dict) -> UserProfile:
        """
        Idempotent create-on-first-login: delegates to auth_utils for
        thread-safe user creation with name update support.
        """
        from tradeiq.auth_utils import get_or_create_user_from_jwt

        try:
            return get_or_create_user_from_jwt(payload)
        except ValueError as exc:
            raise AuthenticationFailed(
                detail=str(exc),
                code="token_missing_email",
            )
