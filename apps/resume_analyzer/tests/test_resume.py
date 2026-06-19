"""
Unit tests for Milestone 2 — Resume Upload, History, and Delete endpoints.

Supabase Storage is mocked throughout so no real bucket calls are made.
All DB operations use pytest-django's test database.

Test coverage:
  Upload:
    - Unauthenticated request → 401
    - No file in request → 400
    - Non-PDF file → 415
    - File exceeding 5 MB → 413
    - Valid PDF → 202, ResumeRecord created with status=PENDING
    - Storage failure → 500, no orphan DB record

  History (list):
    - Unauthenticated request → 401
    - Returns only the authenticated user's records
    - Correct pagination fields returned
    - Page beyond range returns empty results, not an error
    - Invalid page param → 400

  Delete:
    - Unauthenticated request → 401
    - Non-existent resume_id → 404
    - Another user's record → 403
    - Successful delete → 204, record removed from DB
    - Storage failure → 500, DB record retained
"""

import io
import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.auth_service.models import CustomUser
from apps.resume_analyzer.models import ResumeRecord


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pdf_bytes(size_bytes: int = 1024) -> bytes:
    """Return a minimal valid PDF byte string of approximately the given size."""
    # A real PDF starts with %PDF — our serializer checks this magic number
    header = b'%PDF-1.4\n'
    padding = b'x' * max(0, size_bytes - len(header))
    return header + padding


def _make_non_pdf_bytes() -> bytes:
    """Return bytes that are clearly not a PDF (PNG magic number)."""
    return b'\x89PNG\r\n\x1a\n' + b'x' * 100


def _auth_client(user: CustomUser) -> APIClient:
    """Return an APIClient with a valid Bearer token for the given user."""
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
    return client


def _upload_url():
    return reverse('resume-upload')


def _list_url():
    return reverse('resume-list')


def _delete_url(resume_id):
    return reverse('resume-delete', kwargs={'resume_id': resume_id})


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def user_a(db):
    return CustomUser.objects.create_user(
        email='usera@example.com',
        password='StrongPass123',
    )


@pytest.fixture
def user_b(db):
    return CustomUser.objects.create_user(
        email='userb@example.com',
        password='StrongPass123',
    )


@pytest.fixture
def client_a(user_a):
    return _auth_client(user_a)


@pytest.fixture
def client_b(user_b):
    return _auth_client(user_b)


@pytest.fixture
def anon_client():
    return APIClient()


@pytest.fixture
def resume_record_a(user_a):
    """A ResumeRecord owned by user_a."""
    return ResumeRecord.objects.create(
        user=user_a,
        original_filename='resume_a.pdf',
        storage_path='usera/abc/resume_a.pdf',
        status=ResumeRecord.STATUS_PENDING,
    )


