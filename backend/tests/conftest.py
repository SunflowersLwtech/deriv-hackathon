"""
conftest.py - Shared test utilities, JWT helpers, and fixtures for TradeIQ auth tests.

This module provides helper functions for generating test JWTs, shared constants,
and reusable test fixtures used across all auth test modules.
"""
import jwt as pyjwt
from datetime import datetime, timedelta, timezone
from django.test import override_settings

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TEST_JWT_SECRET = "test-secret-key-for-testing-32chars!"
TEST_SUPABASE_URL = "https://test.supabase.co"

# Common override_settings decorator for auth tests
AUTH_SETTINGS = override_settings(
    SUPABASE_JWT_SECRET=TEST_JWT_SECRET,
    SUPABASE_URL=TEST_SUPABASE_URL,
    REST_FRAMEWORK={
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "tradeiq.middleware.supabase_auth.SupabaseJWTAuthentication",
        ],
        "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticatedOrReadOnly"],
        "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
        "PAGE_SIZE": 20,
        "EXCEPTION_HANDLER": "tradeiq.exceptions.custom_exception_handler",
    },
)


# ---------------------------------------------------------------------------
# JWT Helper
# ---------------------------------------------------------------------------
def make_jwt(
    email="test@example.com",
    sub="00000000-0000-0000-0000-000000000001",
    exp_delta=timedelta(hours=1),
    secret=TEST_JWT_SECRET,
    name="Test User",
    **extra_claims,
):
    """
    Generate an HS256 JWT token suitable for Supabase auth testing.

    Args:
        email:     User email claim.
        sub:       Subject (Supabase user UUID).
        exp_delta: Time until expiry (negative = already expired).
        secret:    HMAC secret for signing.
        name:      Full name stored in user_metadata.
        **extra_claims: Additional top-level claims to merge.

    Returns:
        Encoded JWT string.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "email": email,
        "exp": now + exp_delta,
        "iat": now,
        "iss": f"{TEST_SUPABASE_URL}/auth/v1",
        "aud": "authenticated",
        "role": "authenticated",
        "user_metadata": {"full_name": name, "email": email},
    }
    payload.update(extra_claims)
    return pyjwt.encode(payload, secret, algorithm="HS256")


def auth_header(token):
    """Return an HTTP_AUTHORIZATION header dict for DRF's APIClient."""
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}
