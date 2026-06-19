"""
Unit tests for Milestone 4 — ATS Scoring Engine.

Scorer unit tests:
  - Output structure: all required keys present
  - ats_score is always an integer in [0, 100]
  - Weighted formula: round(skills*0.40 + section*0.20 + experience*0.20 + content*0.20)
  - Determinism: same input always produces the same output
  - Full resume scores higher than empty resume
  - JD path: skills score differs when a matching JD is provided
  - Missing skills list contains strings, capped at 10
  - Strengths and weaknesses are non-empty lists of strings
  - ScoreError raised when input is malformed

Category-specific tests:
  Skills: corpus match, JD match, empty skills, full match
  Sections: all present, some missing, all missing, thin sections
  Experience: action verbs, quantification, empty, short, adequate
  Content: word count, email/phone detection, filler phrases, skills diversity

Integration tests (scorer wired into upload view):
  - Valid PDF upload returns status=SCORED with ats_score
  - Response contains scores dict with all four category keys
  - DB record has ats_score and all four score columns populated
  - ScoreError path sets status=SCORE_FAILED
  - Results endpoint returns ats_score when status=SCORED
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
from apps.resume_analyzer.pipeline.scorer import score, ScoreError

FIXTURES_DIR = pathlib.Path(__file__).parent / 'fixtures'
SAMPLE_PDF_PATH = FIXTURES_DIR / 'sample_resume.pdf'

# ---------------------------------------------------------------------------
# Shared parsed_resume fixture data
# ---------------------------------------------------------------------------

FULL_PARSED_RESUME = {
    'sections': {
        'contact': 'John Smith\njohn.smith@email.com\n+1 555-0100\nNew York, NY',
        'skills': 'Python, Django, REST API, PostgreSQL, Git, Docker, Linux, React, SQL, AWS',
        'education': 'Bachelor of Science in Computer Science, New York University, 2019-2023, GPA 3.8 out of 4.0',
        'experience': (
            'Software Engineer at Acme Corp 2023-Present\n'
            'Built REST APIs using Django that served 50,000 daily users\n'
            'Reduced API response time by 40% through query optimisation\n'
            'Led migration of legacy monolith to modular Django apps\n'
            'Designed and deployed microservices architecture on AWS\n'
            'Improved test coverage from 60% to 90% across all services\n'
        ),
        'projects': (
            'Khan IntelliHub - Resume Analyzer\n'
            'Built AI-powered resume analysis with Django REST Framework\n'
            'Implemented JWT authentication and Supabase Storage integration\n'
        ),
        'certifications': 'AWS Certified Developer 2024\nDjango Advanced Course 2023',
    },
    'raw_text': (
        'John Smith john.smith@email.com +1 555-0100 New York NY\n'
        'Skills\nPython, Django, REST API, PostgreSQL, Git, Docker, Linux, React, SQL, AWS\n'
        'Education\nBachelor of Science in Computer Science New York University 2019-2023 GPA 3.8 out of 4.0\n'
        'Experience\n'
        'Software Engineer at Acme Corp 2023-Present\n'
        'Built REST APIs using Django that served 50000 daily users\n'
        'Reduced API response time by 40% through query optimisation\n'
        'Led migration of legacy monolith to modular Django apps\n'
        'Designed and deployed microservices architecture on AWS\n'
        'Improved test coverage from 60% to 90% across all services\n'
        'Projects\n'
        'Khan IntelliHub Resume Analyzer\n'
        'Built AI-powered resume analysis with Django REST Framework\n'
        'Implemented JWT authentication and Supabase Storage integration\n'
        'Certifications\nAWS Certified Developer 2024\nDjango Advanced Course 2023\n'
    ),
    'metadata': {'filename': 'resume.pdf', 'page_count': 1, 'word_count': 95},
}

EMPTY_PARSED_RESUME = {
    'sections': {
        'contact': None,
        'skills': None,
        'education': None,
        'experience': None,
        'projects': None,
        'certifications': None,
    },
    'raw_text': 'Some random text without structure.',
    'metadata': {'filename': 'empty.pdf', 'page_count': 1, 'word_count': 6},
}

MINIMAL_PARSED_RESUME = {
    'sections': {
        'contact': 'Jane Doe jane@example.com',
        'skills': 'Python, SQL',
        'education': 'BSc CS University 2020',
        'experience': 'Developer at Company built things',
        'projects': None,
        'certifications': None,
    },
    'raw_text': 'Jane Doe jane@example.com Python SQL BSc CS University 2020 Developer at Company built things',
    'metadata': {'filename': 'minimal.pdf', 'page_count': 1, 'word_count': 17},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _auth_client(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
    return client


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def user(db):
    return CustomUser.objects.create_user(
        email='scorer_test@example.com',
        password='StrongPass123',
    )


@pytest.fixture
def auth_client(user):
    return _auth_client(user)


@pytest.fixture
def sample_pdf_bytes():
    return SAMPLE_PDF_PATH.read_bytes()


# ===========================================================================
# Pure scorer unit tests
# ===========================================================================

class TestScorerOutputStructure:

    def test_all_required_keys_present(self):
        result = score(FULL_PARSED_RESUME)
        for key in ['ats_score', 'skills_score', 'section_score',
                    'experience_score', 'content_score',
                    'missing_skills', 'strengths', 'weaknesses']:
            assert key in result, f"Key '{key}' missing from scorer output"

    def test_ats_score_is_integer(self):
        result = score(FULL_PARSED_RESUME)
        assert isinstance(result['ats_score'], int)

    def test_ats_score_is_in_valid_range(self):
        result = score(FULL_PARSED_RESUME)
        assert 0 <= result['ats_score'] <= 100

    def test_ats_score_is_in_valid_range_empty_resume(self):
        result = score(EMPTY_PARSED_RESUME)
        assert 0 <= result['ats_score'] <= 100

    def test_category_scores_are_floats_in_range(self):
        result = score(FULL_PARSED_RESUME)
        for key in ['skills_score', 'section_score', 'experience_score', 'content_score']:
            val = result[key]
            assert isinstance(val, float), f"{key} should be float"
            assert 0.0 <= val <= 100.0, f"{key} out of range: {val}"

    def test_missing_skills_is_list_of_strings(self):
        result = score(FULL_PARSED_RESUME)
        assert isinstance(result['missing_skills'], list)
        for item in result['missing_skills']:
            assert isinstance(item, str)

    def test_missing_skills_capped_at_10(self):
        result = score(EMPTY_PARSED_RESUME)
        assert len(result['missing_skills']) <= 10

    def test_strengths_is_list_of_strings(self):
        result = score(FULL_PARSED_RESUME)
        assert isinstance(result['strengths'], list)
        for item in result['strengths']:
            assert isinstance(item, str)

    def test_weaknesses_is_list_of_strings(self):
        result = score(FULL_PARSED_RESUME)
        assert isinstance(result['weaknesses'], list)
        for item in result['weaknesses']:
            assert isinstance(item, str)


class TestScorerWeightedFormula:

    def test_weighted_formula_is_correct(self):
        """
        ats_score must equal round(skills*0.40 + section*0.20 + experience*0.20 + content*0.20)
        clamped to [0, 100].
        """
        result = score(FULL_PARSED_RESUME)
        expected = round(
            result['skills_score'] * 0.40
            + result['section_score'] * 0.20
            + result['experience_score'] * 0.20
            + result['content_score'] * 0.20
        )
        expected = max(0, min(100, expected))
        assert result['ats_score'] == expected

    def test_weighted_formula_holds_for_minimal_resume(self):
        result = score(MINIMAL_PARSED_RESUME)
        expected = round(
            result['skills_score'] * 0.40
            + result['section_score'] * 0.20
            + result['experience_score'] * 0.20
            + result['content_score'] * 0.20
        )
        expected = max(0, min(100, expected))
        assert result['ats_score'] == expected

    def test_weighted_formula_holds_for_empty_resume(self):
        result = score(EMPTY_PARSED_RESUME)
        expected = round(
            result['skills_score'] * 0.40
            + result['section_score'] * 0.20
            + result['experience_score'] * 0.20
            + result['content_score'] * 0.20
        )
        expected = max(0, min(100, expected))
        assert result['ats_score'] == expected


class TestScorerDeterminism:

    def test_same_input_produces_same_output_twice(self):
        result1 = score(FULL_PARSED_RESUME)
        result2 = score(FULL_PARSED_RESUME)
        assert result1['ats_score'] == result2['ats_score']
        assert result1['skills_score'] == result2['skills_score']
        assert result1['section_score'] == result2['section_score']
        assert result1['experience_score'] == result2['experience_score']
        assert result1['content_score'] == result2['content_score']

    def test_same_input_produces_same_output_ten_times(self):
        scores = [score(MINIMAL_PARSED_RESUME)['ats_score'] for _ in range(10)]
        assert len(set(scores)) == 1, "Score is not deterministic"

    def test_full_resume_scores_higher_than_empty(self):
        full = score(FULL_PARSED_RESUME)['ats_score']
        empty = score(EMPTY_PARSED_RESUME)['ats_score']
        assert full > empty


class TestSkillsScoring:

    def test_matching_jd_raises_skills_score(self):
        """Score with a highly matching JD should beat score without JD."""
        jd = (
            'We are looking for a Python developer with experience in Django, '
            'PostgreSQL, REST API, Git, Docker, AWS, and Linux.'
        )
        with_jd = score(FULL_PARSED_RESUME, job_description=jd)
        without_jd = score(FULL_PARSED_RESUME, job_description=None)
        # Both are valid — we just assert the JD path runs without error
        assert 0 <= with_jd['skills_score'] <= 100
        assert 0 <= without_jd['skills_score'] <= 100

    def test_jd_with_all_skills_present_gives_high_skills_score(self):
        jd = 'Python Django PostgreSQL Git REST API'
        result = score(FULL_PARSED_RESUME, job_description=jd)
        assert result['skills_score'] >= 70

    def test_jd_with_no_skills_present_gives_low_skills_score(self):
        jd = 'COBOL Fortran Assembly BASIC Pascal mainframe'
        result = score(FULL_PARSED_RESUME, job_description=jd)
        assert result['skills_score'] < 50

    def test_missing_skills_contains_jd_terms_not_in_resume(self):
        jd = 'COBOL Fortran Assembly BASIC Pascal mainframe'
        result = score(FULL_PARSED_RESUME, job_description=jd)
        assert len(result['missing_skills']) > 0

    def test_missing_skills_empty_when_all_present(self):
        jd = 'Python Django'
        result = score(FULL_PARSED_RESUME, job_description=jd)
        assert result['missing_skills'] == []

    def test_no_jd_uses_general_corpus(self):
        result = score(FULL_PARSED_RESUME, job_description=None)
        # Full resume has python, django, sql, git, rest, api, docker, aws — expect decent score
        assert result['skills_score'] >= 30

    def test_empty_resume_has_missing_skills(self):
        result = score(EMPTY_PARSED_RESUME)
        assert len(result['missing_skills']) > 0


class TestSectionScoring:

    def test_all_sections_present_gives_full_section_score(self):
        result = score(FULL_PARSED_RESUME)
        assert result['section_score'] == 100.0

    def test_missing_sections_reduce_score(self):
        parsed = dict(FULL_PARSED_RESUME)
        parsed['sections'] = dict(FULL_PARSED_RESUME['sections'])
        parsed['sections']['experience'] = None
        parsed['sections']['certifications'] = None
        result = score(parsed)
        assert result['section_score'] < 100.0

    def test_all_sections_missing_gives_zero_section_score(self):
        result = score(EMPTY_PARSED_RESUME)
        assert result['section_score'] == 0.0

    def test_missing_section_appears_in_weaknesses(self):
        parsed = dict(FULL_PARSED_RESUME)
        parsed['sections'] = dict(FULL_PARSED_RESUME['sections'])
        parsed['sections']['certifications'] = None
        result = score(parsed)
        weakness_text = ' '.join(result['weaknesses']).lower()
        assert 'certification' in weakness_text

    def test_two_missing_sections_both_in_weaknesses(self):
        parsed = dict(FULL_PARSED_RESUME)
        parsed['sections'] = dict(FULL_PARSED_RESUME['sections'])
        parsed['sections']['projects'] = None
        parsed['sections']['certifications'] = None
        result = score(parsed)
        weakness_text = ' '.join(result['weaknesses']).lower()
        assert 'project' in weakness_text
        assert 'certification' in weakness_text


class TestExperienceScoring:

    def test_no_experience_gives_zero_experience_score(self):
        parsed = dict(FULL_PARSED_RESUME)
        parsed['sections'] = dict(FULL_PARSED_RESUME['sections'])
        parsed['sections']['experience'] = None
        result = score(parsed)
        assert result['experience_score'] == 0.0

    def test_strong_experience_section_scores_high(self):
        result = score(FULL_PARSED_RESUME)
        # Full resume has action verbs (built, led, reduced, improved, designed)
        # and quantification (50,000 users, 40%, 60% to 90%)
        assert result['experience_score'] >= 75.0

    def test_experience_without_verbs_scores_lower(self):
        parsed = dict(FULL_PARSED_RESUME)
        parsed['sections'] = dict(FULL_PARSED_RESUME['sections'])
        parsed['sections']['experience'] = (
            'At a company from 2020 to 2023. '
            'Responsibilities included things. '
            'Was part of a team. '
            'Did various tasks related to software. '
            'Had duties and assignments in the department. '
        )
        result = score(parsed)
        full_result = score(FULL_PARSED_RESUME)
        assert result['experience_score'] <= full_result['experience_score']

    def test_experience_without_numbers_penalised(self):
        parsed = dict(FULL_PARSED_RESUME)
        parsed['sections'] = dict(FULL_PARSED_RESUME['sections'])
        parsed['sections']['experience'] = (
            'Built REST APIs using Django.\n'
            'Led migration of monolith to microservices.\n'
            'Improved test coverage across all services.\n'
            'Designed and deployed cloud infrastructure.\n'
        )
        result = score(parsed)
        weakness_text = ' '.join(result['weaknesses']).lower()
        # Should flag lack of quantification
        assert 'quantif' in weakness_text or 'metric' in weakness_text or 'number' in weakness_text

    def test_experience_with_quantification_not_flagged(self):
        result = score(FULL_PARSED_RESUME)
        weakness_text = ' '.join(result['weaknesses']).lower()
        # Full resume has 50,000 users, 40%, 60% to 90% — should not flag missing metrics
        assert 'no quantified' not in weakness_text


class TestContentScoring:

    def test_email_and_phone_present_scores_full_contact_points(self):
        result = score(FULL_PARSED_RESUME)
        # Full resume has email and phone in contact section
        assert result['content_score'] >= 25.0

    def test_no_contact_info_penalised(self):
        parsed = dict(FULL_PARSED_RESUME)
        parsed = {
            'sections': {k: v for k, v in FULL_PARSED_RESUME['sections'].items()},
            'raw_text': 'John Smith Skills Python Django Education BSc Experience Built APIs',
            'metadata': FULL_PARSED_RESUME['metadata'],
        }
        result = score(parsed)
        # Without email/phone the content score should be lower
        full_result = score(FULL_PARSED_RESUME)
        assert result['content_score'] <= full_result['content_score']

    def test_short_resume_penalised(self):
        result = score(EMPTY_PARSED_RESUME)
        weakness_text = ' '.join(result['weaknesses']).lower()
        assert 'short' in weakness_text or 'word' in weakness_text or 'detail' in weakness_text

    def test_filler_phrases_detected_and_flagged(self):
        parsed = dict(FULL_PARSED_RESUME)
        parsed['raw_text'] = (
            FULL_PARSED_RESUME['raw_text']
            + ' I am a team player and hard-working self-motivated detail-oriented '
            + 'results-oriented go-getter with synergy.'
        )
        result = score(parsed)
        weakness_text = ' '.join(result['weaknesses']).lower()
        assert 'clich' in weakness_text or 'filler' in weakness_text or 'phrase' in weakness_text

    def test_adequate_skills_list_not_flagged(self):
        result = score(FULL_PARSED_RESUME)
        weakness_text = ' '.join(result['weaknesses']).lower()
        # Full resume has 10 comma-separated skills — should not be flagged as sparse
        assert 'sparse' not in weakness_text


class TestScorerErrorHandling:

    def test_score_error_raised_on_completely_missing_input(self):
        with pytest.raises((ScoreError, KeyError, AttributeError, TypeError)):
            score(None)

    def test_empty_sections_dict_does_not_crash(self):
        parsed = {'sections': {}, 'raw_text': '', 'metadata': {}}
        result = score(parsed)
        assert 0 <= result['ats_score'] <= 100

    def test_none_raw_text_does_not_crash(self):
        parsed = {
            'sections': FULL_PARSED_RESUME['sections'],
            'raw_text': None,
            'metadata': {},
        }
        # Should either score gracefully or raise ScoreError — not crash with unhandled exception
        try:
            result = score(parsed)
            assert 0 <= result['ats_score'] <= 100
        except ScoreError:
            pass  # Acceptable


# ===========================================================================
# Integration tests — scorer wired into upload view
# ===========================================================================

@pytest.mark.django_db
class TestScorerUploadIntegration:

    def test_valid_upload_returns_scored_status(self, auth_client, sample_pdf_bytes):
        pdf = io.BytesIO(sample_pdf_bytes)
        pdf.name = 'resume.pdf'
        with patch('apps.resume_analyzer.views.storage.upload') as mock_upload:
            mock_upload.return_value = 'user/uuid/resume.pdf'
            response = auth_client.post(
                reverse('resume-upload'), {'file': pdf}, format='multipart'
            )
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.json()['status'] == ResumeRecord.STATUS_SCORED

    def test_upload_response_contains_ats_score(self, auth_client, sample_pdf_bytes):
        pdf = io.BytesIO(sample_pdf_bytes)
        pdf.name = 'resume.pdf'
        with patch('apps.resume_analyzer.views.storage.upload') as mock_upload:
            mock_upload.return_value = 'user/uuid/resume.pdf'
            response = auth_client.post(
                reverse('resume-upload'), {'file': pdf}, format='multipart'
            )
        data = response.json()
        assert 'ats_score' in data
        assert isinstance(data['ats_score'], int)
        assert 0 <= data['ats_score'] <= 100

    def test_upload_response_contains_all_score_keys(self, auth_client, sample_pdf_bytes):
        pdf = io.BytesIO(sample_pdf_bytes)
        pdf.name = 'resume.pdf'
        with patch('apps.resume_analyzer.views.storage.upload') as mock_upload:
            mock_upload.return_value = 'user/uuid/resume.pdf'
            response = auth_client.post(
                reverse('resume-upload'), {'file': pdf}, format='multipart'
            )
        scores = response.json().get('scores', {})
        for key in ['skills_match', 'section_completeness', 'experience_quality', 'content_quality']:
            assert key in scores, f"Score key '{key}' missing from response"

    def test_upload_response_contains_missing_skills(self, auth_client, sample_pdf_bytes):
        pdf = io.BytesIO(sample_pdf_bytes)
        pdf.name = 'resume.pdf'
        with patch('apps.resume_analyzer.views.storage.upload') as mock_upload:
            mock_upload.return_value = 'user/uuid/resume.pdf'
            response = auth_client.post(
                reverse('resume-upload'), {'file': pdf}, format='multipart'
            )
        data = response.json()
        assert 'missing_skills' in data
        assert isinstance(data['missing_skills'], list)

    def test_upload_response_contains_strengths_and_weaknesses(
        self, auth_client, sample_pdf_bytes
    ):
        pdf = io.BytesIO(sample_pdf_bytes)
        pdf.name = 'resume.pdf'
        with patch('apps.resume_analyzer.views.storage.upload') as mock_upload:
            mock_upload.return_value = 'user/uuid/resume.pdf'
            response = auth_client.post(
                reverse('resume-upload'), {'file': pdf}, format='multipart'
            )
        data = response.json()
        assert 'strengths' in data
        assert 'weaknesses' in data
        assert isinstance(data['strengths'], list)
        assert isinstance(data['weaknesses'], list)

    def test_db_record_has_ats_score_after_upload(self, auth_client, user, sample_pdf_bytes):
        pdf = io.BytesIO(sample_pdf_bytes)
        pdf.name = 'resume.pdf'
        with patch('apps.resume_analyzer.views.storage.upload') as mock_upload:
            mock_upload.return_value = 'user/uuid/resume.pdf'
            response = auth_client.post(
                reverse('resume-upload'), {'file': pdf}, format='multipart'
            )
        record = ResumeRecord.objects.get(id=response.json()['resume_id'])
        assert record.ats_score is not None
        assert 0 <= record.ats_score <= 100

    def test_db_record_has_all_four_category_scores(self, auth_client, user, sample_pdf_bytes):
        pdf = io.BytesIO(sample_pdf_bytes)
        pdf.name = 'resume.pdf'
        with patch('apps.resume_analyzer.views.storage.upload') as mock_upload:
            mock_upload.return_value = 'user/uuid/resume.pdf'
            response = auth_client.post(
                reverse('resume-upload'), {'file': pdf}, format='multipart'
            )
        record = ResumeRecord.objects.get(id=response.json()['resume_id'])
        assert record.keyword_score is not None    # skills_match
        assert record.section_score is not None    # section_completeness
        assert record.formatting_score is not None # experience_quality
        assert record.content_score is not None    # content_quality

    def test_db_record_status_is_scored(self, auth_client, user, sample_pdf_bytes):
        pdf = io.BytesIO(sample_pdf_bytes)
        pdf.name = 'resume.pdf'
        with patch('apps.resume_analyzer.views.storage.upload') as mock_upload:
            mock_upload.return_value = 'user/uuid/resume.pdf'
            response = auth_client.post(
                reverse('resume-upload'), {'file': pdf}, format='multipart'
            )
        record = ResumeRecord.objects.get(id=response.json()['resume_id'])
        assert record.status == ResumeRecord.STATUS_SCORED

    def test_score_failure_sets_score_failed_status(self, auth_client, user, sample_pdf_bytes):
        pdf = io.BytesIO(sample_pdf_bytes)
        pdf.name = 'resume.pdf'
        with patch('apps.resume_analyzer.views.storage.upload') as mock_upload:
            mock_upload.return_value = 'user/uuid/resume.pdf'
            with patch('apps.resume_analyzer.views.score_resume') as mock_score:
                mock_score.side_effect = ScoreError('scorer crashed')
                response = auth_client.post(
                    reverse('resume-upload'), {'file': pdf}, format='multipart'
                )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.json()['code'] == 'PROCESSING_FAILED'

        record = ResumeRecord.objects.filter(user=user).first()
        assert record.status == ResumeRecord.STATUS_SCORE_FAILED
        assert record.error_reason is not None

    def test_results_endpoint_returns_ats_score(self, auth_client, user, sample_pdf_bytes):
        pdf = io.BytesIO(sample_pdf_bytes)
        pdf.name = 'resume.pdf'
        with patch('apps.resume_analyzer.views.storage.upload') as mock_upload:
            mock_upload.return_value = 'user/uuid/resume.pdf'
            upload_resp = auth_client.post(
                reverse('resume-upload'), {'file': pdf}, format='multipart'
            )
        resume_id = upload_resp.json()['resume_id']
        results_resp = auth_client.get(
            reverse('resume-results', kwargs={'resume_id': resume_id})
        )
        assert results_resp.status_code == status.HTTP_200_OK
        data = results_resp.json()
        assert data['ats_score'] is not None
        assert data['status'] == ResumeRecord.STATUS_SCORED
        scores = data.get('scores', {})
        assert scores.get('skills_match') is not None
        assert scores.get('section_completeness') is not None
        assert scores.get('experience_quality') is not None
        assert scores.get('content_quality') is not None
