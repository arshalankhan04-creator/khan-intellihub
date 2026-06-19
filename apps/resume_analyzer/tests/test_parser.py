"""
Unit tests for Milestone 3 — Parser and Upload pipeline integration.

Parser tests:
  - All six sections detected in a well-structured PDF
  - metadata contains filename, page_count, word_count
  - word_count matches actual word count of raw_text
  - ParseError raised on empty / non-text PDF
  - section values are strings or None (never empty strings)

Upload integration tests (parser wired into upload view):
  - Valid PDF upload returns 202 with status=PARSED and parsed_data
  - parsed_data contains all six section keys
  - Image-only / empty PDF returns 422 with PROCESSING_FAILED code
  - DB record status is PARSED after a successful upload
  - DB record status is PARSE_FAILED after a failed parse
"""

import io
import pathlib
import pytest
from unittest.mock import patch
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.auth_service.models import CustomUser
from apps.resume_analyzer.models import ResumeRecord
from apps.resume_analyzer.pipeline.parser import parse, ParseError

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
FIXTURES_DIR = pathlib.Path(__file__).parent / 'fixtures'
SAMPLE_PDF_PATH = FIXTURES_DIR / 'sample_resume.pdf'

SECTION_KEYS = ['contact', 'skills', 'education', 'experience', 'projects', 'certifications']


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_sample_pdf() -> bytes:
    return SAMPLE_PDF_PATH.read_bytes()


def _make_empty_pdf() -> bytes:
    """A valid PDF that contains no text (empty content stream)."""
    content = b'BT ET'
    header = b'%PDF-1.4\n'
    obj1 = b'1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n'
    obj2 = b'2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n'
    obj3 = (
        b'3 0 obj\n'
        b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] '
        b'/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\n'
        b'endobj\n'
    )
    obj4 = (
        b'4 0 obj\n<< /Length ' + str(len(content)).encode() + b' >>\nstream\n'
        + content + b'\nendstream\nendobj\n'
    )
    obj5 = b'5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n'
    objects = [obj1, obj2, obj3, obj4, obj5]
    body = b''.join(objects)
    pos = len(header)
    offsets = []
    for obj in objects:
        offsets.append(pos)
        pos += len(obj)
    xref_pos = len(header) + len(body)
    xref = f'xref\n0 6\n0000000000 65535 f \n'
    for off in offsets:
        xref += f'{off:010d} 00000 n \n'
    trailer = f'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n'
    return header + body + xref.encode() + trailer.encode()


