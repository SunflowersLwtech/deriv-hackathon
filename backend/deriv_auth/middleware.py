"""Utility functions for retrieving the active Deriv token for the current user.

NOT Django middleware - these are helper functions used by other apps
to get the appropriate Deriv API token for requests.
"""

import os

from .models import DerivAccount


def get_deriv_token(request) -> str:
    """Get the active Deriv token for the current user.

    Returns user's default Deriv account token, or falls back to env DERIV_TOKEN.
    """
    if hasattr(request, "_deriv_token_cache"):
        return request._deriv_token_cache

    token = os.environ.get("DERIV_TOKEN", "")  # default fallback

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
            except Exception:
                pass

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
