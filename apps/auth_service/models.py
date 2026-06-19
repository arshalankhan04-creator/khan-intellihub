"""
CustomUser model.

Replaces Django's default integer PK with a UUID and uses email
as the login identifier instead of username (Req 1.1, 9.1, 10.1).
"""

import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import CustomUserManager


class CustomUser(AbstractUser):
    """
    Drop-in replacement for Django's built-in User.

    Key differences from the default:
    - UUID primary key (avoids exposing sequential IDs in the API)
    - email is the login field (USERNAME_FIELD = 'email')
    - username field is removed entirely
    - Password is stored as PBKDF2-SHA256 (Django default, satisfies Req 10.1)
    """

    # UUID primary key — no sequential integer leak in the API
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    # Email is the unique login identifier
    email = models.EmailField(unique=True)

    # Remove username — we don't need it
    username = None

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # email + password are enough for createsuperuser

    objects = CustomUserManager()

    class Meta:
        db_table = 'auth_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email
