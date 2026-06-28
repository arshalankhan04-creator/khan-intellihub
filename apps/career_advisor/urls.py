from django.urls import path
from .views import (
    CareerAdvisorGenerateView,
    CareerAdvisorResultsView,
    CareerAdvisorHistoryView
)

urlpatterns = [
    # POST /api/v1/career-advisor/generate/
    path('generate/', CareerAdvisorGenerateView.as_view(), name='career-advisor-generate'),

    # GET /api/v1/career-advisor/{record_id}/results/
    path('<uuid:record_id>/results/', CareerAdvisorResultsView.as_view(), name='career-advisor-results'),

    # GET /api/v1/career-advisor/history/
    path('history/', CareerAdvisorHistoryView.as_view(), name='career-advisor-history'),
]
