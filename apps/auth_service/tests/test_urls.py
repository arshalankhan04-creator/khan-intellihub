"""
URL configuration used only during JWT protection tests.
Extends the main urlconf with a single protected endpoint so tests
don't rely on hitting non-existent URLs (which triggers a Django 4.2 /
Python 3.14 incompatibility in the debug error logger).
"""

from django.urls import path, include
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected_test_view(request):
    """A minimal endpoint that requires a valid JWT. Used in tests only."""
    return Response({'ok': True})


urlpatterns = [
    # All real auth routes
    path('api/v1/auth/', include('apps.auth_service.urls')),
    # Test-only protected route
    path('api/v1/test-protected/', protected_test_view, name='test-protected'),
]
