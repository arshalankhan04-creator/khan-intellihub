import json
import logging
from django.conf import settings
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.exceptions import PermissionDenied

from .models import CareerAdvisorRecord
from .serializers import CareerAdvisorRequestSerializer, CareerAdvisorRecordSerializer
from apps.resume_analyzer.models import ResumeRecord

logger = logging.getLogger(__name__)

# Pagination defaults
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 50

# ---------------------------------------------------------------------------
# Job Fetching Helpers
# ---------------------------------------------------------------------------

def _get_mock_job_listings(target_role: str, location: str) -> list:
    """Generate realistic mock job listings for development fallback."""
    return [
        {
            'title': f"Senior {target_role}",
            'company': "Acme Global Solutions",
            'location': location,
            'salary_min': 110000,
            'salary_max': 150000,
            'description': f"We are looking for a Senior {target_role} to join our engineering department. Experience with cloud platforms is a plus.",
            'redirect_url': "https://example.com/jobs/senior-role"
        },
        {
            'title': f"Lead {target_role}",
            'company': "Stark Enterprises",
            'location': location,
            'salary_min': 130000,
            'salary_max': 180000,
            'description': f"Join us as a Lead {target_role} and drive key technical architectural decisions. You will collaborate with product and engineering teams.",
            'redirect_url': "https://example.com/jobs/lead-role"
        },
        {
            'title': f"{target_role}",
            'company': "Cyberdyne Systems",
            'location': location,
            'salary_min': 85000,
            'salary_max': 120000,
            'description': f"Seeking a motivated {target_role} to develop high-performance services and refine existing codebase workflows.",
            'redirect_url': "https://example.com/jobs/standard-role"
        }
    ]

def _fetch_job_listings(target_role: str, location: str) -> list:
    """Fetch jobs from Adzuna or fall back to mock jobs."""
    app_id = getattr(settings, 'ADZUNA_APP_ID', None)
    app_key = getattr(settings, 'ADZUNA_APP_KEY', None)
    
    if not app_id or not app_key:
        logger.info("Adzuna API credentials missing. Using mock jobs.")
        return _get_mock_job_listings(target_role, location)
        
    try:
        import requests
        # Use US endpoint as default country search
        url = "https://api.adzuna.com/v1/api/jobs/us/search/1"
        params = {
            'app_id': app_id,
            'app_key': app_key,
            'results_per_page': 5,
            'what': target_role,
            'where': location,
            'content-type': 'application/json'
        }
        response = requests.get(url, params=params, timeout=8)
        if response.status_code == 200:
            data = response.json()
            jobs = []
            for item in data.get('results', []):
                jobs.append({
                    'title': item.get('title'),
                    'company': item.get('company', {}).get('display_name', 'Unknown Company'),
                    'location': item.get('location', {}).get('display_name', location),
                    'salary_min': item.get('salary_min'),
                    'salary_max': item.get('salary_max'),
                    'description': item.get('description'),
                    'redirect_url': item.get('redirect_url')
                })
            return jobs
        else:
            logger.warning("Adzuna API returned status code %s. Using fallback.", response.status_code)
    except Exception as exc:
        logger.warning("Adzuna API call failed. Using fallback. Error: %s", exc)
        
    return _get_mock_job_listings(target_role, location)


# ---------------------------------------------------------------------------
# Advice Generation Helpers
# ---------------------------------------------------------------------------

