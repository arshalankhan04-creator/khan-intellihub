"""
Initial migration — creates the resume_records table.
"""

import uuid
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        # Must run after the custom user model is created
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ResumeRecord',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4,
                    editable=False,
                    primary_key=True,
                    serialize=False,
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='resumes',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('original_filename', models.CharField(max_length=255)),
                ('storage_path', models.TextField()),
                ('status', models.CharField(
                    choices=[
                        ('PENDING', 'Pending'),
                        ('PARSED', 'Parsed'),
                        ('SCORED', 'Scored'),
                        ('COMPLETED', 'Completed'),
                        ('PARSE_FAILED', 'Parse Failed'),
                        ('SCORE_FAILED', 'Score Failed'),
                        ('FEEDBACK_FAILED', 'Feedback Failed'),
                    ],
                    default='PENDING',
                    max_length=20,
                )),
                ('job_description', models.TextField(blank=True, null=True)),
                ('parsed_data', models.JSONField(blank=True, null=True)),
                ('ats_score', models.SmallIntegerField(blank=True, null=True)),
                ('keyword_score', models.DecimalField(
                    blank=True, decimal_places=2, max_digits=5, null=True
                )),
                ('formatting_score', models.DecimalField(
                    blank=True, decimal_places=2, max_digits=5, null=True
                )),
                ('section_score', models.DecimalField(
                    blank=True, decimal_places=2, max_digits=5, null=True
                )),
                ('content_score', models.DecimalField(
                    blank=True, decimal_places=2, max_digits=5, null=True
                )),
                ('feedback_report', models.JSONField(blank=True, null=True)),
                ('error_reason', models.TextField(blank=True, null=True)),
                ('upload_timestamp', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'resume_records',
                'ordering': ['-upload_timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='resumerecord',
            index=models.Index(
                fields=['user', '-upload_timestamp'],
                name='idx_resume_records_user_ts',
            ),
        ),
    ]
