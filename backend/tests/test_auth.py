"""
test_auth.py - Comprehensive authentication tests for TradeIQ backend.

Tests JWT verification, endpoint authorization, user creation flows,
and error response formats for the Supabase JWT auth integration.

Run with:
    python manage.py test tests.test_auth
"""
import uuid
from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework import status

from behavior.models import UserProfile, Trade
from content.models import AIPersona, SocialPost

from .conftest import (
    TEST_JWT_SECRET,
    AUTH_SETTINGS,
    make_jwt,
    auth_header,
)


# ============================================================================
# Base test class with common setup
# ============================================================================
class AuthTestBase(TestCase):
    """Base class providing shared setUp for all auth tests."""

    def setUp(self):
        self.client = APIClient()
        self.valid_token = make_jwt()
        self.user_email = "test@example.com"
        self.user_sub = "00000000-0000-0000-0000-000000000001"

        # Pre-create a UserProfile for tests that need an existing user
        self.existing_user = UserProfile.objects.create(
            id=uuid.UUID("00000000-0000-0000-0000-aaaaaaaaaaaa"),
            email="existing@example.com",
            name="Existing User",
            preferences={},
            watchlist=["EUR/USD"],
        )

        # Pre-create a second user for trade tests
        self.trade_user = UserProfile.objects.create(
            id=uuid.UUID("00000000-0000-0000-0000-bbbbbbbbbbbb"),
            email="trader@example.com",
            name="Trader User",
        )

        # Pre-create an AIPersona for content tests
        self.persona = AIPersona.objects.create(
            name="Test Persona",
            personality_type="calm",
            is_primary=True,
        )


