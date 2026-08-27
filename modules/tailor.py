"""
Tailors the candidate's real profile data to a specific job — reordering,
re-weighting, and rephrasing what's already true, never inventing new
experience, skills, or claims. Also drafts a cover letter.
"""
from modules.gemini_client import generate_json, generate_text

TAILORED_CV_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "skills_to_highlight": {"type": "array", "items": {"type": "string"}},
        "experience": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "company": {"type": "string"},
                    "location": {"type": "string"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "bullets": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
    },
    "required": ["summary", "skills_to_highlight", "experience"],
}

CV_SYSTEM_INSTRUCTION = (
    "You tailor a real candidate CV to a specific job posting. Non-negotiable guardrails:\n"
    "1. NEVER invent employers, titles, dates, skills, tools, or achievements that "
    "aren't in the candidate's profile data. Every factual claim must trace to the source.\n"
    "2. No invented numbers. Never generate or upgrade a quantification unless that exact figure "
    "is in the source.\n"
    "3. No invented skills or tools. If the JD asks for a skill not in the profile, do not add it.\n"
    "4. You MAY reorder, re-prioritize, and rephrase existing bullets to "
    "surface the most relevant experience first and mirror the job's "
    "terminology where honestly applicable (synonym-swap toward JD).\n"
    "5. Keep the same factual content — this is reframing, not fabrication.\n"
    "6. Do not include custom sections, stick strictly to the schema structure."
)

COVER_LETTER_SYSTEM_INSTRUCTION = (
    "You write concise, specific cover letters (250-350 words, 3-4 short paragraphs) grounded "
    "only in the candidate's real profile data and the job's stated requirements.\n"
    "1. Opens with the specific role and company by name — never a generic opener.\n"
    "2. References 1-2 concrete, true things from the candidate's background that map directly "
    "to the role's stated needs.\n"
    "3. No filler phrases (if a sentence would survive find-and-replace into a cover letter for "
    "a totally different job unchanged, cut it).\n"
    "4. Matches the tone signal from the JD without inventing personality traits.\n"
    "5. No generic filler, no invented achievements. "
    "Write the cover letter body (no address block, no salutation, no signature — just the body paragraphs)."
)


def tailor_cv(profile: dict, job_analysis: dict, feedback: dict = None) -> dict:
    prompt = (
        f"Candidate profile:\n{profile}\n\n"
        f"Target job:\n{job_analysis}\n\n"
    )
    if feedback:
        prompt += (
            f"PREVIOUS ATTEMPT FAILED VERIFICATION. Please fix these issues:\n"
            f"Unsupported claims: {feedback.get('unsupported_claims', [])}\n"
            f"Missing keywords: {feedback.get('missing_keywords', [])}\n"
            f"ATS issues: {feedback.get('ats_issues', [])}\n\n"
        )
    prompt += "Produce a tailored version of this candidate's CV content for this specific role, following the ground rules."
    return generate_json(prompt, TAILORED_CV_SCHEMA, system_instruction=CV_SYSTEM_INSTRUCTION)


def draft_cover_letter(profile: dict, job_analysis: dict, feedback: dict = None) -> str:
    prompt = (
        f"Candidate profile:\n{profile}\n\n"
        f"Target job:\n{job_analysis}\n\n"
    )
    if feedback:
        prompt += (
            f"PREVIOUS ATTEMPT FAILED VERIFICATION. Please fix these issues:\n"
            f"Unsupported claims: {feedback.get('unsupported_claims', [])}\n"
            f"Missing keywords: {feedback.get('missing_keywords', [])}\n"
            f"ATS issues: {feedback.get('ats_issues', [])}\n\n"
        )
    prompt += "Write the cover letter body (no address block, no salutation, no signature — just the body paragraphs)."
    return generate_text(prompt, system_instruction=COVER_LETTER_SYSTEM_INSTRUCTION, temperature=0.5)

VERIFICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "unsupported_claims": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List any sentence/phrase not traceable to the source profile"
        },
        "missing_keywords": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Must-have skills from the JD that aren't reflected anywhere honestly"
        },
        "ats_issues": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Any formatting/structure concerns (e.g., non-standard sections, custom bullets)"
        },
        "overall_pass": {
            "type": "boolean",
            "description": "True if no unsupported claims and no critical ATS issues"
        }
    },
    "required": ["unsupported_claims", "missing_keywords", "ats_issues", "overall_pass"]
}

VERIFICATION_SYSTEM_INSTRUCTION = (
    "You are a strict compliance auditor. Your ONLY job is to verify that the generated CV "
    "and Cover Letter strictly adhere to the source candidate profile, without inventing ANY "
    "facts, numbers, skills, or achievements. Also ensure ATS-friendly formatting (standard sections). "
    "Return the structured verification verdict."
)

def verify_artifacts(profile: dict, job_analysis: dict, tailored_cv: dict, cover_letter_body: str) -> dict:
    prompt = (
        f"Original Candidate Profile:\n{profile}\n\n"
        f"Target Job Description Analysis:\n{job_analysis}\n\n"
        f"Generated Tailored CV:\n{tailored_cv}\n\n"
        f"Generated Cover Letter Body:\n{cover_letter_body}\n\n"
        "Audit these generated artifacts against the Original Candidate Profile. "
        "List any unsupported_claims (hallucinations), missing_keywords (from JD must-haves), "
        "and ats_issues. Set overall_pass to true ONLY if there are 0 unsupported claims and 0 critical ATS issues."
    )
    return generate_json(prompt, VERIFICATION_SCHEMA, system_instruction=VERIFICATION_SYSTEM_INSTRUCTION, temperature=0.0)
