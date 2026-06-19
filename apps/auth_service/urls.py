"""
URL patterns for the auth_service app.

Mounted at /api/v1/auth/ by the project urls.py.
"""

from django.urls import path
from .views import RegisterView, LoginView, CustomTokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth-register'),
    path('login/', LoginView.as_view(), name='auth-login'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='auth-token-refresh'),
]