def _generate_career_advice_with_gemini(
    resume_record: ResumeRecord | None,
    skills: list[str] | None,
    job_listings: list,
    target_role: str,
    location: str,
    api_key: str
) -> dict:
    """Use Gemini model to generate structured career advice."""
    import google.generativeai as genai
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    if resume_record:
        resume_text = resume_record.parsed_data.get('raw_text', '') if resume_record.parsed_data else ''
        skills_text = resume_record.parsed_data.get('sections', {}).get('skills', '') if resume_record.parsed_data else ''
        ats_context = f"""
- ATS Score: {resume_record.ats_score or "N/A"}
- Category Scores (Skills, Sections, Experience, Content): {resume_record.keyword_score}, {resume_record.section_score}, {resume_record.formatting_score}, {resume_record.content_score}
- Raw Resume Text: {resume_text[:2000]}  # Truncated to avoid context bloat
- Current Stated Skills: {skills_text}
"""
    else:
        skills_text = ", ".join(skills or [])
        ats_context = f"""
- Mode: Totally Separate from Resume (Self-input Profile)
- Current Stated Skills: {skills_text}
- ATS Score / Category Scores: Not Applicable / N/A
"""
    
    prompt = f"""
You are an expert career advisor. Based on the user's career profile (either from their resume analysis or manually input skills) and the current job market context, generate a structured career path dashboard.

USER TARGET PROFILE:
- Target Job Role: {target_role}
- Desired Location: {location}

RESUME / ATS ANALYSIS CONTEXT:
{ats_context}

LIVE JOB MARKET CONTEXT (Adzuna Listings):
{json.dumps(job_listings, indent=2)}

INSTRUCTIONS:
Analyze the data and return a valid JSON object.
Your JSON object MUST contain exactly the following structure:
{{
    "career_paths": [
        {{
            "name": "<career path name, e.g. Senior Software Engineer, Engineering Manager>",
            "match_score": <integer from 0 to 100>,
            "match_level": "strong_match" | "partial_match" | "low_match",
            "description": "<why this path is suitable for the user>",
            "required_skills": [<list of key required skills>]
        }}
    ],
    "salary_insights": {{
        "current_estimated": "<estimated salary range based on user's current experience level in location>",
        "target_role_range": "<expected salary range for the target role in location>",
        "top_paying_skills": [<list of 3 high-paying skills relevant to the role>]
    }},
    "recommended_jobs": [
        {{
            "title": "<job title>",
            "company": "<company name>",
            "location": "<location>",
            "match_score": <integer from 0 to 100 representing how well the user fits this specific job description>,
            "apply_url": "<redirect_url from Adzuna>"
        }}
    ],
    "action_plan": [
        "<detailed, prioritized action step 1 to help the user transition or upskill>",
        "<detailed, prioritized action step 2>",
        "<detailed, prioritized action step 3>"
    ]
}}

Return ONLY the JSON object. Do not include markdown formatting like ```json or any other text before/after the JSON.
"""

    response = model.generate_content(prompt)
    text = response.text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    
    return json.loads(text)


def _generate_career_advice_static(
    resume_record: ResumeRecord | None,
    skills: list[str] | None,
    job_listings: list,
    target_role: str,
    location: str
) -> dict:
    """Generate career advice using local rule-based pipeline engines."""
    from apps.career_advisor.pipeline import (
        career_path_engine,
        skill_gap_engine,
        role_engine,
        next_steps_engine
    )

    # 1. Build career profile
    if resume_record:
        skills_text = (resume_record.parsed_data or {}).get('sections', {}).get('skills') or ''
        skills_list = [s.strip() for s in skills_text.split(',') if s.strip()]
        missing = resume_record.feedback_report.get('missing_skills', []) if resume_record.feedback_report else []
        ats_score = resume_record.ats_score or 0
        mode = 'resume_based'
    else:
        skills_list = skills or []
        missing = []
        ats_score = 0
        mode = 'manual'
        
    if not skills_list:
        skills_list = ['Python', 'SQL']
        
    career_profile = {
        'skills': skills_list,
        'interests': [target_role],
        'career_goals': f"Become a successful {target_role} in {location}",
        'missing_skills': missing,
        'mode': mode,
        'ats_score': ats_score,
        'experience_level': 'mid'
    }

    # 2. Run rule-based engines
    try:
        recommended_paths = career_path_engine.recommend(career_profile)
        gap = skill_gap_engine.analyse(career_profile, recommended_paths)
        next_steps = next_steps_engine.generate(career_profile)
    except Exception as exc:
        logger.warning("Local career advisor engines failed: %s", exc)
        recommended_paths = [{'name': 'Software Engineer', 'match_score': 80, 'match_level': 'strong_match', 'description': 'Matches your coding profile.', 'required_skills': ['Python', 'SQL']}]
        next_steps = [{'priority': 'high', 'action': 'Update skills section.', 'category': 'skill_building'}]

    # 3. Format outputs
    paths_out = []
    for path in recommended_paths[:3]:
        paths_out.append({
            'name': path['name'],
            'match_score': path['match_score'],
            'match_level': path.get('match_level', 'strong_match'),
            'description': path.get('description', f"Analytical match for {path['name']}"),
            'required_skills': path.get('required_skills', [])
        })

    jobs_out = []
    for job in job_listings:
        jobs_out.append({
            'title': job['title'],
            'company': job['company'],
            'location': job['location'],
            'match_score': 85,
            'apply_url': job['redirect_url']
        })

    salary_insights = {
        'current_estimated': "$80,000 - $110,000",
        'target_role_range': "$95,000 - $140,000",
        'top_paying_skills': ['Django', 'AWS', 'System Design']
    }

    action_plan = [step['action'] for step in next_steps]

    return {
        'career_paths': paths_out,
        'salary_insights': salary_insights,
        'recommended_jobs': jobs_out,
        'action_plan': action_plan
    }


