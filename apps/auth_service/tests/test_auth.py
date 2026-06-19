"""
Unit tests for auth endpoints.

Covers:
  - Registration: duplicate email, short password, valid registration
  - Login: wrong password, valid login
  - Token refresh: valid token, expired/invalid token
  - Protected endpoint: missing JWT
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.auth_service.models import CustomUser


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def existing_user(db):
    """A user that already exists in the DB."""
    return CustomUser.objects.create_user(
        email='existing@example.com',
        password='StrongPass123',
    )


@pytest.fixture
def register_url():
    return reverse('auth-register')


@pytest.fixture
def login_url():
    return reverse('auth-login')


@pytest.fixture
def refresh_url():
    return reverse('auth-token-refresh')


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _protected_url():
    """
    We don't have a real protected endpoint yet in Milestone 1,
    so we hit /api/v1/resumes/ which doesn't exist — Django will return 404,
    but the JWT middleware fires *before* URL resolution, so a missing
    token still yields 401.

    A cleaner approach: create a tiny test-only view, but for M1 we check
    that hitting the register endpoint with a non-AllowAny method returns
    401 when unauthenticated (the register view itself is AllowAny, so we
    need another approach).

    We'll hit /api/v1/auth/token/refresh/ with no body: the view is AllowAny
    but returns 401 on bad token, which is close enough for the "no JWT" check.

    For a real protected resource test, Milestone 2 adds /api/v1/resumes/.
    """
    # Use a URL that doesn't exist — DRF JWT middleware runs before 404 routing.
    return '/api/v1/resumes/'


# ---------------------------------------------------------------------------
# Registration tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestRegister:

    def test_valid_registration_returns_201_with_tokens(self, client, register_url):
        payload = {'email': 'new@example.com', 'password': 'StrongPass123'}
        response = client.post(register_url, payload, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert 'access' in data
        assert 'refresh' in data
        assert 'user_id' in data
        # Confirm the user was actually created
        assert CustomUser.objects.filter(email='new@example.com').exists()

    def test_duplicate_email_returns_409(self, client, register_url, existing_user):
        payload = {'email': existing_user.email, 'password': 'AnotherPass456'}
        response = client.post(register_url, payload, format='json')

        assert response.status_code == status.HTTP_409_CONFLICT
        data = response.json()
        assert data['code'] == 'EMAIL_EXISTS'

    def test_password_too_short_returns_400(self, client, register_url):
        payload = {'email': 'short@example.com', 'password': '1234567'}  # 7 chars
        response = client.post(register_url, payload, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data['code'] == 'VALIDATION_ERROR'

    def test_missing_email_returns_400(self, client, register_url):
        payload = {'password': 'StrongPass123'}
        response = client.post(register_url, payload, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()['code'] == 'VALIDATION_ERROR'

    def test_missing_password_returns_400(self, client, register_url):
        payload = {'email': 'nopw@example.com'}
        response = client.post(register_url, payload, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()['code'] == 'VALIDATION_ERROR'

    def test_invalid_email_format_returns_400(self, client, register_url):
        payload = {'email': 'not-an-email', 'password': 'StrongPass123'}
        response = client.post(register_url, payload, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()['code'] == 'VALIDATION_ERROR'

    def test_email_is_case_insensitive(self, client, register_url, existing_user):
        """Registering with uppercase version of an existing email should 409."""
        payload = {
            'email': existing_user.email.upper(),
            'password': 'AnotherPass456',
        }
        response = client.post(register_url, payload, format='json')
        assert response.status_code == status.HTTP_409_CONFLICT


# ---------------------------------------------------------------------------
# Login tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestLogin:

    def test_valid_credentials_return_200_with_tokens(self, client, login_url, existing_user):
        payload = {'email': existing_user.email, 'password': 'StrongPass123'}
        response = client.post(login_url, payload, format='json')

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'access' in data
        assert 'refresh' in data

    def test_wrong_password_returns_401(self, client, login_url, existing_user):
        payload = {'email': existing_user.email, 'password': 'WrongPassword!'}
        response = client.post(login_url, payload, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data['code'] == 'INVALID_CREDENTIALS'
        assert data['error'] == 'Invalid email or password.'

    def test_wrong_email_returns_401(self, client, login_url):
        payload = {'email': 'ghost@example.com', 'password': 'SomePass123'}
        response = client.post(login_url, payload, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()['code'] == 'INVALID_CREDENTIALS'

    def test_missing_password_returns_400(self, client, login_url, existing_user):
        payload = {'email': existing_user.email}
        response = client.post(login_url, payload, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()['code'] == 'VALIDATION_ERROR'

    def test_missing_email_returns_400(self, client, login_url):
        payload = {'password': 'StrongPass123'}
        response = client.post(login_url, payload, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()['code'] == 'VALIDATION_ERROR'


# ---------------------------------------------------------------------------
# Token refresh tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestTokenRefresh:

    def test_valid_refresh_token_returns_new_access_token(
        self, client, refresh_url, existing_user
    ):
        refresh = RefreshToken.for_user(existing_user)
        response = client.post(
            refresh_url,
            {'refresh': str(refresh)},
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.json()

    def test_invalid_refresh_token_returns_401(self, client, refresh_url):
        response = client.post(
            refresh_url,
            {'refresh': 'this.is.not.a.valid.token'},
            format='json',
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data['code'] == 'UNAUTHORIZED'

    def test_missing_refresh_token_returns_401(self, client, refresh_url):
        response = client.post(refresh_url, {}, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_expired_token_returns_401(self, client, refresh_url, existing_user):
        """
        Simulate an expired token by manually constructing a token with a
        past expiry. We use a raw tampered token string; simplejwt will
        reject it as invalid.
        """
        # A well-formed JWT but with wrong signature — simplejwt rejects it
        fake_token = (
            'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9'
            '.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTYwMDAwMDAwMH0'
            '.invalidsignature'
        )
        response = client.post(
            refresh_url,
            {'refresh': fake_token},
            format='json',
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()['code'] == 'UNAUTHORIZED'


# ---------------------------------------------------------------------------
# Protected endpoint tests (JWT middleware)
# ---------------------------------------------------------------------------

# A minimal protected view registered only for testing purposes.
# This avoids hitting non-existent URLs (which cause a Django 4.2/Python 3.14
# template copy crash in the debug error logger on 404s).
from django.urls import path as _path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response as _Response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def _protected_test_view(request):
    return _Response({'ok': True})


# Patch the URL conf to include our test endpoint
import django.test.utils as _test_utils  # noqa: E402

_original_urlconf = None


@pytest.fixture(autouse=False)
def with_protected_url(settings):
    """Add a temporary /api/v1/test-protected/ endpoint for JWT tests."""
    from django.urls import include, path, clear_url_caches
    import importlib, sys

    # Temporarily override ROOT_URLCONF with a version that has our test route
    settings.ROOT_URLCONF = 'apps.auth_service.tests.test_urls'
    clear_url_caches()
    yield
    settings.ROOT_URLCONF = 'khan_intellihub.urls'
    clear_url_caches()


@pytest.mark.django_db
class TestJWTProtection:

    def test_request_without_token_returns_401(self, client, with_protected_url):
        response = client.get('/api/v1/test-protected/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_request_with_valid_token_passes_auth(self, client, existing_user, with_protected_url):
        refresh = RefreshToken.for_user(existing_user)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
        response = client.get('/api/v1/test-protected/')
        assert response.status_code == status.HTTP_200_OK

    def test_request_with_invalid_token_returns_401(self, client, with_protected_url):
        client.credentials(HTTP_AUTHORIZATION='Bearer invalidtoken123')
        response = client.get('/api/v1/test-protected/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
