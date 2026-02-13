"""
Safe API endpoint decorator for DRF views.
Catches common exceptions and returns clean JSON error responses.
"""
import functools
import logging
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def safe_api_endpoint(func):
    """
    Decorator for DRF view methods that catches exceptions
    and returns clean JSON error responses.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return Response(
                {"error": str(e), "type": "validation_error"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ConnectionError as e:
            logger.error("Connection error in %s: %s", func.__name__, e)
            return Response(
                {"error": "Service temporarily unavailable", "type": "connection_error"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except TimeoutError as e:
            logger.error("Timeout in %s: %s", func.__name__, e)
            return Response(
                {"error": "Request timed out", "type": "timeout_error"},
                status=status.HTTP_504_GATEWAY_TIMEOUT,
            )
        except Exception as e:
            logger.exception("Unexpected error in %s", func.__name__)
            return Response(
                {"error": "Internal server error", "type": "server_error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    return wrapper
