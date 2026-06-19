"""
URL patterns for the resume_analyzer app.

Mounted at /api/v1/resumes/ by the project urls.py.
"""

from django.urls import path
from .views import ResumeUploadView, ResumeListView, ResumeDeleteView, ResumeResultsView

urlpatterns = [
    # POST /api/v1/resumes/upload/
    path('upload/', ResumeUploadView.as_view(), name='resume-upload'),

    # GET /api/v1/resumes/
    path('', ResumeListView.as_view(), name='resume-list'),

    # GET /api/v1/resumes/{resume_id}/results/
    path('<uuid:resume_id>/results/', ResumeResultsView.as_view(), name='resume-results'),

    # DELETE /api/v1/resumes/{resume_id}/
    path('<uuid:resume_id>/', ResumeDeleteView.as_view(), name='resume-delete'),
]
