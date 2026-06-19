"""
Initial migration — creates the auth_user table.

Uses UUID primary key and email as the login identifier.
"""

import uuid
import django.contrib.auth.models
import django.contrib.auth.validators
import django.utils.timezone
from django.db import migrations, models

import apps.auth_service.managers


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomUser',
            fields=[
                # UUID primary key
                ('id', models.UUIDField(
                    default=uuid.uuid4,
                    editable=False,
                    primary_key=True,
                    serialize=False,
                )),
                # Password hash (PBKDF2-SHA256 by default)
                ('password', models.CharField(max_length=128, verbose_name='password')),
                # Timestamps
                ('last_login', models.DateTimeField(
                    blank=True,
                    null=True,
                    verbose_name='last login',
                )),
                ('date_joined', models.DateTimeField(
                    default=django.utils.timezone.now,
                    verbose_name='date joined',
                )),
                # Name fields (optional display names)
                ('first_name', models.CharField(
                    blank=True,
                    max_length=150,
                    verbose_name='first name',
                )),
                ('last_name', models.CharField(
                    blank=True,
                    max_length=150,
                    verbose_name='last name',
                )),
                # Login identifier
                ('email', models.EmailField(
                    max_length=254,
                    unique=True,
                    verbose_name='email address',
                )),
                # Admin / active flags
                ('is_active', models.BooleanField(
                    default=True,
                    help_text='Designates whether this user should be treated as active.',
                    verbose_name='active',
                )),
                ('is_staff', models.BooleanField(
                    default=False,
                    help_text='Designates whether the user can log into the admin site.',
                    verbose_name='staff status',
                )),
                ('is_superuser', models.BooleanField(
                    default=False,
                    help_text='Designates that this user has all permissions without explicitly assigning them.',
                    verbose_name='superuser status',
                )),
                # Many-to-many permissions (required by AbstractUser)
                ('groups', models.ManyToManyField(
                    blank=True,
                    help_text='The groups this user belongs to.',
                    related_name='user_set',
                    related_query_name='user',
                    to='auth.group',
                    verbose_name='groups',
                )),
                ('user_permissions', models.ManyToManyField(
                    blank=True,
                    help_text='Specific permissions for this user.',
                    related_name='user_set',
                    related_query_name='user',
                    to='auth.permission',
                    verbose_name='user permissions',
                )),
            ],
            options={
                'db_table': 'auth_user',
                'verbose_name': 'User',
                'verbose_name_plural': 'Users',
            },
            managers=[
                ('objects', apps.auth_service.managers.CustomUserManager()),
            ],
        ),
    ]