# ---------------------------------------------------------------------------
# Upload tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestResumeUpload:

    def test_unauthenticated_returns_401(self, anon_client):
        response = anon_client.post(_upload_url(), {}, format='multipart')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_missing_file_returns_400(self, client_a):
        response = client_a.post(_upload_url(), {}, format='multipart')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()['code'] == 'VALIDATION_ERROR'

    def test_non_pdf_file_returns_415(self, client_a):
        fake_file = io.BytesIO(_make_non_pdf_bytes())
        fake_file.name = 'photo.png'
        with patch('apps.resume_analyzer.views.storage.upload') as mock_upload:
            response = client_a.post(
                _upload_url(),
                {'file': fake_file},
                format='multipart',
            )
        assert response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        data = response.json()
        assert data['code'] == 'UNSUPPORTED_MEDIA_TYPE'
        assert 'PDF' in data['error']
        # Storage must never be called for an invalid file
        mock_upload.assert_not_called()

    def test_file_over_5mb_returns_413(self, client_a):
        big_file = io.BytesIO(_make_pdf_bytes(size_bytes=6 * 1024 * 1024))
        big_file.name = 'big_resume.pdf'
        response = client_a.post(
            _upload_url(),
            {'file': big_file},
            format='multipart',
        )
        assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        assert response.json()['code'] == 'FILE_TOO_LARGE'

    def test_valid_pdf_creates_pending_record(self, client_a, user_a):
        # Use the real sample PDF fixture so pdfminer can parse it.
        # After M3, a successful upload advances status to PARSED, not PENDING.
        import pathlib
        sample_pdf = pathlib.Path(__file__).parent / 'fixtures' / 'sample_resume.pdf'
        pdf = io.BytesIO(sample_pdf.read_bytes())
        pdf.name = 'my_resume.pdf'

        with patch('apps.resume_analyzer.views.storage.upload') as mock_upload:
            mock_upload.return_value = f'{user_a.id}/some-uuid/my_resume.pdf'
            response = client_a.post(
                _upload_url(),
                {'file': pdf},
                format='multipart',
            )

        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert 'resume_id' in data
        # M3: status is PARSED (not PENDING) after a successful upload+parse
        assert data['status'] == ResumeRecord.STATUS_PARSED

        record = ResumeRecord.objects.get(id=data['resume_id'])
        assert record.user == user_a
        assert record.status == ResumeRecord.STATUS_PARSED
        assert record.original_filename == 'my_resume.pdf'
        assert record.storage_path != ''
        assert record.parsed_data is not None

    def test_valid_pdf_with_job_description_stored(self, client_a, user_a):
        import pathlib
        sample_pdf = pathlib.Path(__file__).parent / 'fixtures' / 'sample_resume.pdf'
        pdf = io.BytesIO(sample_pdf.read_bytes())
        pdf.name = 'resume.pdf'
        jd_text = 'Looking for a Python developer with Django experience.'

        with patch('apps.resume_analyzer.views.storage.upload') as mock_upload:
            mock_upload.return_value = f'{user_a.id}/some-uuid/resume.pdf'
            response = client_a.post(
                _upload_url(),
                {'file': pdf, 'job_description': jd_text},
                format='multipart',
            )

        assert response.status_code == status.HTTP_202_ACCEPTED
        record = ResumeRecord.objects.get(id=response.json()['resume_id'])
        assert record.job_description == jd_text

    def test_storage_failure_returns_500_and_no_orphan_record(self, client_a):
        # Django 4.2 + Python 3.14: the test client crashes when trying to
        # copy the debug error template context on a 500 response.
        # We raise the django.request logger to CRITICAL for this test so
        # the debug reporter never runs. The view behaviour is still validated.
        import logging
        django_request_logger = logging.getLogger('django.request')
        original_level = django_request_logger.level
        django_request_logger.setLevel(logging.CRITICAL)

        try:
            pdf = io.BytesIO(_make_pdf_bytes())
            pdf.name = 'resume.pdf'

            from apps.resume_analyzer.storage import StorageError
            with patch('apps.resume_analyzer.views.storage.upload') as mock_upload:
                mock_upload.side_effect = StorageError('bucket unreachable')
                response = client_a.post(
                    _upload_url(),
                    {'file': pdf},
                    format='multipart',
                )
        finally:
            django_request_logger.setLevel(original_level)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()['code'] == 'INTERNAL_ERROR'
        # No orphan record should remain
        assert ResumeRecord.objects.count() == 0


