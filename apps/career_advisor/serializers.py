from rest_framework import serializers
from .models import CareerAdvisorRecord
from apps.resume_analyzer.models import ResumeRecord

class CareerAdvisorRequestSerializer(serializers.Serializer):
    resume_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    target_role = serializers.CharField(max_length=255, required=False, default="Software Engineer")
    location = serializers.CharField(max_length=255, required=False, default="United States")
    skills = serializers.ListField(child=serializers.CharField(max_length=255), required=False, default=list)

    def validate(self, attrs):
        resume_id = attrs.get('resume_id')
        skills = attrs.get('skills')

        if not resume_id:
            if not skills or len(skills) == 0:
                raise serializers.ValidationError(
                    {"skills": "You must provide at least one skill when not using a resume."}
                )
        else:
            user = self.context['request'].user
            try:
                resume = ResumeRecord.objects.get(id=resume_id, user=user)
            except ResumeRecord.DoesNotExist:
                raise serializers.ValidationError(
                    {"resume_id": "Resume record not found or does not belong to you."}
                )
            if resume.status != ResumeRecord.STATUS_COMPLETED:
                raise serializers.ValidationError(
                    {"resume_id": "Resume is still processing or parsing/scoring failed."}
                )
            
        return attrs


class CareerAdvisorRecordSerializer(serializers.ModelSerializer):
    resume_filename = serializers.SerializerMethodField()

    class Meta:
        model = CareerAdvisorRecord
        fields = [
            'id',
            'resume_record',
            'resume_filename',
            'target_role',
            'location',
            'career_paths',
            'salary_insights',
            'recommended_jobs',
            'action_plan',
            'created_at'
        ]
        read_only_fields = ['id', 'resume_filename', 'created_at']

    def get_resume_filename(self, obj):
        if obj.resume_record:
            return obj.resume_record.original_filename
        return None
