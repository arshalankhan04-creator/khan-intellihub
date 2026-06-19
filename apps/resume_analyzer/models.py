"""
ResumeRecord model.

Represents a single resume upload and all its associated analysis data.
One user → many resume records (1:N).
"""

import uuid
from django.conf import settings
from django.db import models


class ResumeRecord(models.Model):
    """
    Stores everything about a single resume upload:
    - the file metadata (name, storage path)
    - the pipeline status (PENDING → PARSED → SCORED → COMPLETED, or *_FAILED)
    - the analysis outputs (parsed_data, scores, feedback) filled in by later milestones

    For Milestone 2 we only populate: id, user, original_filename,
    storage_path, status, job_description, upload_timestamp, updated_at.
    All analysis fields are nullable and left empty until Milestones 3–5.
    """

    # Status choices — pipeline state machine
    STATUS_PENDING = 'PENDING'
    STATUS_PARSED = 'PARSED'
    STATUS_SCORED = 'SCORED'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_PARSE_FAILED = 'PARSE_FAILED'
    STATUS_SCORE_FAILED = 'SCORE_FAILED'
    STATUS_FEEDBACK_FAILED = 'FEEDBACK_FAILED'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PARSED, 'Parsed'),
        (STATUS_SCORED, 'Scored'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_PARSE_FAILED, 'Parse Failed'),
        (STATUS_SCORE_FAILED, 'Score Failed'),
        (STATUS_FEEDBACK_FAILED, 'Feedback Failed'),
    ]

    # -----------------------------------------------------------------------
    # Identity
    # -----------------------------------------------------------------------
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    # Owner — FK to the custom user model; cascade delete removes all
    # resume records when a user account is deleted
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resumes',
    )

    # -----------------------------------------------------------------------
    # File metadata
    # -----------------------------------------------------------------------
    original_filename = models.CharField(max_length=255)

    # Full path inside the Supabase Storage bucket
    # e.g. "a1b2c3.../d4e5f6.../resume.pdf"
    storage_path = models.TextField()

    # -----------------------------------------------------------------------
    # Pipeline state
    # -----------------------------------------------------------------------
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )

    # -----------------------------------------------------------------------
    # Optional job description supplied at upload time
    # -----------------------------------------------------------------------
    job_description = models.TextField(blank=True, null=True)

    # -----------------------------------------------------------------------
    # Analysis outputs — all nullable; populated by Milestones 3–5
    # -----------------------------------------------------------------------
    parsed_data = models.JSONField(null=True, blank=True)

    ats_score = models.SmallIntegerField(null=True, blank=True)
    keyword_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    formatting_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    section_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    content_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    feedback_report = models.JSONField(null=True, blank=True)

    # Human-readable reason set when status is *_FAILED
    error_reason = models.TextField(null=True, blank=True)

    # -----------------------------------------------------------------------
    # Timestamps
    # -----------------------------------------------------------------------
    upload_timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'resume_records'
        # Default ordering: newest uploads first
        ordering = ['-upload_timestamp']
        indexes = [
            # Speeds up paginated history queries filtered by user
            models.Index(
                fields=['user', '-upload_timestamp'],
                name='idx_resume_records_user_ts',
            ),
        ]

    def __str__(self):
        return f"{self.original_filename} ({self.status})"
