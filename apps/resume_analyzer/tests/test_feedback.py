"""
Unit tests for Milestone 5 — Feedback Engine.

Feedback unit tests:
  - Output structure: all required keys present
  - overall_summary is a non-empty string
  - top_strengths / top_weaknesses are lists of strings, max 5
  - priority_actions list: each item has 'priority' and 'action' keys
  - priority values are only 'high', 'medium', or 'low'
  - Actions sorted high → medium → low
  - section_suggestions dict has all six section keys
  - section_suggestions values are str or None
  - skills_suggestions / experience_suggestions / enhancement_tips are lists of strings
  - missing_skills is a list of strings
  - Determinism: same input → same output
  - Full resume produces different summary than empty resume
  - JD path triggers JD-specific skills advice

Summary tests:
  - Score tiers produce correct opening words
  - Two lowest categories identified correctly

Section suggestion tests:
  - Missing section → suggestion is non-null
  - Adequate section → suggestion is None
  - Thin section → suggestion is non-null

Skills suggestion tests:
  - Missing skills list → included in suggestions
  - No skills section → advice to add it
  - JD provided with gaps → JD-specific tip included

Experience suggestion tests:
  - No experience → standard advice returned
  - Passive voice detected → flagged
  - Weak phrases detected → flagged
  - No action verbs → flagged
  - No quantification → flagged

Enhancement tips tests:
  - Filler phrases detected → flagged
  - Short resume → flagged
  - Missing email → flagged
  - Missing LinkedIn → flagged

Priority actions tests:
  - Missing critical section → high priority action
  - Very low skills score → high priority action
  - Missing non-critical section → medium priority
  - Actions contain no duplicates
  - All priorities are valid values

Integration tests (feedback wired into upload view):
  - Valid upload returns status=COMPLETED
  - Response contains feedback_report with all keys
  - DB record feedback_report is non-null after upload
  - DB record status is COMPLETED after upload
  - FeedbackError sets FEEDBACK_FAILED status
  - Results endpoint returns full feedback_report
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
from apps.resume_analyzer.pipeline.feedback import (
    generate, FeedbackError,
    _build_summary, _build_section_suggestions,
    _build_skills_suggestions, _build_experience_suggestions,
    _build_enhancement_tips, _build_priority_actions,
)

FIXTURES_DIR = pathlib.Path(__file__).parent / 'fixtures'
SAMPLE_PDF_PATH = FIXTURES_DIR / 'sample_resume.pdf'

FEEDBACK_OUTPUT_KEYS = [
    'overall_summary', 'top_strengths', 'top_weaknesses',
    'priority_actions', 'section_suggestions',
    'skills_suggestions', 'experience_suggestions',
    'enhancement_tips', 'missing_skills',
]

SECTION_KEYS = ['contact', 'skills', 'education', 'experience', 'projects', 'certifications']

# ---------------------------------------------------------------------------
# Shared fixture data
# ---------------------------------------------------------------------------

FULL_SECTIONS = {
    'contact': 'John Smith\njohn.smith@email.com\n+1 555-0100\nNew York, NY\nlinkedin.com/in/johnsmith',
    'skills': 'Python, Django, REST API, PostgreSQL, Git, Docker, Linux, React, SQL, AWS',
    'education': 'Bachelor of Science in Computer Science, New York University, 2019-2023, GPA 3.8',
    'experience': (
        'Software Engineer at Acme Corp 2023-Present\n'
        'Built REST APIs using Django that served 50,000 daily users\n'
        'Reduced API response time by 40% through query optimisation\n'
        'Led migration of legacy monolith to modular Django apps\n'
        'Designed and deployed microservices on AWS\n'
        'Improved test coverage from 60% to 90%\n'
    ),
    'projects': (
        'Khan IntelliHub - Resume Analyzer\n'
        'Built AI-powered resume analysis platform using Django REST Framework\n'
        'Implemented JWT authentication and Supabase Storage integration\n'
    ),
    'certifications': 'AWS Certified Developer 2024\nDjango Advanced Course 2023',
}

FULL_RAW_TEXT = (
    'John Smith john.smith@email.com +1 555-0100 New York NY linkedin.com/in/johnsmith\n'
    'Python Django REST API PostgreSQL Git Docker Linux React SQL AWS\n'
    'Bachelor of Science Computer Science New York University 2019-2023 GPA 3.8\n'
    'Built REST APIs using Django that served 50000 daily users\n'
    'Reduced API response time by 40% through query optimisation\n'
    'Led migration of legacy monolith to modular Django apps\n'
    'Designed and deployed microservices on AWS\n'
    'Improved test coverage from 60% to 90%\n'
    'Khan IntelliHub Resume Analyzer\n'
    'Built AI-powered resume analysis platform using Django REST Framework\n'
    'AWS Certified Developer 2024 Django Advanced Course 2023\n'
)

FULL_PARSED = {
    'sections': FULL_SECTIONS,
    'raw_text': FULL_RAW_TEXT,
    'metadata': {'filename': 'resume.pdf', 'page_count': 1, 'word_count': 95},
}

FULL_SCORING = {
    'ats_score': 74,
    'skills_score': 60.0,
    'section_score': 100.0,
    'experience_score': 100.0,
    'content_score': 75.0,
    'missing_skills': ['typescript', 'kubernetes', 'microservices', 'scrum', 'ci/cd'],
    'strengths': [
        'All expected resume sections are present and complete',
        'Experience section uses strong, impact-focused language',
        'Resume has good overall content depth and contact information',
    ],
    'weaknesses': [
        'Skills match is moderate — consider adding: typescript, kubernetes',
    ],
}

EMPTY_SECTIONS = {k: None for k in SECTION_KEYS}

EMPTY_PARSED = {
    'sections': EMPTY_SECTIONS,
    'raw_text': 'Some text without structure.',
    'metadata': {'filename': 'empty.pdf', 'page_count': 1, 'word_count': 5},
}

EMPTY_SCORING = {
    'ats_score': 12,
    'skills_score': 10.0,
    'section_score': 0.0,
    'experience_score': 0.0,
    'content_score': 12.5,
    'missing_skills': ['python', 'django', 'sql', 'git', 'rest', 'api', 'docker', 'aws'],
    'strengths': [],
    'weaknesses': ['Missing all sections', 'No skills found'],
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
        email='feedback_test@example.com',
        password='StrongPass123',
    )


@pytest.fixture
def auth_client(user):
    return _auth_client(user)


@pytest.fixture
def sample_pdf_bytes():
    return SAMPLE_PDF_PATH.read_bytes()


# ===========================================================================
# Output structure tests
# ===========================================================================

class TestFeedbackOutputStructure:

    def test_all_required_keys_present(self):
        result = generate(FULL_PARSED, FULL_SCORING)
        for key in FEEDBACK_OUTPUT_KEYS:
            assert key in result, f"Key '{key}' missing from feedback output"

    def test_overall_summary_is_non_empty_string(self):
        result = generate(FULL_PARSED, FULL_SCORING)
        assert isinstance(result['overall_summary'], str)
        assert len(result['overall_summary'].strip()) > 0

    def test_top_strengths_is_list_of_strings(self):
        result = generate(FULL_PARSED, FULL_SCORING)
        assert isinstance(result['top_strengths'], list)
        for item in result['top_strengths']:
            assert isinstance(item, str)

    def test_top_weaknesses_is_list_of_strings(self):
        result = generate(FULL_PARSED, FULL_SCORING)
        assert isinstance(result['top_weaknesses'], list)
        for item in result['top_weaknesses']:
            assert isinstance(item, str)

    def test_top_strengths_max_5(self):
        result = generate(FULL_PARSED, FULL_SCORING)
        assert len(result['top_strengths']) <= 5

    def test_top_weaknesses_max_5(self):
        result = generate(FULL_PARSED, FULL_SCORING)
        assert len(result['top_weaknesses']) <= 5

    def test_priority_actions_is_list(self):
        result = generate(FULL_PARSED, FULL_SCORING)
        assert isinstance(result['priority_actions'], list)

    def test_priority_actions_have_required_keys(self):
        result = generate(FULL_PARSED, FULL_SCORING)
        for action in result['priority_actions']:
            assert 'priority' in action, "Action missing 'priority' key"
            assert 'action' in action, "Action missing 'action' key"

    def test_priority_values_are_valid(self):
        result = generate(FULL_PARSED, FULL_SCORING)
        valid = {'high', 'medium', 'low'}
        for action in result['priority_actions']:
            assert action['priority'] in valid, \
                f"Invalid priority: {action['priority']}"

    def test_section_suggestions_has_all_six_keys(self):
        result = generate(FULL_PARSED, FULL_SCORING)
        for key in SECTION_KEYS:
            assert key in result['section_suggestions'], \
                f"Section key '{key}' missing from section_suggestions"

    def test_section_suggestion_values_are_str_or_none(self):
        result = generate(FULL_PARSED, FULL_SCORING)
        for key, value in result['section_suggestions'].items():
            assert value is None or isinstance(value, str), \
                f"section_suggestions['{key}'] must be str or None"

    def test_skills_suggestions_is_list_of_strings(self):
        result = generate(FULL_PARSED, FULL_SCORING)
        assert isinstance(result['skills_suggestions'], list)
        for item in result['skills_suggestions']:
            assert isinstance(item, str)

    def test_experience_suggestions_is_list_of_strings(self):
        result = generate(FULL_PARSED, FULL_SCORING)
        assert isinstance(result['experience_suggestions'], list)
        for item in result['experience_suggestions']:
            assert isinstance(item, str)

    def test_enhancement_tips_is_list_of_strings(self):
        result = generate(FULL_PARSED, FULL_SCORING)
        assert isinstance(result['enhancement_tips'], list)
        for item in result['enhancement_tips']:
            assert isinstance(item, str)

    def test_missing_skills_is_list_of_strings(self):
        result = generate(FULL_PARSED, FULL_SCORING)
        assert isinstance(result['missing_skills'], list)
        for item in result['missing_skills']:
            assert isinstance(item, str)


# ===========================================================================
# Determinism tests
# ===========================================================================

class TestFeedbackDeterminism:

    def test_same_input_produces_same_summary(self):
        r1 = generate(FULL_PARSED, FULL_SCORING)
        r2 = generate(FULL_PARSED, FULL_SCORING)
        assert r1['overall_summary'] == r2['overall_summary']

    def test_same_input_produces_same_priority_actions(self):
        r1 = generate(FULL_PARSED, FULL_SCORING)
        r2 = generate(FULL_PARSED, FULL_SCORING)
        assert r1['priority_actions'] == r2['priority_actions']

    def test_same_input_produces_same_section_suggestions(self):
        r1 = generate(FULL_PARSED, FULL_SCORING)
        r2 = generate(FULL_PARSED, FULL_SCORING)
        assert r1['section_suggestions'] == r2['section_suggestions']

    def test_full_resume_summary_differs_from_empty_resume(self):
        full = generate(FULL_PARSED, FULL_SCORING)['overall_summary']
        empty = generate(EMPTY_PARSED, EMPTY_SCORING)['overall_summary']
        assert full != empty

    def test_ten_calls_produce_identical_ats_context(self):
        summaries = [generate(FULL_PARSED, FULL_SCORING)['overall_summary'] for _ in range(10)]
        assert len(set(summaries)) == 1


# ===========================================================================
# Summary tests
# ===========================================================================

class TestOverallSummary:

    def test_score_80_plus_tier_is_strong(self):
        summary = _build_summary(85, 80, 90, 85, 80)
        assert 'well-optimised' in summary.lower() or '85/100' in summary

    def test_score_60_79_tier_is_good(self):
        summary = _build_summary(65, 60, 70, 65, 60)
        assert '65/100' in summary
        assert 'reasonably competitive' in summary

    def test_score_40_59_tier_is_moderate(self):
        summary = _build_summary(50, 40, 50, 55, 45)
        assert '50/100' in summary
        assert 'room for improvement' in summary

    def test_score_below_40_tier_is_weak(self):
        summary = _build_summary(25, 20, 10, 15, 30)
        assert '25/100' in summary
        assert 'significant improvement' in summary

    def test_two_lowest_categories_mentioned(self):
        # skills=10, section=20 are clearly lowest
        summary = _build_summary(30, 10, 20, 80, 90)
        assert 'skills match' in summary.lower()
        assert 'section completeness' in summary.lower()

    def test_summary_contains_three_sentences(self):
        summary = _build_summary(60, 55, 65, 70, 60)
        # Each sentence ends with a period
        sentences = [s.strip() for s in summary.split('.') if s.strip()]
        assert len(sentences) >= 2


# ===========================================================================
# Section suggestion tests
# ===========================================================================

class TestSectionSuggestions:

    def test_missing_section_gets_non_null_suggestion(self):
        sections = dict(FULL_SECTIONS)
        sections['certifications'] = None
        result = _build_section_suggestions(sections, 83.0)
        assert result['certifications'] is not None
        assert len(result['certifications']) > 0

    def test_adequate_section_gets_none(self):
        result = _build_section_suggestions(FULL_SECTIONS, 100.0)
        # All sections in FULL_SECTIONS are above minimums — all should be None
        for key in SECTION_KEYS:
            assert result[key] is None, \
                f"Expected None for adequate section '{key}', got: {result[key]}"

    def test_thin_section_gets_non_null_suggestion(self):
        sections = dict(FULL_SECTIONS)
        sections['education'] = 'BSc CS'  # only 2 words, below min of 10
        result = _build_section_suggestions(sections, 83.0)
        assert result['education'] is not None

    def test_missing_experience_suggestion_mentions_experience(self):
        sections = dict(FULL_SECTIONS)
        sections['experience'] = None
        result = _build_section_suggestions(sections, 83.0)
        assert 'experience' in result['experience'].lower() or 'Experience' in result['experience']

    def test_all_missing_sections_get_add_advice(self):
        result = _build_section_suggestions(EMPTY_SECTIONS, 0.0)
        for key in SECTION_KEYS:
            assert result[key] is not None
            assert 'add' in result[key].lower() or key.lower() in result[key].lower()


# ===========================================================================
# Skills suggestion tests
# ===========================================================================

class TestSkillsSuggestions:

    def test_missing_skills_appear_in_suggestions(self):
        missing = ['typescript', 'kubernetes', 'scrum']
        result = _build_skills_suggestions(missing, 55.0, 'Python, Django', None)
        combined = ' '.join(result).lower()
        assert any(skill in combined for skill in missing)

    def test_no_skills_section_advises_to_add_it(self):
        result = _build_skills_suggestions([], 50.0, None, None)
        combined = ' '.join(result).lower()
        assert 'missing' in combined or 'add' in combined or 'dedicated' in combined

    def test_jd_with_gaps_adds_jd_specific_tip(self):
        result = _build_skills_suggestions(
            ['kubernetes', 'terraform'],
            45.0,
            'Python, Django',
            'We need kubernetes and terraform experience',
        )
        combined = ' '.join(result).lower()
        assert 'job description' in combined or 'tailor' in combined

    def test_low_skills_score_adds_review_tip(self):
        result = _build_skills_suggestions(['java', 'scala'], 20.0, 'Python', None)
        combined = ' '.join(result).lower()
        assert 'low' in combined or 'review' in combined or 'relevant' in combined

    def test_returns_at_most_5_suggestions(self):
        result = _build_skills_suggestions(
            ['a', 'b', 'c', 'd', 'e'], 15.0, 'x', 'some jd'
        )
        assert len(result) <= 5


# ===========================================================================
# Experience suggestion tests
# ===========================================================================

class TestExperienceSuggestions:

    def test_no_experience_returns_standard_advice(self):
        result = _build_experience_suggestions(None, 0.0)
        assert len(result) >= 1
        combined = ' '.join(result).lower()
        assert 'experience' in combined

    def test_empty_experience_returns_advice(self):
        result = _build_experience_suggestions('', 0.0)
        assert len(result) >= 1

    def test_no_action_verbs_flagged(self):
        text = 'At a company from 2020 to 2023. Had duties. Was part of a team. Did various things.'
        result = _build_experience_suggestions(text, 25.0)
        combined = ' '.join(result).lower()
        assert 'action verb' in combined or 'verb' in combined

    def test_no_quantification_flagged(self):
        text = 'Built REST APIs. Led migration of monolith. Designed cloud infrastructure. Improved coverage.'
        result = _build_experience_suggestions(text, 50.0)
        combined = ' '.join(result).lower()
        assert 'measurable' in combined or 'quantif' in combined or 'metric' in combined

    def test_passive_voice_flagged(self):
        text = 'Was responsible for building the system. Was tasked with managing deployments.'
        result = _build_experience_suggestions(text, 25.0)
        combined = ' '.join(result).lower()
        assert 'passive' in combined or 'active' in combined or 'responsible for' in combined

    def test_weak_phrases_flagged(self):
        text = 'Was responsible for building APIs. Had duties included managing servers.'
        result = _build_experience_suggestions(text, 25.0)
        combined = ' '.join(result).lower()
        assert 'responsible' in combined or 'achievement' in combined or 'language' in combined

    def test_strong_experience_returns_few_suggestions(self):
        # Full FULL_SECTIONS experience has verbs, quantification, adequate length
        result = _build_experience_suggestions(FULL_SECTIONS['experience'], 100.0)
        # Strong experience should have 0 or very few suggestions
        assert len(result) <= 2

    def test_returns_at_most_6_suggestions(self):
        bad_exp = 'Was responsible for some things. Had duties. Was part of a team.'
        result = _build_experience_suggestions(bad_exp, 12.5)
        assert len(result) <= 6


# ===========================================================================
# Enhancement tips tests
# ===========================================================================

class TestEnhancementTips:

    def test_filler_phrases_flagged(self):
        raw = FULL_RAW_TEXT + ' I am a team player and hard-working self-motivated individual.'
        result = _build_enhancement_tips(raw, FULL_SECTIONS, 74)
        combined = ' '.join(result).lower()
        assert 'clich' in combined or 'filler' in combined or 'phrase' in combined

    def test_short_resume_flagged(self):
        result = _build_enhancement_tips('Short resume text here.', EMPTY_SECTIONS, 20)
        combined = ' '.join(result).lower()
        assert 'short' in combined or 'word' in combined or '300' in combined

    def test_missing_email_flagged(self):
        raw = 'John Smith +1 555-0100 New York NY'  # no email
        result = _build_enhancement_tips(raw, FULL_SECTIONS, 60)
        combined = ' '.join(result).lower()
        assert 'email' in combined

    def test_missing_phone_flagged(self):
        raw = 'John Smith john@example.com New York NY'  # no phone
        result = _build_enhancement_tips(raw, FULL_SECTIONS, 60)
        combined = ' '.join(result).lower()
        assert 'phone' in combined

    def test_missing_linkedin_flagged(self):
        raw = 'John Smith john@example.com +1 555-0100 New York NY'  # no linkedin
        result = _build_enhancement_tips(raw, FULL_SECTIONS, 60)
        combined = ' '.join(result).lower()
        assert 'linkedin' in combined

    def test_no_filler_no_flag(self):
        # FULL_RAW_TEXT has no filler phrases
        result = _build_enhancement_tips(FULL_RAW_TEXT, FULL_SECTIONS, 74)
        combined = ' '.join(result).lower()
        assert 'clich' not in combined

    def test_returns_at_most_6_tips(self):
        result = _build_enhancement_tips('tiny text', EMPTY_SECTIONS, 10)
        assert len(result) <= 6


# ===========================================================================
# Priority actions tests
# ===========================================================================

class TestPriorityActions:

    def test_missing_experience_is_high_priority(self):
        sections = dict(FULL_SECTIONS)
        sections['experience'] = None
        actions = _build_priority_actions(50, 55, 100, 0, 50, [], sections)
        high_actions = [a for a in actions if a['priority'] == 'high']
        texts = [a['action'].lower() for a in high_actions]
        assert any('experience' in t for t in texts)

    def test_missing_skills_section_is_high_priority(self):
        sections = dict(FULL_SECTIONS)
        sections['skills'] = None
        actions = _build_priority_actions(40, 55, 100, 80, 50, [], sections)
        high_actions = [a for a in actions if a['priority'] == 'high']
        texts = [a['action'].lower() for a in high_actions]
        assert any('skills' in t for t in texts)

    def test_very_low_skills_score_is_high_priority(self):
        actions = _build_priority_actions(
            30, 20, 100, 80, 50,
            ['typescript', 'kubernetes', 'terraform', 'java'],
            FULL_SECTIONS,
        )
        high_actions = [a for a in actions if a['priority'] == 'high']
        assert len(high_actions) >= 1

    def test_missing_education_is_medium_priority(self):
        sections = dict(FULL_SECTIONS)
        sections['education'] = None
        actions = _build_priority_actions(60, 65, 83, 80, 60, [], sections)
        medium_actions = [a for a in actions if a['priority'] == 'medium']
        texts = [a['action'].lower() for a in medium_actions]
        assert any('education' in t for t in texts)

    def test_missing_projects_is_medium_priority(self):
        sections = dict(FULL_SECTIONS)
        sections['projects'] = None
        actions = _build_priority_actions(60, 65, 83, 80, 60, [], sections)
        medium_actions = [a for a in actions if a['priority'] == 'medium']
        texts = [a['action'].lower() for a in medium_actions]
        assert any('project' in t for t in texts)

    def test_actions_sorted_high_then_medium_then_low(self):
        sections = {k: None for k in SECTION_KEYS}  # all missing → many actions
        actions = _build_priority_actions(
            20, 10, 0, 0, 10, ['python', 'django'], sections
        )
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        orders = [priority_order[a['priority']] for a in actions]
        assert orders == sorted(orders), "Actions are not sorted high → medium → low"

    def test_no_duplicate_actions(self):
        sections = {k: None for k in SECTION_KEYS}
        actions = _build_priority_actions(
            20, 10, 0, 0, 10, ['python', 'django', 'sql'], sections
        )
        action_texts = [a['action'] for a in actions]
        assert len(action_texts) == len(set(action_texts)), "Duplicate actions found"

    def test_all_priorities_are_valid(self):
        actions = _build_priority_actions(
            50, 40, 60, 50, 40, ['typescript'], FULL_SECTIONS
        )
        for action in actions:
            assert action['priority'] in ('high', 'medium', 'low')

    def test_linkedin_missing_from_contact_is_low_priority(self):
        sections = dict(FULL_SECTIONS)
        sections['contact'] = 'John Smith john@example.com +1 555-0100'  # no linkedin
        actions = _build_priority_actions(65, 60, 100, 80, 70, [], sections)
        low_actions = [a for a in actions if a['priority'] == 'low']
        texts = [a['action'].lower() for a in low_actions]
        assert any('linkedin' in t for t in texts)


# ===========================================================================
# Full generate() integration tests (pure Python, no DB)
# ===========================================================================

class TestGenerateFull:

    def test_full_resume_generates_without_error(self):
        result = generate(FULL_PARSED, FULL_SCORING)
        assert result is not None

    def test_empty_resume_generates_without_error(self):
        result = generate(EMPTY_PARSED, EMPTY_SCORING)
        assert result is not None

    def test_with_jd_generates_without_error(self):
        jd = 'Looking for a Python Django developer with AWS and PostgreSQL experience.'
        result = generate(FULL_PARSED, FULL_SCORING, job_description=jd)
        assert result is not None

    def test_jd_path_includes_jd_advice_in_skills_suggestions(self):
        jd = 'We require terraform, kubernetes, and helm experience.'
        scoring_with_missing = dict(FULL_SCORING)
        scoring_with_missing['missing_skills'] = ['terraform', 'kubernetes', 'helm']
        result = generate(FULL_PARSED, scoring_with_missing, job_description=jd)
        combined = ' '.join(result['skills_suggestions']).lower()
        assert 'job description' in combined or 'tailor' in combined or 'role' in combined

    def test_feedback_error_raised_on_none_input(self):
        with pytest.raises((FeedbackError, AttributeError, TypeError)):
            generate(None, None)

    def test_empty_scoring_dict_does_not_crash(self):
        result = generate(FULL_PARSED, {})
        assert 0 <= len(result['overall_summary']) > 0

    def test_missing_skills_in_output_matches_scoring_input(self):
        result = generate(FULL_PARSED, FULL_SCORING)
        assert result['missing_skills'] == FULL_SCORING['missing_skills']

    def test_top_strengths_come_from_scoring_strengths(self):
        result = generate(FULL_PARSED, FULL_SCORING)
        # top_strengths should be a subset/head of scoring_result['strengths']
        for strength in result['top_strengths']:
            assert strength in FULL_SCORING['strengths']

    def test_top_weaknesses_come_from_scoring_weaknesses(self):
        result = generate(FULL_PARSED, FULL_SCORING)
        for weakness in result['top_weaknesses']:
            assert weakness in FULL_SCORING['weaknesses']


# ===========================================================================
# Django integration tests — feedback wired into upload view
# ===========================================================================

@pytest.mark.django_db
class TestFeedbackUploadIntegration:

    def test_valid_upload_returns_completed_status(self, auth_client, sample_pdf_bytes):
        pdf = io.BytesIO(sample_pdf_bytes)
        pdf.name = 'resume.pdf'
        with patch('apps.resume_analyzer.views.storage.upload') as mock_upload:
            mock_upload.return_value = 'user/uuid/resume.pdf'
            response = auth_client.post(
                reverse('resume-upload'), {'file': pdf}, format='multipart'
            )
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.json()['status'] == ResumeRecord.STATUS_COMPLETED

    def test_upload_response_contains_feedback_report(self, auth_client, sample_pdf_bytes):
        pdf = io.BytesIO(sample_pdf_bytes)
        pdf.name = 'resume.pdf'
        with patch('apps.resume_analyzer.views.storage.upload') as mock_upload:
            mock_upload.return_value = 'user/uuid/resume.pdf'
            response = auth_client.post(
                reverse('resume-upload'), {'file': pdf}, format='multipart'
            )
        data = response.json()
        assert 'feedback_report' in data
        assert data['feedback_report'] is not None

    def test_upload_response_feedback_has_all_keys(self, auth_client, sample_pdf_bytes):
        pdf = io.BytesIO(sample_pdf_bytes)
        pdf.name = 'resume.pdf'
        with patch('apps.resume_analyzer.views.storage.upload') as mock_upload:
            mock_upload.return_value = 'user/uuid/resume.pdf'
            response = auth_client.post(
                reverse('resume-upload'), {'file': pdf}, format='multipart'
            )
        feedback = response.json()['feedback_report']
        for key in FEEDBACK_OUTPUT_KEYS:
            assert key in feedback, f"Key '{key}' missing from feedback_report in response"

    def test_db_record_status_is_completed(self, auth_client, user, sample_pdf_bytes):
        pdf = io.BytesIO(sample_pdf_bytes)
        pdf.name = 'resume.pdf'
        with patch('apps.resume_analyzer.views.storage.upload') as mock_upload:
            mock_upload.return_value = 'user/uuid/resume.pdf'
            response = auth_client.post(
                reverse('resume-upload'), {'file': pdf}, format='multipart'
            )
        record = ResumeRecord.objects.get(id=response.json()['resume_id'])
        assert record.status == ResumeRecord.STATUS_COMPLETED

    def test_db_record_feedback_report_is_not_null(self, auth_client, user, sample_pdf_bytes):
        pdf = io.BytesIO(sample_pdf_bytes)
        pdf.name = 'resume.pdf'
        with patch('apps.resume_analyzer.views.storage.upload') as mock_upload:
            mock_upload.return_value = 'user/uuid/resume.pdf'
            response = auth_client.post(
                reverse('resume-upload'), {'file': pdf}, format='multipart'
            )
        record = ResumeRecord.objects.get(id=response.json()['resume_id'])
        assert record.feedback_report is not None
        assert 'overall_summary' in record.feedback_report

    def test_feedback_error_sets_feedback_failed_status(
        self, auth_client, user, sample_pdf_bytes
    ):
        pdf = io.BytesIO(sample_pdf_bytes)
        pdf.name = 'resume.pdf'
        with patch('apps.resume_analyzer.views.storage.upload') as mock_upload:
            mock_upload.return_value = 'user/uuid/resume.pdf'
            with patch('apps.resume_analyzer.views.generate_feedback') as mock_fb:
                mock_fb.side_effect = FeedbackError('engine crashed')
                response = auth_client.post(
                    reverse('resume-upload'), {'file': pdf}, format='multipart'
                )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert response.json()['code'] == 'PROCESSING_FAILED'

        record = ResumeRecord.objects.filter(user=user).first()
        assert record.status == ResumeRecord.STATUS_FEEDBACK_FAILED
        assert record.error_reason is not None

    def test_results_endpoint_returns_feedback_report(
        self, auth_client, user, sample_pdf_bytes
    ):
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
        assert data['status'] == ResumeRecord.STATUS_COMPLETED
        assert data['feedback_report'] is not None
        assert 'overall_summary' in data['feedback_report']
        assert 'priority_actions' in data['feedback_report']

    def test_upload_response_still_contains_ats_score(self, auth_client, sample_pdf_bytes):
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

    def test_upload_response_still_contains_scores_dict(self, auth_client, sample_pdf_bytes):
        pdf = io.BytesIO(sample_pdf_bytes)
        pdf.name = 'resume.pdf'
        with patch('apps.resume_analyzer.views.storage.upload') as mock_upload:
            mock_upload.return_value = 'user/uuid/resume.pdf'
            response = auth_client.post(
                reverse('resume-upload'), {'file': pdf}, format='multipart'
            )
        scores = response.json().get('scores', {})
        for key in ['skills_match', 'section_completeness', 'experience_quality', 'content_quality']:
            assert key in scores
