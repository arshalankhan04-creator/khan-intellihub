"""
Root conftest.py

pytest-django uses DJANGO_SETTINGS_MODULE from pytest.ini.
"""

import pytest
from unittest.mock import patch

@pytest.fixture(autouse=True)
def mock_gemini_fallback():
    """Globally mock Gemini scorer to return None, forcing fallback to deterministic logic in tests."""
    with patch('apps.resume_analyzer.pipeline.scorer._score_with_gemini', return_value=None):
        yield