# ---------------------------------------------------------------------------
# API Views
# ---------------------------------------------------------------------------

class CareerAdvisorGenerateView(APIView):
    """
    POST /api/v1/career-advisor/generate/
    
    Inputs:
      - resume_id (UUID, optional)
      - target_role (str, optional)
      - location (str, optional)
      - skills (list of str, optional)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CareerAdvisorRequestSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid request parameters.', 'code': 'VALIDATION_ERROR', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        resume_id = serializer.validated_data.get('resume_id')
        target_role = serializer.validated_data.get('target_role', 'Software Engineer')
        location = serializer.validated_data.get('location', 'United States')
        skills = serializer.validated_data.get('skills', [])

        resume_record = ResumeRecord.objects.get(id=resume_id) if resume_id else None

        # Step 1: Fetch job market listings
        job_listings = _fetch_job_listings(target_role, location)

        # Step 2: Generate Career Advice (Gemini with Fallback)
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        advice_data = None
        
        if api_key:
            try:
                advice_data = _generate_career_advice_with_gemini(
                    resume_record=resume_record,
                    skills=skills,
                    job_listings=job_listings,
                    target_role=target_role,
                    location=location,
                    api_key=api_key
                )
            except Exception as exc:
                logger.warning("Gemini career advice generation failed, falling back: %s", exc)
                
        if not advice_data:
            advice_data = _generate_career_advice_static(
                resume_record=resume_record,
                skills=skills,
                job_listings=job_listings,
                target_role=target_role,
                location=location
            )

        # Step 3: Save to Database
        record = CareerAdvisorRecord.objects.create(
            user=request.user,
            resume_record=resume_record,
            target_role=target_role,
            location=location,
            career_paths=advice_data.get('career_paths', []),
            salary_insights=advice_data.get('salary_insights', {}),
            recommended_jobs=advice_data.get('recommended_jobs', []),
            action_plan=advice_data.get('action_plan', [])
        )


        response_serializer = CareerAdvisorRecordSerializer(record)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class CareerAdvisorResultsView(APIView):
    """
    GET /api/v1/career-advisor/{record_id}/results/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, record_id):
        try:
            record = CareerAdvisorRecord.objects.get(id=record_id)
        except CareerAdvisorRecord.DoesNotExist:
            return Response(
                {'error': 'Career advice record not found.', 'code': 'NOT_FOUND'},
                status=status.HTTP_404_NOT_FOUND
            )

        if record.user_id != request.user.id:
            return Response(
                {'error': 'You do not have permission to view this record.', 'code': 'FORBIDDEN'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CareerAdvisorRecordSerializer(record)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, record_id):
        try:
            record = CareerAdvisorRecord.objects.get(id=record_id)
        except CareerAdvisorRecord.DoesNotExist:
            return Response(
                {'error': 'Career advice record not found.', 'code': 'NOT_FOUND'},
                status=status.HTTP_404_NOT_FOUND
            )

        if record.user_id != request.user.id:
            return Response(
                {'error': 'You do not have permission to delete this record.', 'code': 'FORBIDDEN'},
                status=status.HTTP_403_FORBIDDEN
            )

        record.delete()
        return Response({'message': 'Record deleted successfully.'}, status=status.HTTP_200_OK)


class CareerAdvisorHistoryView(APIView):
    """
    GET /api/v1/career-advisor/history/?page=1&page_size=10
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', DEFAULT_PAGE_SIZE))
        except (ValueError, TypeError):
            return Response(
                {'error': 'page and page_size must be integers.', 'code': 'VALIDATION_ERROR'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if page < 1 or page_size < 1 or page_size > MAX_PAGE_SIZE:
            return Response(
                {'error': f'page must be >= 1 and page_size must be 1 to {MAX_PAGE_SIZE}.', 'code': 'VALIDATION_ERROR'},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = CareerAdvisorRecord.objects.filter(user=request.user)
        total_count = queryset.count()

        offset = (page - 1) * page_size
        records = queryset[offset:offset + page_size]

        serializer = CareerAdvisorRecordSerializer(records, many=True)

        return Response({
            'total_count': total_count,
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        }, status=status.HTTP_200_OK)
