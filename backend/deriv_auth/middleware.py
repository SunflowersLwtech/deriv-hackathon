"""Utility functions for retrieving the active Deriv token for the current user.

NOT Django middleware - these are helper functions used by other apps
to get the appropriate Deriv API token for requests.
"""

import os
import logging

from .models import DerivAccount

logger = logging.getLogger(__name__)


def get_deriv_token(request) -> str:
    """Get the active Deriv token for the current user.

    Priority: user's default account token > env DERIV_TOKEN fallback.
    """
    if hasattr(request, "_deriv_token_cache"):
        return request._deriv_token_cache

    token = ""

    # 1. Try authenticated user's linked Deriv account first
    user = getattr(request, "user", None)
    if user and getattr(user, "is_authenticated", False):
        user_id = getattr(user, "id", None)
        if user_id:
            try:
                account = DerivAccount.objects.filter(
                    user_id=user_id,
                    is_active=True,
                    is_default=True,
                ).first()
                if account:
                    token = account.token
            except Exception as e:
                logger.warning("Failed to lookup Deriv account for user %s: %s", user_id, e)

    # 2. Fall back to env only when no user account token found
    if not token:
        token = os.environ.get("DERIV_TOKEN", "")

    request._deriv_token_cache = token
    return token


def has_real_deriv_account(request) -> bool:
    """Check if current user has a real (non-demo) Deriv account linked."""
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return False
    user_id = getattr(user, "id", None)
    if not user_id:
        return False
    return DerivAccount.objects.filter(
        user_id=user_id,
        is_active=True,
        account_type="real",
    ).exists()
