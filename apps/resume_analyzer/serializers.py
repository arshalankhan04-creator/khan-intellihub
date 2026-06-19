"""
Serializers for the resume_analyzer app.

ResumeUploadSerializer   — validates an incoming upload request
ResumeListItemSerializer — serializes one record for the history list
"""

from rest_framework import serializers

from .models import ResumeRecord

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_MIME_TYPES = {'application/pdf'}


# ---------------------------------------------------------------------------
# Upload serializer
# ---------------------------------------------------------------------------

class ResumeUploadSerializer(serializers.Serializer):
    """
    Validates a multipart/form-data upload request.

    Fields:
      file            (required) — the resume file
      job_description (optional) — plain text job description
    """

    file = serializers.FileField()
    job_description = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=10000,
    )

    def validate_file(self, file):
        # ── 1. Size check ──────────────────────────────────────────────────
        if file.size > MAX_FILE_SIZE_BYTES:
            raise serializers.ValidationError(
                'FILE_TOO_LARGE',
                code='FILE_TOO_LARGE',
            )

        # ── 2. MIME type check from binary content ─────────────────────────
        # Read the first 8 bytes to sniff the magic number.
        # PDF files always start with %PDF  (hex: 25 50 44 46)
        header = file.read(8)
        file.seek(0)  # reset so the view can re-read the full file

        if not header.startswith(b'%PDF'):
            raise serializers.ValidationError(
                'UNSUPPORTED_MEDIA_TYPE',
                code='UNSUPPORTED_MEDIA_TYPE',
            )

        return file


# ---------------------------------------------------------------------------
# History list serializer
# ---------------------------------------------------------------------------

class ResumeListItemSerializer(serializers.ModelSerializer):
    """
    Serializes a ResumeRecord for the paginated history list.
    Exposes only the fields the spec requires (Req 7.4).
    """

    resume_id = serializers.UUIDField(source='id', read_only=True)

    class Meta:
        model = ResumeRecord
        fields = [
            'resume_id',
            'original_filename',
            'upload_timestamp',
            'status',
            'ats_score',
        ]