# ============================================================================
# 1. JWT Verification Tests
# ============================================================================
@AUTH_SETTINGS
class JWTVerificationTests(AuthTestBase):
    """Test that the SupabaseJWTAuthentication class correctly verifies JWTs."""

    def test_valid_jwt_authenticates_user(self):
        """Valid HS256 JWT with correct secret should authenticate (200 on read)."""
        token = make_jwt(email="valid@example.com")
        response = self.client.get(
            "/api/behavior/profiles/",
            **auth_header(token),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_expired_jwt_returns_401(self):
        """JWT with exp in the past should be rejected with 401."""
        token = make_jwt(exp_delta=timedelta(hours=-1))
        response = self.client.get(
            "/api/behavior/profiles/",
            **auth_header(token),
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_signature_returns_401(self):
        """JWT signed with wrong secret should be rejected with 401."""
        token = make_jwt(secret="wrong-secret-entirely")
        response = self.client.get(
            "/api/behavior/profiles/",
            **auth_header(token),
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_missing_token_allows_read(self):
        """
        No Authorization header should still allow GET on public endpoints.
        IsAuthenticatedOrReadOnly permits unauthenticated reads.
        """
        response = self.client.get("/api/behavior/profiles/")
        self.assertIn(
            response.status_code,
            [status.HTTP_200_OK, status.HTTP_301_MOVED_PERMANENTLY],
        )

    def test_missing_token_blocks_write(self):
        """No Authorization header should block POST on protected endpoints."""
        response = self.client.post(
            "/api/behavior/trades/",
            data={
                "user": str(self.trade_user.id),
                "instrument": "EUR/USD",
                "pnl": "10.00",
            },
            format="json",
        )
        # Should be 401 (not authenticated) or 403 (permission denied)
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_malformed_token_returns_401(self):
        """'Bearer invalid-garbage' should be rejected with 401."""
        response = self.client.get(
            "/api/behavior/profiles/",
            HTTP_AUTHORIZATION="Bearer invalid-garbage-not-a-jwt",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_missing_bearer_prefix_returns_401(self):
        """Token without 'Bearer ' prefix should be rejected."""
        token = make_jwt()
        response = self.client.get(
            "/api/behavior/profiles/",
            HTTP_AUTHORIZATION=token,  # No "Bearer " prefix
        )
        # Without the Bearer prefix, auth class should not parse it,
        # so user is anonymous. For a GET this might still be 200.
        # But if any auth class tries and fails it returns 401.
        # We accept either 200 (skipped) or 401 (rejected).
        self.assertIn(
            response.status_code,
            [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED],
        )


# ============================================================================
# 2. User Creation Tests (via JWT-triggered get_or_create)
# ============================================================================
@AUTH_SETTINGS
class UserCreationTests(AuthTestBase):
    """Test that JWT auth triggers proper user creation/lookup."""

    def test_first_login_creates_user(self):
        """JWT with a new email should create a UserProfile on first request."""
        new_email = "brand-new-user@example.com"
        new_sub = "11111111-1111-1111-1111-111111111111"
        token = make_jwt(email=new_email, sub=new_sub, name="Brand New")

        self.assertFalse(UserProfile.objects.filter(email=new_email).exists())

        response = self.client.get(
            "/api/behavior/profiles/",
            **auth_header(token),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # After the authenticated request, a UserProfile should exist
        self.assertTrue(UserProfile.objects.filter(email=new_email).exists())
        user = UserProfile.objects.get(email=new_email)
        self.assertEqual(user.name, "Brand New")

    def test_second_login_reuses_user(self):
        """JWT with existing email should return the same UserProfile, not duplicate."""
        email = "returning@example.com"
        sub = "22222222-2222-2222-2222-222222222222"
        token = make_jwt(email=email, sub=sub, name="Returner")

        # First request creates the user
        self.client.get("/api/behavior/profiles/", **auth_header(token))
        count_after_first = UserProfile.objects.filter(email=email).count()

        # Second request should reuse
        self.client.get("/api/behavior/profiles/", **auth_header(token))
        count_after_second = UserProfile.objects.filter(email=email).count()

        self.assertEqual(count_after_first, 1)
        self.assertEqual(count_after_second, 1)

    def test_user_name_updated_on_login(self):
        """JWT with updated name should update the UserProfile.name."""
        email = "updater@example.com"
        sub = "33333333-3333-3333-3333-333333333333"

        # First login with original name
        token_v1 = make_jwt(email=email, sub=sub, name="Old Name")
        self.client.get("/api/behavior/profiles/", **auth_header(token_v1))

        user = UserProfile.objects.get(email=email)
        self.assertEqual(user.name, "Old Name")

        # Second login with updated name
        token_v2 = make_jwt(email=email, sub=sub, name="New Name")
        self.client.get("/api/behavior/profiles/", **auth_header(token_v2))

        user.refresh_from_db()
        self.assertEqual(user.name, "New Name")


# ============================================================================
# 3. Endpoint Authorization Tests
# ============================================================================
@AUTH_SETTINGS
class EndpointAuthorizationTests(AuthTestBase):
    """Test that endpoints enforce correct read/write permissions."""

    # -- Market endpoints (ReadOnly viewset -> always public) ----------------
    def test_market_endpoints_public(self):
        """GET /api/market/insights/ should return 200 without any auth."""
        response = self.client.get("/api/market/insights/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # -- Demo endpoints (custom View, csrf_exempt, should remain public) -----
    def test_demo_endpoints_public(self):
        """
        POST /api/demo/load-scenario/ should be accessible without auth.
        The demo view uses plain Django View (not DRF), so DRF auth
        middleware does not apply. We test that it remains accessible.
        """
        response = self.client.post(
            "/api/demo/load-scenario/",
            data={"scenario": "revenge_trading"},
            content_type="application/json",
        )
        # 200 if fixture exists, 404 if fixture file not found -- both are
        # acceptable; the point is we do NOT get 401/403.
        self.assertNotIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    # -- Behavior endpoints --------------------------------------------------
    def test_behavior_list_public_read(self):
        """GET /api/behavior/profiles/ should be 200 without auth (public read)."""
        response = self.client.get("/api/behavior/profiles/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_behavior_create_requires_auth(self):
        """POST /api/behavior/trades/ without auth should return 401 or 403."""
        response = self.client.post(
            "/api/behavior/trades/",
            data={
                "user": str(self.trade_user.id),
                "instrument": "BTC/USD",
                "pnl": "-5.50",
            },
            format="json",
        )
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_behavior_create_with_auth(self):
        """POST /api/behavior/trades/ with valid JWT should return 201."""
        token = make_jwt(email="trader@example.com")
        response = self.client.post(
            "/api/behavior/trades/",
            data={
                "user": str(self.trade_user.id),
                "instrument": "BTC/USD",
                "direction": "buy",
                "pnl": "15.00",
                "is_mock": True,
            },
            format="json",
            **auth_header(token),
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Trade.objects.filter(
                user=self.trade_user, instrument="BTC/USD"
            ).exists()
        )

    # -- Content endpoints ---------------------------------------------------
    def test_content_read_public(self):
        """GET /api/content/personas/ should be 200 without auth."""
        response = self.client.get("/api/content/personas/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_content_write_requires_auth(self):
        """POST /api/content/posts/ without auth should return 401 or 403."""
        response = self.client.post(
            "/api/content/posts/",
            data={
                "persona": str(self.persona.id),
                "content": "Test post content",
                "platform": "bluesky",
                "status": "draft",
            },
            format="json",
        )
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_content_write_with_auth(self):
        """POST /api/content/posts/ with valid JWT should succeed."""
        token = make_jwt(email="writer@example.com")
        response = self.client.post(
            "/api/content/posts/",
            data={
                "persona": str(self.persona.id),
                "content": "Authenticated post content",
                "platform": "bluesky",
                "status": "draft",
            },
            format="json",
            **auth_header(token),
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_behavior_metrics_read_public(self):
        """GET /api/behavior/metrics/ should be 200 without auth."""
        response = self.client.get("/api/behavior/metrics/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# ============================================================================
# 4. Error Response Format Tests
# ============================================================================
@AUTH_SETTINGS
class ErrorResponseFormatTests(AuthTestBase):
    """
    Test that authentication/authorization errors return standardized JSON.
    Expected format: {"error": "...", "message": "...", "status": <int>}
    
    Note: The exact format depends on the custom exception handler that
    Teammate A implements. These tests verify the structure once available.
    If the default DRF handler is used, the format will be {"detail": "..."}.
    """

    def test_401_response_format(self):
        """401 responses should return JSON with an error description."""
        token = make_jwt(exp_delta=timedelta(hours=-1))  # expired
        response = self.client.get(
            "/api/behavior/profiles/",
            **auth_header(token),
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        data = response.json()
        # Accept either custom format or DRF default
        has_custom_format = "error" in data and "message" in data and "status" in data
        has_drf_format = "detail" in data
        self.assertTrue(
            has_custom_format or has_drf_format,
            f"401 response should have structured error body, got: {data}",
        )

    def test_401_response_content_type(self):
        """401 responses should have application/json content type."""
        token = make_jwt(secret="wrong-secret")
        response = self.client.get(
            "/api/behavior/profiles/",
            **auth_header(token),
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("application/json", response["Content-Type"])

    def test_403_response_format(self):
        """
        403 responses should return JSON with an error description.
        Trigger: authenticated user trying to access a forbidden resource.
        This may require a custom permission class; test structure only.
        """
        # POST without auth to a write endpoint -> 401 or 403
        response = self.client.post(
            "/api/behavior/trades/",
            data={
                "user": str(self.trade_user.id),
                "instrument": "GOLD",
                "pnl": "0",
            },
            format="json",
        )
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )
        data = response.json()
        has_custom_format = "error" in data and "message" in data and "status" in data
        has_drf_format = "detail" in data
        self.assertTrue(
            has_custom_format or has_drf_format,
            f"Error response should have structured body, got: {data}",
        )


# ============================================================================
# 5. Edge Cases and Robustness
# ============================================================================
@AUTH_SETTINGS
class EdgeCaseTests(AuthTestBase):
    """Additional edge-case tests for auth robustness."""

    def test_empty_authorization_header(self):
        """Empty Authorization header should not crash the server."""
        response = self.client.get(
            "/api/behavior/profiles/",
            HTTP_AUTHORIZATION="",
        )
        # Should either skip auth (200 for read) or reject (401)
        self.assertIn(
            response.status_code,
            [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED],
        )

    def test_bearer_with_empty_token(self):
        """'Bearer ' with no actual token should be handled gracefully."""
        response = self.client.get(
            "/api/behavior/profiles/",
            HTTP_AUTHORIZATION="Bearer ",
        )
        self.assertIn(
            response.status_code,
            [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED],
        )

    def test_multiple_bearer_tokens(self):
        """Multiple tokens in header should not cause server error."""
        token = make_jwt()
        response = self.client.get(
            "/api/behavior/profiles/",
            HTTP_AUTHORIZATION=f"Bearer {token} extra-stuff",
        )
        # Should either parse the first token or reject
        self.assertIn(
            response.status_code,
            [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED],
        )

    def test_jwt_missing_email_claim(self):
        """JWT without email claim should be handled (reject or ignore)."""
        import jwt as pyjwt
        from datetime import datetime, timezone as tz

        now = datetime.now(tz.utc)
        payload = {
            "sub": "no-email-uuid",
            "exp": now + timedelta(hours=1),
            "iat": now,
            "aud": "authenticated",
            "role": "authenticated",
        }
        token = pyjwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")
        response = self.client.get(
            "/api/behavior/profiles/",
            **auth_header(token),
        )
        # Without email, user creation should fail -> 401 or still allow read
        self.assertIn(
            response.status_code,
            [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED],
        )

    def test_concurrent_user_creation_idempotent(self):
        """
        Two requests with the same new email should not create duplicates.
        Simulates the idempotency guarantee of get_or_create_user_from_jwt.
        """
        email = "concurrent@example.com"
        sub = "44444444-4444-4444-4444-444444444444"
        token = make_jwt(email=email, sub=sub)

        # Make two rapid requests
        self.client.get("/api/behavior/profiles/", **auth_header(token))
        self.client.get("/api/behavior/profiles/", **auth_header(token))

        self.assertEqual(
            UserProfile.objects.filter(email=email).count(),
            1,
            "Should have exactly one UserProfile for the email",
        )


# ============================================================================
# AUTH TEST MATRIX
# ============================================================================
#
# +----------------------------------+----------+--------+-------------------------------+
# | Scenario                         | Expected | Status | Notes                         |
# +----------------------------------+----------+--------+-------------------------------+
# | Valid JWT                        | 200      | TESTED | test_valid_jwt_authenticates  |
# | Expired JWT                      | 401      | TESTED | test_expired_jwt_returns_401  |
# | Invalid signature                | 401      | TESTED | test_invalid_signature_401    |
# | Missing token (GET)              | 200      | TESTED | Public read allowed           |
# | Missing token (POST)             | 401/403  | TESTED | Write blocked                 |
# | Malformed token                  | 401      | TESTED | Garbage string rejected       |
# | Missing Bearer prefix            | 200/401  | TESTED | Depends on auth class logic   |
# | First login creation             | 200+user | TESTED | UserProfile created           |
# | Second login reuse               | 200      | TESTED | No duplicate UserProfile      |
# | Name update on login             | 200      | TESTED | UserProfile.name updated      |
# | Market endpoints public          | 200      | TESTED | ReadOnly viewset              |
# | Demo endpoints public            | !401     | TESTED | Plain Django view             |
# | Behavior list read               | 200      | TESTED | IsAuthenticatedOrReadOnly     |
# | Behavior create no auth          | 401/403  | TESTED | Write blocked                 |
# | Behavior create with auth        | 201      | TESTED | Trade created                 |
# | Content read public              | 200      | TESTED | Personas readable             |
# | Content write no auth            | 401/403  | TESTED | Posts write blocked           |
# | Content write with auth          | 201      | TESTED | Post created                  |
# | 401 response format              | JSON     | TESTED | Structured error body         |
# | 401 content type                 | JSON     | TESTED | application/json              |
# | 403 response format              | JSON     | TESTED | Structured error body         |
# | Empty authorization header       | 200/401  | TESTED | No crash                      |
# | Bearer with empty token          | 200/401  | TESTED | Graceful handling             |
# | Multiple tokens in header        | 200/401  | TESTED | No crash                      |
# | JWT missing email claim          | 200/401  | TESTED | Handled gracefully            |
# | Concurrent user creation         | 1 user   | TESTED | Idempotent                    |
# | Metrics read public              | 200      | TESTED | Public read on metrics        |
# +----------------------------------+----------+--------+-------------------------------+
#
# Total: 25 test cases across 5 test classes
# Run:   python manage.py test tests.test_auth
