"""
Custom DRF exception handler.

- All error responses follow the shape: {"error": "...", "code": "..."}
- Unhandled exceptions return HTTP 500 without leaking stack traces (Req 11.3, 11.4)
"""

import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Called by DRF whenever an exception is raised inside a view.

    1. Let DRF handle known exceptions first (validation errors, auth errors, etc.)
    2. Normalise the response body to {"error": "...", "code": "..."}
    3. For completely unhandled exceptions, return a generic 500
    """

    # Step 1: let DRF do its default processing
    response = exception_handler(exc, context)

    if response is not None:
        # Step 2: normalise the body
        error_message = _extract_message(response.data)
        error_code = _status_to_code(response.status_code, response.data)

        response.data = {
            'error': error_message,
            'code': error_code,
        }
        return response

    # Step 3: unhandled exception — log it, return generic 500
    logger.exception('Unhandled exception in view: %s', exc)
    return Response(
        {'error': 'An unexpected error occurred.', 'code': 'INTERNAL_ERROR'},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _extract_message(data):
    """Pull a single human-readable string out of whatever DRF gives us."""
    if isinstance(data, dict):
        # DRF validation errors look like {"field": ["msg1", ...]} or {"detail": "msg"}
        if 'detail' in data:
            return str(data['detail'])
        # Grab the first error message from the first field
        for key, value in data.items():
            if isinstance(value, list) and value:
                return str(value[0])
            return str(value)
    if isinstance(data, list) and data:
        return str(data[0])
    return str(data)


def _status_to_code(http_status, data):
    """Map HTTP status → our internal error code string."""
    # If our view already set a 'code' key, preserve it
    if isinstance(data, dict) and 'code' in data:
        return data['code']

    mapping = {
        400: 'VALIDATION_ERROR',
        401: 'UNAUTHORIZED',
        403: 'FORBIDDEN',
        404: 'NOT_FOUND',
        405: 'METHOD_NOT_ALLOWED',
        409: 'EMAIL_EXISTS',
        413: 'FILE_TOO_LARGE',
        415: 'UNSUPPORTED_MEDIA_TYPE',
        422: 'PROCESSING_FAILED',
        429: 'RATE_LIMIT_EXCEEDED',
        500: 'INTERNAL_ERROR',
    }
    return mapping.get(http_status, 'ERROR')
