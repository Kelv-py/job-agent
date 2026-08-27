"""
End-to-end pipeline:
  1. Load your profile data
  2. Get a job posting (by direct URL, or via search)
  3. Analyze the posting into structured requirements (Gemini)
  4. Tailor CV content + draft a cover letter (Gemini)
  5. Render both as PDFs

Usage:
  python main.py --url "https://company.com/careers/job/123"
  python main.py --search "AI developer" --location "Remote"
"""
import argparse
import json
import re

import config
from modules import browser_research, job_analyzer, tailor, pdf_builder, tracker


def slugify(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()


def load_profile() -> dict:
    if not config.PROFILE_PATH.exists():
        raise FileNotFoundError(
            f"No profile found at {config.PROFILE_PATH}. Copy "
            "profile/profile_template.json to profile/profile_data.json "
            "and fill in your real details."
        )
    with open(config.PROFILE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("candidate", data)


def run_for_url(job_url: str, profile: dict):
    if tracker.has_applied(job_url):
        print(f"Already tracked as applied: {job_url}")
        choice = input("Process again anyway? (y/n): ")
        if choice.lower() != "y":
            return

    print(f"[1/4] Fetching job posting: {job_url}")
    raw_text = browser_research.fetch_job_posting(job_url)

    print("[2/4] Analyzing requirements...")
    job_analysis = job_analyzer.analyze_job_posting(raw_text)
    print(f"      -> {job_analysis['role_title']} at {job_analysis['company']}")

    print("[3/4] Tailoring CV + drafting cover letter (with verification pass)...")
    tailored_cv = tailor.tailor_cv(profile, job_analysis)
    cover_letter_body = tailor.draft_cover_letter(profile, job_analysis)

    print("      -> Verifying generated artifacts against source profile...")
    verdict = tailor.verify_artifacts(profile, job_analysis, tailored_cv, cover_letter_body)
    
    if not verdict.get("overall_pass", False):
        print("      -> Verification failed. Attempting one retry to fix issues...")
        print(f"         Issues: {verdict}")
        tailored_cv = tailor.tailor_cv(profile, job_analysis, feedback=verdict)
        cover_letter_body = tailor.draft_cover_letter(profile, job_analysis, feedback=verdict)
        
        print("      -> Re-verifying...")
        verdict = tailor.verify_artifacts(profile, job_analysis, tailored_cv, cover_letter_body)
        
        if not verdict.get("overall_pass", False):
            print("      -> [WARNING] Artifacts still failed verification!")
            print(f"         Issues: {verdict}")
            choice = input("         Do you want to proceed rendering these PDFs anyway? (y/n): ")
            if choice.lower() != 'y':
                print("Aborting.")
                return
    else:
        print("      -> Verification passed!")

    print("[4/4] Rendering PDFs...")
    slug = slugify(f"{job_analysis['company']}_{job_analysis['role_title']}")
    cv_path = config.OUTPUT_DIR / f"CV_{slug}.pdf"
    cl_path = config.OUTPUT_DIR / f"CoverLetter_{slug}.pdf"

    pdf_builder.build_cv_pdf(
        contact=profile["contact"],
        tailored=tailored_cv,
        education=profile.get("education", []),
        output_path=str(cv_path),
        certifications=profile.get("certifications", []),
    )
    pdf_builder.build_cover_letter_pdf(
        contact=profile["contact"],
        company=job_analysis["company"],
        role_title=job_analysis["role_title"],
        body_text=cover_letter_body,
        output_path=str(cl_path),
    )

    tracker.add_application(
        company=job_analysis["company"],
        role_title=job_analysis["role_title"],
        location=job_analysis.get("location", ""),
        job_url=job_url,
        cv_path=str(cv_path),
        cover_letter_path=str(cl_path),
    )

    print(f"Done:\n  {cv_path}\n  {cl_path}\n  Logged in {tracker.TRACKER_PATH}")


def run_search(query: str, location: str, profile: dict):
    print(f"Searching for: {query} {location}")
    results = browser_research.search_job_listings(query, location)
    if not results:
        print("No results found.")
        return

    for i, r in enumerate(results):
        print(f"  [{i}] {r['title']}\n      {r['url']}")

    choice = input("Pick a result number to process (or 'q' to quit): ")
    if choice.lower() == "q":
        return
    run_for_url(results[int(choice)]["url"], profile)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", help="Direct job posting URL")
    parser.add_argument("--search", help="Job title / keywords to search for")
    parser.add_argument("--location", default="", help="Location filter for --search")
    args = parser.parse_args()

    profile_data = load_profile()

    if args.url:
        run_for_url(args.url, profile_data)
    elif args.search:
        run_search(args.search, args.location, profile_data)
    else:
        parser.error("Provide either --url or --search")