def _auth_client(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
    return client


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_pdf_bytes():
    return _load_sample_pdf()


@pytest.fixture
def empty_pdf_bytes():
    return _make_empty_pdf()


@pytest.fixture
def user(db):
    return CustomUser.objects.create_user(
        email='parser_test@example.com',
        password='StrongPass123',
    )


@pytest.fixture
def auth_client(user):
    return _auth_client(user)


# ---------------------------------------------------------------------------
# Pure parser unit tests
# ---------------------------------------------------------------------------

class TestParser:

    def test_all_six_sections_present_in_output(self, sample_pdf_bytes):
        result = parse(sample_pdf_bytes, 'sample_resume.pdf')
        for key in SECTION_KEYS:
            assert key in result['sections'], f"Section '{key}' missing from output"

    def test_detected_sections_have_content(self, sample_pdf_bytes):
        result = parse(sample_pdf_bytes, 'sample_resume.pdf')
        sections = result['sections']
        # Our fixture has all sections — each should be non-None
        for key in SECTION_KEYS:
            assert sections[key] is not None, f"Section '{key}' should not be None for fixture"
            assert sections[key].strip() != '', f"Section '{key}' should not be empty"

    def test_metadata_contains_required_fields(self, sample_pdf_bytes):
        result = parse(sample_pdf_bytes, 'sample_resume.pdf')
        meta = result['metadata']
        assert 'filename' in meta
        assert 'page_count' in meta
        assert 'word_count' in meta

    def test_metadata_filename_matches_input(self, sample_pdf_bytes):
        result = parse(sample_pdf_bytes, 'my_cv.pdf')
        assert result['metadata']['filename'] == 'my_cv.pdf'

    def test_word_count_matches_raw_text(self, sample_pdf_bytes):
        result = parse(sample_pdf_bytes, 'sample_resume.pdf')
        expected = len(result['raw_text'].split())
        assert result['metadata']['word_count'] == expected

    def test_page_count_is_positive_integer(self, sample_pdf_bytes):
        result = parse(sample_pdf_bytes, 'sample_resume.pdf')
        assert isinstance(result['metadata']['page_count'], int)
        assert result['metadata']['page_count'] >= 1

    def test_raw_text_is_non_empty_string(self, sample_pdf_bytes):
        result = parse(sample_pdf_bytes, 'sample_resume.pdf')
        assert isinstance(result['raw_text'], str)
        assert len(result['raw_text'].strip()) > 0

    def test_section_values_are_string_or_none(self, sample_pdf_bytes):
        result = parse(sample_pdf_bytes, 'sample_resume.pdf')
        for key, value in result['sections'].items():
            assert value is None or isinstance(value, str), \
                f"Section '{key}' must be str or None, got {type(value)}"

    def test_section_values_never_empty_string(self, sample_pdf_bytes):
        """Empty sections must be None, not an empty string."""
        result = parse(sample_pdf_bytes, 'sample_resume.pdf')
        for key, value in result['sections'].items():
            if value is not None:
                assert value.strip() != '', \
                    f"Section '{key}' is an empty string — should be None instead"

    def test_parse_error_raised_on_empty_pdf(self, empty_pdf_bytes):
        with pytest.raises(ParseError) as exc_info:
            parse(empty_pdf_bytes, 'empty.pdf')
        assert 'extract' in str(exc_info.value).lower() or 'text' in str(exc_info.value).lower()

    def test_parse_error_raised_on_non_pdf_bytes(self):
        with pytest.raises(ParseError):
            parse(b'This is definitely not a PDF', 'fake.pdf')

    def test_skills_section_contains_expected_keywords(self, sample_pdf_bytes):
        result = parse(sample_pdf_bytes, 'sample_resume.pdf')
        skills = result['sections']['skills'] or ''
        assert 'Python' in skills

    def test_experience_section_contains_expected_content(self, sample_pdf_bytes):
        result = parse(sample_pdf_bytes, 'sample_resume.pdf')
        experience = result['sections']['experience'] or ''
        assert 'Acme Corp' in experience

    def test_education_section_contains_expected_content(self, sample_pdf_bytes):
        result = parse(sample_pdf_bytes, 'sample_resume.pdf')
        education = result['sections']['education'] or ''
        assert 'University' in education

    def test_certifications_section_contains_expected_content(self, sample_pdf_bytes):
        result = parse(sample_pdf_bytes, 'sample_resume.pdf')
        certs = result['sections']['certifications'] or ''
        assert 'AWS' in certs


# ---------------------------------------------------------------------------
# Upload + parser integration tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestUploadParserIntegration:

    def test_valid_pdf_returns_202_with_parsed_status(self, auth_client, sample_pdf_bytes):
        pdf = io.BytesIO(sample_pdf_bytes)
        pdf.name = 'resume.pdf'

        with patch('apps.resume_analyzer.views.storage.upload') as mock_upload:
            mock_upload.return_value = 'user/uuid/resume.pdf'
            response = auth_client.post(
                reverse('resume-upload'),
                {'file': pdf},
                format='multipart',
            )

        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        # M4: pipeline now advances to SCORED after parse + score
        assert data['status'] == ResumeRecord.STATUS_SCORED

    def test_upload_response_contains_parsed_data(self, auth_client, sample_pdf_bytes):
        pdf = io.BytesIO(sample_pdf_bytes)
        pdf.name = 'resume.pdf'

        with patch('apps.resume_analyzer.views.storage.upload') as mock_upload:
            mock_upload.return_value = 'user/uuid/resume.pdf'
            response = auth_client.post(
                reverse('resume-upload'),
                {'file': pdf},
                format='multipart',
            )

        data = response.json()
        assert 'parsed_data' in data
        parsed = data['parsed_data']
        assert 'sections' in parsed
        assert 'raw_text' in parsed
        assert 'metadata' in parsed

    def test_upload_response_sections_have_all_keys(self, auth_client, sample_pdf_bytes):
        pdf = io.BytesIO(sample_pdf_bytes)
        pdf.name = 'resume.pdf'

        with patch('apps.resume_analyzer.views.storage.upload') as mock_upload:
            mock_upload.return_value = 'user/uuid/resume.pdf'
            response = auth_client.post(
                reverse('resume-upload'),
                {'file': pdf},
                format='multipart',
            )

        sections = response.json()['parsed_data']['sections']
        for key in SECTION_KEYS:
            assert key in sections, f"Section '{key}' missing from upload response"

    def test_db_record_status_is_parsed_after_upload(self, auth_client, user, sample_pdf_bytes):
        pdf = io.BytesIO(sample_pdf_bytes)
        pdf.name = 'resume.pdf'

        with patch('apps.resume_analyzer.views.storage.upload') as mock_upload:
            mock_upload.return_value = 'user/uuid/resume.pdf'
            response = auth_client.post(
                reverse('resume-upload'),
                {'file': pdf},
                format='multipart',
            )

        resume_id = response.json()['resume_id']
        record = ResumeRecord.objects.get(id=resume_id)
        # M4: pipeline now advances to SCORED
        assert record.status == ResumeRecord.STATUS_SCORED
        assert record.parsed_data is not None

    def test_empty_pdf_returns_422_parse_failed(self, auth_client, empty_pdf_bytes):
        pdf = io.BytesIO(empty_pdf_bytes)
        pdf.name = 'empty.pdf'

        with patch('apps.resume_analyzer.views.storage.upload') as mock_upload:
            mock_upload.return_value = 'user/uuid/empty.pdf'
            response = auth_client.post(
                reverse('resume-upload'),
                {'file': pdf},
                format='multipart',
            )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.json()['code'] == 'PROCESSING_FAILED'

    def test_db_record_status_is_parse_failed_on_empty_pdf(
        self, auth_client, user, empty_pdf_bytes
    ):
        pdf = io.BytesIO(empty_pdf_bytes)
        pdf.name = 'empty.pdf'

        with patch('apps.resume_analyzer.views.storage.upload') as mock_upload:
            mock_upload.return_value = 'user/uuid/empty.pdf'
            response = auth_client.post(
                reverse('resume-upload'),
                {'file': pdf},
                format='multipart',
            )

        # Record is created (storage succeeded), but status=PARSE_FAILED
        record = ResumeRecord.objects.filter(user=user).first()
        assert record is not None
        assert record.status == ResumeRecord.STATUS_PARSE_FAILED
        assert record.error_reason is not None
        assert record.error_reason.strip() != ''

    def test_results_endpoint_returns_parsed_data(self, auth_client, user, sample_pdf_bytes):
        pdf = io.BytesIO(sample_pdf_bytes)
        pdf.name = 'resume.pdf'

        with patch('apps.resume_analyzer.views.storage.upload') as mock_upload:
            mock_upload.return_value = 'user/uuid/resume.pdf'
            upload_resp = auth_client.post(
                reverse('resume-upload'),
                {'file': pdf},
                format='multipart',
            )

        resume_id = upload_resp.json()['resume_id']
        results_resp = auth_client.get(
            reverse('resume-results', kwargs={'resume_id': resume_id})
        )

        assert results_resp.status_code == status.HTTP_200_OK
        data = results_resp.json()
        # M4: pipeline now advances to SCORED after parse + score
        assert data['status'] == ResumeRecord.STATUS_SCORED
        assert data['parsed_data'] is not None
        assert 'sections' in data['parsed_data']

    def test_results_endpoint_returns_403_for_wrong_user(
        self, auth_client, user, sample_pdf_bytes
    ):
        # Upload as user A
        pdf = io.BytesIO(sample_pdf_bytes)
        pdf.name = 'resume.pdf'
        with patch('apps.resume_analyzer.views.storage.upload') as mock_upload:
            mock_upload.return_value = 'user/uuid/resume.pdf'
            upload_resp = auth_client.post(
                reverse('resume-upload'),
                {'file': pdf},
                format='multipart',
            )
        resume_id = upload_resp.json()['resume_id']

        # Try to access as user B
        user_b = CustomUser.objects.create_user(
            email='userb_parser@example.com', password='StrongPass123'
        )
        client_b = _auth_client(user_b)
        response = client_b.get(
            reverse('resume-results', kwargs={'resume_id': resume_id})
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_results_endpoint_returns_404_for_unknown_id(self, auth_client):
        import uuid
        response = auth_client.get(
            reverse('resume-results', kwargs={'resume_id': uuid.uuid4()})
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
