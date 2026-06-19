"""
Production settings stub.
Inherits from base; tighten security for live deployment here.
"""

from .base import *  # noqa: F401, F403
from decouple import config

DEBUG = False

# ALLOWED_HOSTS and CORS_ALLOWED_ORIGINS are already read from env vars in base.py

# Force HTTPS
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
