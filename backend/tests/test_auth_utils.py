"""
test_auth_utils.py - Unit tests for the auth utility functions.

Tests the get_or_create_user_from_jwt() function from tradeiq.auth_utils,
which handles idempotent UserProfile creation from JWT claims.

Run with:
    python manage.py test tests.test_auth_utils
"""
import uuid
from unittest.mock import patch

from django.test import TestCase, override_settings

from behavior.models import UserProfile

from .conftest import TEST_JWT_SECRET


# ============================================================================
# Test get_or_create_user_from_jwt
# ============================================================================
@override_settings(SUPABASE_JWT_SECRET=TEST_JWT_SECRET)
class GetOrCreateUserFromJWTTests(TestCase):
    """
    Test the get_or_create_user_from_jwt utility function.
    
    This function is expected to:
    - Accept JWT claims dict (decoded payload)
    - Look up UserProfile by email
    - Create a new UserProfile if none exists
    - Update the name if it changed
    - Raise ValueError if email is missing
    """

    def setUp(self):
        """Create an existing user for reuse tests."""
        self.existing_user = UserProfile.objects.create(
            id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
            email="exists@example.com",
            name="Original Name",
        )

    def _import_get_or_create(self):
        """
        Import the function under test.
        Returns the function or raises ImportError if Teammate B
        has not yet created auth_utils.py.
        """
        from tradeiq.auth_utils import get_or_create_user_from_jwt
        return get_or_create_user_from_jwt

    # -- Happy path: new user ------------------------------------------------
    def test_get_or_create_new_user(self):
        """New email in claims should create a fresh UserProfile."""
        try:
            get_or_create = self._import_get_or_create()
        except ImportError:
            self.skipTest("tradeiq.auth_utils not yet created by Teammate B")

        claims = {
            "sub": "new-sub-uuid",
            "email": "newuser@example.com",
            "user_metadata": {"full_name": "New User", "email": "newuser@example.com"},
        }

        user = get_or_create(claims)

        self.assertIsInstance(user, UserProfile)
        self.assertEqual(user.email, "newuser@example.com")
        self.assertEqual(user.name, "New User")
        self.assertTrue(
            UserProfile.objects.filter(email="newuser@example.com").exists()
        )

    # -- Happy path: existing user -------------------------------------------
    def test_get_or_create_existing_user(self):
        """Existing email should return the same UserProfile without duplicating."""
        try:
            get_or_create = self._import_get_or_create()
        except ImportError:
            self.skipTest("tradeiq.auth_utils not yet created by Teammate B")

        claims = {
            "sub": "existing-sub",
            "email": "exists@example.com",
            "user_metadata": {"full_name": "Original Name", "email": "exists@example.com"},
        }

        user = get_or_create(claims)

        self.assertEqual(user.id, self.existing_user.id)
        self.assertEqual(
            UserProfile.objects.filter(email="exists@example.com").count(),
            1,
        )

    # -- Name update ---------------------------------------------------------
    def test_get_or_create_updates_name(self):
        """Changed name in claims should update UserProfile.name."""
        try:
            get_or_create = self._import_get_or_create()
        except ImportError:
            self.skipTest("tradeiq.auth_utils not yet created by Teammate B")

        claims = {
            "sub": "existing-sub",
            "email": "exists@example.com",
            "user_metadata": {"full_name": "Updated Name", "email": "exists@example.com"},
        }

        user = get_or_create(claims)

        self.existing_user.refresh_from_db()
        self.assertEqual(user.name, "Updated Name")
        self.assertEqual(self.existing_user.name, "Updated Name")

    # -- Missing email -------------------------------------------------------
    def test_get_or_create_missing_email(self):
        """Claims without email should raise ValueError."""
        try:
            get_or_create = self._import_get_or_create()
        except ImportError:
            self.skipTest("tradeiq.auth_utils not yet created by Teammate B")

        claims = {
            "sub": "no-email-sub",
            "user_metadata": {"full_name": "No Email User"},
        }

        with self.assertRaises(ValueError):
            get_or_create(claims)

    # -- Empty email ---------------------------------------------------------
    def test_get_or_create_empty_email(self):
        """Claims with empty string email should raise ValueError."""
        try:
            get_or_create = self._import_get_or_create()
        except ImportError:
            self.skipTest("tradeiq.auth_utils not yet created by Teammate B")

        claims = {
            "sub": "empty-email-sub",
            "email": "",
            "user_metadata": {"full_name": "Empty Email"},
        }

        with self.assertRaises(ValueError):
            get_or_create(claims)

    # -- Name extraction fallback --------------------------------------------
    def test_get_or_create_name_from_email(self):
        """
        If user_metadata.full_name is missing, function should handle
        gracefully (empty name or derive from email).
        """
        try:
            get_or_create = self._import_get_or_create()
        except ImportError:
            self.skipTest("tradeiq.auth_utils not yet created by Teammate B")

        claims = {
            "sub": "no-name-sub",
            "email": "noname@example.com",
            "user_metadata": {},
        }

        user = get_or_create(claims)
        self.assertEqual(user.email, "noname@example.com")
        # Name may be empty or derived - just ensure no crash
        self.assertIsInstance(user.name, str)

    # -- Idempotency under repeated calls ------------------------------------
    def test_get_or_create_idempotent(self):
        """Calling twice with same claims should not create duplicates."""
        try:
            get_or_create = self._import_get_or_create()
        except ImportError:
            self.skipTest("tradeiq.auth_utils not yet created by Teammate B")

        claims = {
            "sub": "idempotent-sub",
            "email": "idempotent@example.com",
            "user_metadata": {"full_name": "Idempotent User"},
        }

        user1 = get_or_create(claims)
        user2 = get_or_create(claims)

        self.assertEqual(user1.id, user2.id)
        self.assertEqual(
            UserProfile.objects.filter(email="idempotent@example.com").count(),
            1,
        )


# ============================================================================
# AUTH UTILS TEST MATRIX
# ============================================================================
#
# +----------------------------------+-------------------+--------+-----------------------------+
# | Scenario                         | Expected          | Status | Notes                       |
# +----------------------------------+-------------------+--------+-----------------------------+
# | New email -> create user         | UserProfile made  | TESTED | Happy path                  |
# | Existing email -> reuse          | Same UserProfile  | TESTED | No duplicate                |
# | Changed name -> update           | name updated      | TESTED | Idempotent update           |
# | Missing email -> error           | ValueError        | TESTED | Validation                  |
# | Empty email -> error             | ValueError        | TESTED | Edge case                   |
# | Missing full_name -> graceful    | No crash          | TESTED | Fallback handling           |
# | Repeated calls -> idempotent     | 1 user only       | TESTED | Concurrency safety          |
# +----------------------------------+-------------------+--------+-----------------------------+
#
# Total: 7 test cases
# Run:   python manage.py test tests.test_auth_utils
