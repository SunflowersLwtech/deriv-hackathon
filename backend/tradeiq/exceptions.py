"""
Custom DRF exception handler for TradeIQ.

Standardizes 401 and 403 error responses to a consistent JSON format.
"""

from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.exceptions import (
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
)
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    if response is None:
        return None

    if isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
        error_code = "authentication_required"
        if isinstance(exc, AuthenticationFailed):
            error_code = getattr(exc, "default_code", None) or "authentication_failed"
            if hasattr(exc, "detail") and hasattr(exc.detail, "code"):
                error_code = exc.detail.code or error_code

        message = _extract_message(exc)
        response.data = {
            "error": error_code,
            "message": message,
            "status": response.status_code,
        }
        return response

    if isinstance(exc, PermissionDenied):
        message = _extract_message(exc)
        response.data = {
            "error": "permission_denied",
            "message": message,
            "status": response.status_code,
        }
        return response

    return response


def _extract_message(exc):
    detail = exc.detail
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list):
        return "; ".join(str(item) for item in detail)
    if isinstance(detail, dict):
        parts = []
        for key, value in detail.items():
            if isinstance(value, list):
                parts.append(str(key) + ": " + "; ".join(str(v) for v in value))
            else:
                parts.append(str(key) + ": " + str(value))
        return "; ".join(parts)
    return str(detail)
