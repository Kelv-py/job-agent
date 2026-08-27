"""
Turns raw scraped job-posting text into structured requirements Gemini
can use later to tailor the CV and cover letter.
"""
from modules.gemini_client import generate_json

JOB_SCHEMA = {
    "type": "object",
    "properties": {
        "company": {"type": "string"},
        "role_title": {"type": "string"},
        "location": {"type": "string"},
        "seniority_level": {"type": "string"},
        "must_have_skills": {"type": "array", "items": {"type": "string"}},
        "nice_to_have_skills": {"type": "array", "items": {"type": "string"}},
        "key_responsibilities": {"type": "array", "items": {"type": "string"}},
        "company_values_or_culture_signals": {
            "type": "array", "items": {"type": "string"}
        },
        "keywords_for_ats": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["company", "role_title", "must_have_skills", "key_responsibilities"],
}

SYSTEM_INSTRUCTION = (
    "You extract structured information from job postings. Be precise and "
    "only include what is actually stated or strongly implied in the text. "
    "Do not invent requirements."
)


def analyze_job_posting(raw_text: str) -> dict:
    prompt = f"Extract structured job details from this posting:\n\n{raw_text[:15000]}"
    return generate_json(prompt, JOB_SCHEMA, system_instruction=SYSTEM_INSTRUCTION)
