"""
Custom DRF permissions for TradeIQ.

These permissions work with SupabaseJWTAuthentication and produce
standardized JSON error responses (handled by the custom exception
handler in tradeiq.exceptions).
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthenticated(BasePermission):
    """
    Allows access only to authenticated Supabase users.

    Returns a 401 with a structured JSON payload when the user is not
    authenticated (handled by the custom exception handler).
    """

    message = "Authentication is required to access this resource."

    def has_permission(self, request, view):
        return bool(
            request.user
            and getattr(request.user, "is_authenticated", False)
        )


class IsAuthenticatedOrReadOnly(BasePermission):
    """
    Allows unauthenticated users to perform safe (read-only) requests
    (GET, HEAD, OPTIONS) but requires authentication for writes.
    """

    message = "Authentication is required for write operations."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(
            request.user
            and getattr(request.user, "is_authenticated", False)
        )


class IsOwnerOrReadOnly(BasePermission):
    """
    Object-level permission: only the owner of a resource may mutate it.

    Expects the object to have a ``user`` FK or ``email`` field that can be
    matched against the authenticated SupabaseUser.
    """

    message = "You do not have permission to modify this resource."

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        # Compare against the profile attached to SupabaseUser.
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False

        # Try matching by user FK first, then by email.
        if hasattr(obj, "user_id"):
            return str(obj.user_id) == str(user.id)
        if hasattr(obj, "email"):
            return obj.email == user.email
        return False
