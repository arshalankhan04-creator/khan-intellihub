"""
Auth views for registration, login, and token refresh.

Endpoints:
  POST /api/v1/auth/register/        → RegisterView
  POST /api/v1/auth/login/           → LoginView
  POST /api/v1/auth/token/refresh/   → CustomTokenRefreshView
"""

from django.db import IntegrityError
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer, LoginSerializer


class RegisterView(APIView):
    """
    POST /api/v1/auth/register/

    Creates a new user account and returns a JWT token pair.

    Responses:
      201 — account created, returns {access, refresh, user_id}
      400 — validation error (missing fields, bad email, short password)
      409 — email already registered
    """

    permission_classes = [AllowAny]
    # Exclude from default throttle so unauthenticated users can register
    throttle_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {'error': _first_error(serializer.errors), 'code': 'VALIDATION_ERROR'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check for duplicate email before hitting the DB (Req 1.2)
        from .models import CustomUser
        email = serializer.validated_data['email']
        if CustomUser.objects.filter(email=email).exists():
            return Response(
                {
                    'error': 'An account with this email already exists.',
                    'code': 'EMAIL_EXISTS',
                },
                status=status.HTTP_409_CONFLICT,
            )

        try:
            user = serializer.save()
        except IntegrityError:
            # Race condition: two requests with the same email at the same instant
            return Response(
                {
                    'error': 'An account with this email already exists.',
                    'code': 'EMAIL_EXISTS',
                },
                status=status.HTTP_409_CONFLICT,
            )

        tokens = RegisterSerializer.get_tokens(user)
        return Response(
            {
                'access': tokens['access'],
                'refresh': tokens['refresh'],
                'user_id': str(user.id),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """
    POST /api/v1/auth/login/

    Authenticates a user and returns a JWT token pair.

    Responses:
      200 — credentials valid, returns {access, refresh}
      400 — missing required fields
      401 — wrong credentials
    """

    permission_classes = [AllowAny]
    throttle_classes = []

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data,
            context={'request': request},
        )

        if not serializer.is_valid():
            errors = serializer.errors

            # Detect our INVALID_CREDENTIALS sentinel from LoginSerializer.validate()
            non_field = errors.get('non_field_errors', [])
            if any('INVALID_CREDENTIALS' in str(e) for e in non_field):
                return Response(
                    {
                        'error': 'Invalid email or password.',
                        'code': 'INVALID_CREDENTIALS',
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            return Response(
                {'error': _first_error(errors), 'code': 'VALIDATION_ERROR'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            status=status.HTTP_200_OK,
        )


class CustomTokenRefreshView(APIView):
    """
    POST /api/v1/auth/token/refresh/

    Exchanges a valid refresh token for a new access token.

    Responses:
      200 — {access: <new_access_token>}
      401 — refresh token invalid or expired
    """

    permission_classes = [AllowAny]
    throttle_classes = []

    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except (TokenError, InvalidToken):
            return Response(
                {
                    'error': 'Token is invalid or expired.',
                    'code': 'UNAUTHORIZED',
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except Exception:
            # simplejwt raises ValidationError (400) when the refresh field is
            # missing entirely — we normalise that to 401 as well, since a
            # missing token is still an authentication failure.
            return Response(
                {
                    'error': 'Token is invalid or expired.',
                    'code': 'UNAUTHORIZED',
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        return Response(
            {'access': serializer.validated_data['access']},
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _first_error(errors: dict) -> str:
    """Extract the first human-readable error message from a serializer errors dict."""
    for field, messages in errors.items():
        if isinstance(messages, list) and messages:
            return str(messages[0])
        if isinstance(messages, str):
            return messages
    return 'Invalid input.'
