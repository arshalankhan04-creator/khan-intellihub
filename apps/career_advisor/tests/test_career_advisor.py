import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.auth_service.models import CustomUser
from apps.resume_analyzer.models import ResumeRecord
from apps.career_advisor.models import CareerAdvisorRecord

# Helper to authenticate user
def _auth_client(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
    return client

@pytest.fixture
def user1(db):
    return CustomUser.objects.create_user(
        email='user1@example.com',
        password='Password123'
    )

@pytest.fixture
def user2(db):
    return CustomUser.objects.create_user(
        email='user2@example.com',
        password='Password123'
    )

@pytest.fixture
def auth_client1(user1):
    return _auth_client(user1)

@pytest.fixture
def auth_client2(user2):
    return _auth_client(user2)

@pytest.fixture
def completed_resume1(user1):
    return ResumeRecord.objects.create(
        user=user1,
        original_filename='resume1.pdf',
        storage_path='user1/resume1.pdf',
        status=ResumeRecord.STATUS_COMPLETED,
        ats_score=75,
        keyword_score=80.0,
        section_score=90.0,
        formatting_score=70.0,
        content_score=60.0,
        parsed_data={
            'sections': {
                'skills': 'Python, Django, SQL, Git',
                'experience': 'Worked as a software engineer for 2 years.'
            },
            'raw_text': 'Python, Django, SQL, Git. Worked as a software engineer for 2 years.'
        },
        feedback_report={
            'overall_summary': 'Good resume.',
            'missing_skills': ['Docker', 'AWS']
        }
    )

@pytest.fixture
def pending_resume1(user1):
    return ResumeRecord.objects.create(
        user=user1,
        original_filename='pending.pdf',
        storage_path='user1/pending.pdf',
        status=ResumeRecord.STATUS_PENDING
    )

# ===========================================================================
# Endpoints Unit Tests
# ===========================================================================

class TestCareerAdvisorGenerateView:

    def test_unauthenticated_user_denied(self):
        client = APIClient()
        url = reverse('career-advisor-generate')
        response = client.post(url, data={'resume_id': '00000000-0000-0000-0000-000000000000'})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_generate_advice_success_with_fallback(self, auth_client1, completed_resume1):
        url = reverse('career-advisor-generate')
        data = {
            'resume_id': str(completed_resume1.id),
            'target_role': 'Backend Engineer',
            'location': 'New York'
        }
        response = auth_client1.post(url, data=data)
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verify response structure
        res_data = response.data
        assert 'id' in res_data
        assert res_data['resume_filename'] == 'resume1.pdf'
        assert res_data['target_role'] == 'Backend Engineer'
        assert res_data['location'] == 'New York'
        assert len(res_data['career_paths']) > 0
        assert 'salary_insights' in res_data
        assert len(res_data['recommended_jobs']) > 0
        assert len(res_data['action_plan']) > 0
        
        # Verify db record exists
        assert CareerAdvisorRecord.objects.filter(id=res_data['id']).exists()

    def test_non_existent_resume_returns_400(self, auth_client1):
        url = reverse('career-advisor-generate')
        data = {
            'resume_id': '00000000-0000-0000-0000-000000000000'
        }
        response = auth_client1.post(url, data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'details' in response.data

    def test_another_users_resume_returns_400(self, auth_client2, completed_resume1):
        url = reverse('career-advisor-generate')
        data = {
            'resume_id': str(completed_resume1.id)
        }
        response = auth_client2.post(url, data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_incomplete_resume_status_returns_400(self, auth_client1, pending_resume1):
        url = reverse('career-advisor-generate')
        data = {
            'resume_id': str(pending_resume1.id)
        }
        response = auth_client1.post(url, data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_generate_advice_manual_mode_success(self, auth_client1):
        url = reverse('career-advisor-generate')
        data = {
            'target_role': 'Frontend Engineer',
            'location': 'Seattle',
            'skills': ['React', 'JavaScript', 'HTML', 'CSS']
        }
        response = auth_client1.post(url, data=data)
        assert response.status_code == status.HTTP_201_CREATED
        
        res_data = response.data
        assert 'id' in res_data
        assert res_data['resume_record'] is None
        assert res_data['resume_filename'] is None
        assert res_data['target_role'] == 'Frontend Engineer'
        assert res_data['location'] == 'Seattle'
        assert len(res_data['career_paths']) > 0
        assert 'salary_insights' in res_data

    def test_generate_advice_manual_mode_missing_skills_fails(self, auth_client1):
        url = reverse('career-advisor-generate')
        data = {
            'target_role': 'Frontend Engineer',
            'location': 'Seattle',
            'skills': []
        }
        response = auth_client1.post(url, data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'details' in response.data
        assert 'skills' in response.data['details']



class TestCareerAdvisorResultsView:

    @pytest.fixture
    def advice_record(self, user1, completed_resume1):
        return CareerAdvisorRecord.objects.create(
            user=user1,
            resume_record=completed_resume1,
            target_role='Data Scientist',
            location='San Francisco',
            career_paths=[{'name': 'Data Scientist', 'match_score': 90}],
            salary_insights={'current_estimated': '$100k'},
            recommended_jobs=[{'title': 'DS Job'}],
            action_plan=['Learn Python']
        )

    def test_retrieve_results_success(self, auth_client1, advice_record):
        url = reverse('career-advisor-results', kwargs={'record_id': str(advice_record.id)})
        response = auth_client1.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['target_role'] == 'Data Scientist'
        assert response.data['location'] == 'San Francisco'

    def test_retrieve_results_forbidden_for_other_user(self, auth_client2, advice_record):
        url = reverse('career-advisor-results', kwargs={'record_id': str(advice_record.id)})
        response = auth_client2.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve_results_not_found(self, auth_client1):
        url = reverse('career-advisor-results', kwargs={'record_id': '00000000-0000-0000-0000-000000000000'})
        response = auth_client1.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestCareerAdvisorHistoryView:

    def test_history_empty(self, auth_client1):
        url = reverse('career-advisor-history')
        response = auth_client1.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_count'] == 0
        assert len(response.data['results']) == 0

    def test_history_list(self, auth_client1, user1, completed_resume1):
        # Create 3 records
        for i in range(3):
            CareerAdvisorRecord.objects.create(
                user=user1,
                resume_record=completed_resume1,
                target_role=f'Role {i}'
            )
        
        url = reverse('career-advisor-history')
        response = auth_client1.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_count'] == 3
        assert len(response.data['results']) == 3
        # History is ordered newest first (which matches creation/default)
        assert response.data['results'][0]['target_role'] == 'Role 2'
