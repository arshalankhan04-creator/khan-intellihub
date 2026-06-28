import uuid
from django.conf import settings
from django.db import models
from apps.resume_analyzer.models import ResumeRecord

class CareerAdvisorRecord(models.Model):
    """
    Stores career advisor queries and their generated results.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='career_advice',
    )
    resume_record = models.ForeignKey(
        ResumeRecord,
        on_delete=models.CASCADE,
        related_name='career_advice',
        null=True,
        blank=True
    )
    target_role = models.CharField(max_length=255, default="Software Engineer")
    location = models.CharField(max_length=255, default="United States")
    
    # Store JSON data representing results
    career_paths = models.JSONField(null=True, blank=True)
    salary_insights = models.JSONField(null=True, blank=True)
    recommended_jobs = models.JSONField(null=True, blank=True)
    action_plan = models.JSONField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'career_advisor_records'
        ordering = ['-created_at']

    def __str__(self):
        return f"Career Advice for {self.user.email} - {self.target_role} ({self.created_at})"
