"""
Development settings.
Inherits everything from base and enables debug mode.
"""

from .base import *  # noqa: F401, F403

DEBUG = True

# In development, allow all hosts for convenience
ALLOWED_HOSTS = ['*']

# Show full error detail in DRF responses during development
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (  # noqa: F405
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',
)
