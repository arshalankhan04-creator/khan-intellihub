"""
Project-level URL configuration.
All API endpoints live under /api/v1/ (Req 9.2).
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Django admin (keep for superuser access during development)
    path('admin/', admin.site.urls),

    # Auth endpoints: /api/v1/auth/
    path('api/v1/auth/', include('apps.auth_service.urls')),

    # Resume endpoints: /api/v1/resumes/
    path('api/v1/resumes/', include('apps.resume_analyzer.urls')),

    # Career Advisor endpoints: /api/v1/career-advisor/
    path('api/v1/career-advisor/', include('apps.career_advisor.urls')),
]