# ---------------------------------------------------------------------------
# History (list) tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestResumeList:

    def test_unauthenticated_returns_401(self, anon_client):
        response = anon_client.get(_list_url())
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_returns_only_own_records(self, client_a, user_a, user_b):
        # Create 2 records for user_a, 1 for user_b
        ResumeRecord.objects.create(
            user=user_a, original_filename='a1.pdf',
            storage_path='a/1', status='PENDING',
        )
        ResumeRecord.objects.create(
            user=user_a, original_filename='a2.pdf',
            storage_path='a/2', status='PENDING',
        )
        ResumeRecord.objects.create(
            user=user_b, original_filename='b1.pdf',
            storage_path='b/1', status='PENDING',
        )

        response = client_a.get(_list_url())
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['total_count'] == 2
        assert len(data['results']) == 2
        filenames = {r['original_filename'] for r in data['results']}
        assert filenames == {'a1.pdf', 'a2.pdf'}

    def test_response_contains_required_fields(self, client_a, user_a):
        ResumeRecord.objects.create(
            user=user_a, original_filename='r.pdf',
            storage_path='u/r', status='PENDING',
        )
        response = client_a.get(_list_url())
        assert response.status_code == status.HTTP_200_OK
        item = response.json()['results'][0]
        assert 'resume_id' in item
        assert 'original_filename' in item
        assert 'upload_timestamp' in item
        assert 'status' in item
        assert 'ats_score' in item      # null for PENDING records

    def test_pagination_defaults(self, client_a, user_a):
        # Create 15 records
        for i in range(15):
            ResumeRecord.objects.create(
                user=user_a, original_filename=f'r{i}.pdf',
                storage_path=f'u/{i}', status='PENDING',
            )
        response = client_a.get(_list_url())
        data = response.json()
        assert data['total_count'] == 15
        assert data['page'] == 1
        assert data['page_size'] == 10
        assert len(data['results']) == 10   # default page size

    def test_page_beyond_range_returns_empty_results(self, client_a, user_a):
        ResumeRecord.objects.create(
            user=user_a, original_filename='r.pdf',
            storage_path='u/r', status='PENDING',
        )
        response = client_a.get(_list_url(), {'page': 99})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['total_count'] == 1
        assert data['results'] == []

    def test_invalid_page_param_returns_400(self, client_a):
        response = client_a.get(_list_url(), {'page': 'abc'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()['code'] == 'VALIDATION_ERROR'

    def test_page_size_too_large_returns_400(self, client_a):
        response = client_a.get(_list_url(), {'page_size': 999})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()['code'] == 'VALIDATION_ERROR'

    def test_empty_history_returns_200_with_empty_list(self, client_a):
        response = client_a.get(_list_url())
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['total_count'] == 0
        assert data['results'] == []


# ---------------------------------------------------------------------------
# Delete tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestResumeDelete:

    def test_unauthenticated_returns_401(self, anon_client, resume_record_a):
        response = anon_client.delete(_delete_url(resume_record_a.id))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_nonexistent_id_returns_404(self, client_a):
        import uuid
        fake_id = uuid.uuid4()
        response = client_a.delete(_delete_url(fake_id))
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()['code'] == 'NOT_FOUND'

    def test_other_users_record_returns_403(self, client_b, resume_record_a):
        """user_b trying to delete user_a's record should get 403."""
        with patch('apps.resume_analyzer.views.storage.delete'):
            response = client_b.delete(_delete_url(resume_record_a.id))
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()['code'] == 'FORBIDDEN'
        # Record must still exist
        assert ResumeRecord.objects.filter(id=resume_record_a.id).exists()

    def test_successful_delete_returns_204(self, client_a, resume_record_a):
        with patch('apps.resume_analyzer.views.storage.delete') as mock_del:
            response = client_a.delete(_delete_url(resume_record_a.id))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_del.assert_called_once_with(resume_record_a.storage_path)
        # DB record must be gone
        assert not ResumeRecord.objects.filter(id=resume_record_a.id).exists()

    def test_storage_failure_returns_500_and_retains_db_record(
        self, client_a, resume_record_a
    ):
        # Same Django 4.2 / Python 3.14 workaround as upload storage-failure test
        import logging
        django_request_logger = logging.getLogger('django.request')
        original_level = django_request_logger.level
        django_request_logger.setLevel(logging.CRITICAL)

        try:
            from apps.resume_analyzer.storage import StorageError
            with patch('apps.resume_analyzer.views.storage.delete') as mock_del:
                mock_del.side_effect = StorageError('bucket error')
                response = client_a.delete(_delete_url(resume_record_a.id))
        finally:
            django_request_logger.setLevel(original_level)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()['code'] == 'INTERNAL_ERROR'
        # DB record must be retained
        assert ResumeRecord.objects.filter(id=resume_record_a.id).exists()
