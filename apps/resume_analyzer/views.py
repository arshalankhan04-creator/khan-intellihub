"""
Views for the resume_analyzer app.

Endpoints:
  POST   /api/v1/resumes/upload/          → ResumeUploadView
  GET    /api/v1/resumes/                 → ResumeListView
  DELETE /api/v1/resumes/{resume_id}/     → ResumeDeleteView
"""

import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ResumeRecord
from .serializers import ResumeUploadSerializer, ResumeListItemSerializer
from . import storage
from .storage import StorageError
from .pipeline.parser import parse as parse_resume, ParseError

logger = logging.getLogger(__name__)

# Pagination defaults (Req 7.1, 7.2)
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 50


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

class ResumeUploadView(APIView):
    """
    POST /api/v1/resumes/upload/

    Accepts a PDF file (multipart/form-data) with an optional job_description.
    Pipeline runs synchronously:
      1. Validate file (size + magic bytes)
      2. Upload to Supabase Storage
      3. Parse PDF → extract text + detect sections
      4. Save parsed_data to ResumeRecord, set status=PARSED

    Responses:
      202 — parsed successfully  {resume_id, status: "PARSED", parsed_data}
      400 — missing file field
      413 — file exceeds 5 MB
      415 — file is not a PDF
      422 — file uploaded but text could not be extracted (PARSE_FAILED)
      500 — Supabase Storage upload failed
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ResumeUploadSerializer(data=request.data)

        if not serializer.is_valid():
            error_code, http_status = _resolve_upload_error(serializer.errors)
            message = _upload_error_message(error_code)
            return Response(
                {'error': message, 'code': error_code},
                status=http_status,
            )

        file = serializer.validated_data['file']
        job_description = serializer.validated_data.get('job_description', None)

        # Read file bytes once — used for both storage upload and parsing
        file_bytes = file.read()
        filename = file.name

        # ── Step 1: Create the DB record to get a UUID for the storage path ──
        record = ResumeRecord.objects.create(
            user=request.user,
            original_filename=filename,
            storage_path='',
            status=ResumeRecord.STATUS_PENDING,
            job_description=job_description or None,
        )

        # ── Step 2: Upload to Supabase Storage ────────────────────────────
        try:
            storage_path = storage.upload(
                user_id=str(request.user.id),
                resume_id=str(record.id),
                filename=filename,
                file_bytes=file_bytes,
            )
        except StorageError as exc:
            record.delete()
            logger.error("Storage upload failed for user %s: %s", request.user.id, exc)
            return Response(
                {'error': 'File storage failed. Please try again.', 'code': 'INTERNAL_ERROR'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        record.storage_path = storage_path
        record.save(update_fields=['storage_path'])

        # ── Step 3: Parse the PDF ─────────────────────────────────────────
        try:
            parsed_data = parse_resume(file_bytes, filename)
        except ParseError as exc:
            record.status = ResumeRecord.STATUS_PARSE_FAILED
            record.error_reason = str(exc)
            record.save(update_fields=['status', 'error_reason', 'updated_at'])
            return Response(
                {'error': str(exc), 'code': 'PROCESSING_FAILED'},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        # ── Step 4: Persist parsed data ───────────────────────────────────
        record.parsed_data = parsed_data
        record.status = ResumeRecord.STATUS_PARSED
        record.save(update_fields=['parsed_data', 'status', 'updated_at'])

        return Response(
            {
                'resume_id': str(record.id),
                'status': record.status,
                'parsed_data': parsed_data,
            },
            status=status.HTTP_202_ACCEPTED,
        )


# ---------------------------------------------------------------------------
# History list
# ---------------------------------------------------------------------------

class ResumeListView(APIView):
    """
    GET /api/v1/resumes/?page=1&page_size=10

    Returns a paginated list of the authenticated user's resume records,
    ordered by upload_timestamp DESC (newest first).

    Responses:
      200 — {total_count, page, page_size, results: [...]}
      400 — invalid query parameters
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # ── Parse and validate query params ──────────────────────────────
        try:
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', DEFAULT_PAGE_SIZE))
        except (ValueError, TypeError):
            return Response(
                {'error': 'page and page_size must be integers.', 'code': 'VALIDATION_ERROR'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if page < 1 or page_size < 1 or page_size > MAX_PAGE_SIZE:
            return Response(
                {
                    'error': (
                        f'page must be ≥ 1 and page_size must be between 1 and {MAX_PAGE_SIZE}.'
                    ),
                    'code': 'VALIDATION_ERROR',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Query ─────────────────────────────────────────────────────────
        queryset = ResumeRecord.objects.filter(user=request.user)
        total_count = queryset.count()

        # Slice for the requested page
        offset = (page - 1) * page_size
        records = queryset[offset: offset + page_size]

        serializer = ResumeListItemSerializer(records, many=True)

        return Response(
            {
                'total_count': total_count,
                'page': page,
                'page_size': page_size,
                'results': serializer.data,
            },
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

class ResumeResultsView(APIView):
    """
    GET /api/v1/resumes/{resume_id}/results/

    Returns the current state of a resume record.

    Milestone 3 behaviour:
      - PARSED     → 200 with full parsed_data
      - PENDING    → 202 (still processing)
      - PARSE_FAILED → 422 with error_reason
      - COMPLETED / SCORED → 200 (will be enriched in M4/M5)

    Responses:
      200 — record data
      202 — still processing
      401 — not authenticated
      403 — not the owner
      404 — resume_id not found
      422 — pipeline failed
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, resume_id):
        try:
            record = ResumeRecord.objects.get(id=resume_id)
        except ResumeRecord.DoesNotExist:
            return Response(
                {'error': 'Resume not found.', 'code': 'NOT_FOUND'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if record.user_id != request.user.id:
            return Response(
                {'error': 'You do not have permission to view this resume.', 'code': 'FORBIDDEN'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Still processing
        if record.status == ResumeRecord.STATUS_PENDING:
            return Response(
                {'status': record.status, 'retry_after': 5},
                status=status.HTTP_202_ACCEPTED,
            )

        # Pipeline failed
        if record.status in (
            ResumeRecord.STATUS_PARSE_FAILED,
            ResumeRecord.STATUS_SCORE_FAILED,
            ResumeRecord.STATUS_FEEDBACK_FAILED,
        ):
            return Response(
                {'error': record.error_reason or 'Processing failed.', 'code': 'PROCESSING_FAILED'},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        # Parsed / Scored / Completed — return whatever is available
        return Response(
            {
                'resume_id': str(record.id),
                'status': record.status,
                'original_filename': record.original_filename,
                'upload_timestamp': record.upload_timestamp,
                'parsed_data': record.parsed_data,
                'ats_score': record.ats_score,
                'feedback_report': record.feedback_report,
            },
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

class ResumeDeleteView(APIView):
    """
    DELETE /api/v1/resumes/{resume_id}/

    Deletes the ResumeRecord from PostgreSQL and the file from Supabase Storage.
    Storage must succeed before the DB row is removed (Req 8.1).

    Responses:
      204 — deleted successfully
      403 — the record belongs to a different user
      404 — resume_id does not exist
      500 — Supabase Storage delete failed (DB row is retained)
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request, resume_id):
        # ── Look up the record ─────────────────────────────────────────────
        try:
            record = ResumeRecord.objects.get(id=resume_id)
        except ResumeRecord.DoesNotExist:
            return Response(
                {'error': 'Resume not found.', 'code': 'NOT_FOUND'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # ── Ownership check ───────────────────────────────────────────────
        if record.user_id != request.user.id:
            return Response(
                {'error': 'You do not have permission to delete this resume.', 'code': 'FORBIDDEN'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # ── Delete from Supabase Storage first ───────────────────────────
        # If storage deletion fails, we keep the DB row (data stays consistent)
        if record.storage_path:
            try:
                storage.delete(record.storage_path)
            except StorageError as exc:
                logger.error(
                    "Storage delete failed for record %s: %s", resume_id, exc
                )
                return Response(
                    {
                        'error': 'Failed to delete the file from storage.',
                        'code': 'INTERNAL_ERROR',
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        # ── Remove DB row ─────────────────────────────────────────────────
        record.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_upload_error(errors: dict):
    """
    Map a ResumeUploadSerializer error dict to (error_code, http_status).
    The serializer embeds the error code as the message string for file errors.
    """
    file_errors = errors.get('file', [])
    for err in file_errors:
        code = str(err)
        if code == 'FILE_TOO_LARGE':
            return 'FILE_TOO_LARGE', status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        if code == 'UNSUPPORTED_MEDIA_TYPE':
            return 'UNSUPPORTED_MEDIA_TYPE', status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    return 'VALIDATION_ERROR', status.HTTP_400_BAD_REQUEST


def _upload_error_message(code: str) -> str:
    messages = {
        'FILE_TOO_LARGE': 'File size must not exceed 5 MB.',
        'UNSUPPORTED_MEDIA_TYPE': 'Only PDF files are accepted.',
        'VALIDATION_ERROR': 'A valid file is required.',
    }
    return messages.get(code, 'Invalid request.')
