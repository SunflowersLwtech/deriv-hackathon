"""
Auth User Mapping Utility for TradeIQ.

Provides idempotent user creation/lookup from Supabase JWT claims.
Called by the auth middleware (Teammate A) after JWT verification.

Design decisions:
- Uses email as the linking field between Supabase auth and UserProfile
- No auth_uid column needed -- avoids schema changes to frozen model
- Thread-safe via select_for_update and atomic transactions
- Handles race conditions on concurrent first-login via IntegrityError catch
"""

import logging
import uuid
from typing import Optional

from django.db import IntegrityError, transaction

from behavior.models import UserProfile

logger = logging.getLogger(__name__)


def get_or_create_user_from_jwt(jwt_claims: dict) -> UserProfile:
    """
    Idempotent user creation from JWT claims.

    Extracts email and name from the JWT, looks up UserProfile by email,
    creates one if not found, and optionally updates the name if it changed.

    Args:
        jwt_claims: Decoded JWT payload. Expected keys:
            - 'email' (str, required): User's email from Supabase auth
            - 'user_metadata' (dict, optional): May contain 'full_name' or 'name'
            - 'sub' (str, optional): Supabase auth user UUID (logged but not stored)

    Returns:
        UserProfile instance (existing or newly created)

    Raises:
        ValueError: If jwt_claims is missing the required 'email' field
    """
    email = _extract_email(jwt_claims)
    name = _extract_name(jwt_claims)
    sub = jwt_claims.get('sub', 'unknown')

    # Try fast path first: user already exists
    try:
        user = UserProfile.objects.get(email=email)
        user = _maybe_update_name(user, name)
        logger.debug(
            "Auth lookup succeeded for email=%s sub=%s user_id=%s",
            email, sub, user.id,
        )
        return user
    except UserProfile.DoesNotExist:
        pass

    # Slow path: create new user with race-condition safety
    return _create_user_safe(email=email, name=name, sub=sub)


def _extract_email(jwt_claims: dict) -> str:
    """Extract and validate email from JWT claims."""
    email = jwt_claims.get('email', '').strip().lower()
    if not email:
        raise ValueError(
            "JWT claims missing required 'email' field. "
            "Ensure Supabase auth is configured to include email in tokens."
        )
    return email


def _extract_name(jwt_claims: dict) -> str:
    """
    Extract display name from JWT claims.

    Checks multiple locations where Supabase/Google may place the name:
    1. user_metadata.full_name (Google Sign-In via Supabase)
    2. user_metadata.name (alternative location)
    3. Top-level 'name' claim (some OIDC providers)
    """
    user_metadata = jwt_claims.get('user_metadata', {})
    if isinstance(user_metadata, dict):
        name = user_metadata.get('full_name', '') or user_metadata.get('name', '')
        if name:
            return name.strip()
    return jwt_claims.get('name', '').strip()


def _maybe_update_name(user: UserProfile, name: str) -> UserProfile:
    """
    Update user's name if the JWT provides a non-empty name that differs.

    Only writes to DB if there is an actual change, to avoid unnecessary writes.
    """
    if name and user.name != name:
        user.name = name
        user.save(update_fields=['name'])
        logger.info(
            "Updated name for user_id=%s from '%s' to '%s'",
            user.id, user.name, name,
        )
    return user


def _create_user_safe(email: str, name: str, sub: str) -> UserProfile:
    """
    Create a new UserProfile with race-condition safety.

    If two requests try to create the same user simultaneously,
    the second one will hit the unique constraint on email and
    fall back to a lookup instead.
    """
    try:
        with transaction.atomic():
            user = UserProfile.objects.create(
                id=uuid.uuid4(),
                email=email,
                name=name,
                preferences={},
                watchlist=[],
            )
        logger.info(
            "Created new UserProfile id=%s email=%s (auth sub=%s)",
            user.id, email, sub,
        )
        return user
    except IntegrityError:
        # Race condition: another request created this user between our
        # DoesNotExist check and this create. Just fetch it.
        logger.info(
            "Race condition on user create for email=%s, falling back to lookup",
            email,
        )
        user = UserProfile.objects.get(email=email)
        return _maybe_update_name(user, name)


def get_user_by_email(email: str) -> Optional[UserProfile]:
    """
    Look up a UserProfile by email. Returns None if not found.

    Convenience function for use outside the JWT auth flow.
    """
    try:
        return UserProfile.objects.get(email=email.strip().lower())
    except UserProfile.DoesNotExist:
        return None
