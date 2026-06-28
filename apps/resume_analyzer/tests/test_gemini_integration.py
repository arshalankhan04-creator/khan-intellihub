import pytest
from unittest.mock import patch, MagicMock
from django.conf import settings
from apps.resume_analyzer.pipeline.preprocessor import preprocess_resume, clean_text
from apps.resume_analyzer.pipeline.scorer import score, _score_with_gemini, ScoreError

def test_clean_text():
    assert clean_text("Hello, World! 123\nNew Line") == "hello world 123 new line"
    assert clean_text("") == ""
    assert clean_text(None) == ""

def test_preprocessor_keyword_and_similarity():
    resume = "Python developer experienced in Django, PostgreSQL and REST APIs."
    jd = "Seeking a Python backend developer with Django and database experience."
    
    res = preprocess_resume(resume, jd)
    assert 'django' in res['keywords'] or 'python' in res['keywords']
    assert res['job_similarity'] is not None
    assert res['job_similarity'] > 0.0
    assert res['classified_domain'] == 'Software Engineering / IT'

def test_preprocessor_domain_classification():
    nurse_resume = "Registered Nurse clinical patient care medication administration hospital medicine nursing."
    res = preprocess_resume(nurse_resume)
    assert res['classified_domain'] == 'Healthcare / Nursing'

@patch('google.generativeai.GenerativeModel')
def test_score_with_mock_gemini(mock_model_class):
    # Mock the Gemini API response
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = """
    {
        "ats_score": 85,
        "skills_score": 90.0,
        "section_score": 80.0,
        "experience_score": 85.0,
        "content_score": 80.0,
        "missing_skills": ["Docker"],
        "strengths": ["Good resume length"],
        "weaknesses": ["Missing Docker"],
        "feedback_report": {
            "overall_summary": "Great resume.",
            "top_strengths": ["Design"],
            "top_weaknesses": ["Skills"],
            "priority_actions": [{"priority": "high", "action": "Add Docker"}],
            "section_suggestions": {
                "contact": null,
                "skills": "Add cloud tools.",
                "education": null,
                "experience": null,
                "projects": null,
                "certifications": null
            },
            "skills_suggestions": ["Add Docker"],
            "experience_suggestions": [],
            "enhancement_tips": [],
            "missing_skills": ["Docker"]
        }
    }
    """
    mock_model.generate_content.return_value = mock_response
    mock_model_class.return_value = mock_model
    
    parsed = {
        'sections': {'skills': 'Python, Django'},
        'raw_text': 'Python, Django developer.',
        'metadata': {'filename': 'test.pdf'}
    }
    
    # We patch settings.GEMINI_API_KEY so it's not None
    with patch.object(settings, 'GEMINI_API_KEY', 'fake_key'):
        # We also need to un-mock the globally mocked _score_with_gemini from conftest.py
        # Since conftest.py fixture mock_gemini_fallback mocks it, we can patch it to call the real one!
        with patch('apps.resume_analyzer.pipeline.scorer._score_with_gemini', side_effect=_score_with_gemini):
            result = score(parsed, "Software Engineer")
            
            assert result['ats_score'] == 85
            assert result['skills_score'] == 90.0
            assert result['missing_skills'] == ["Docker"]
            assert result['_gemini_feedback_report']['overall_summary'] == "Great resume."
