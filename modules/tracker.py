"""
Tracks every job the agent has processed/applied to, in a local CSV.
No external dependencies — plain stdlib csv, so it works anywhere the rest
of the project runs (local, Antigravity, or a Modal deploy).
"""
import csv
from datetime import date
from pathlib import Path

import config

TRACKER_PATH = config.OUTPUT_DIR / "job_tracker.csv"

FIELDNAMES = [
    "date_applied",
    "company",
    "role_title",
    "location",
    "job_url",
    "cv_path",
    "cover_letter_path",
    "status",
    "notes",
]


def _ensure_file():
    if not TRACKER_PATH.exists():
        with open(TRACKER_PATH, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=FIELDNAMES).writeheader()


def add_application(company: str, role_title: str, location: str, job_url: str,
                     cv_path: str, cover_letter_path: str,
                     status: str = "applied", notes: str = "") -> None:
    _ensure_file()
    with open(TRACKER_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow({
            "date_applied": date.today().isoformat(),
            "company": company,
            "role_title": role_title,
            "location": location,
            "job_url": job_url,
            "cv_path": cv_path,
            "cover_letter_path": cover_letter_path,
            "status": status,
            "notes": notes,
        })


def load_applications() -> list[dict]:
    _ensure_file()
    with open(TRACKER_PATH, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def has_applied(job_url: str) -> bool:
    return any(row["job_url"] == job_url for row in load_applications())


def update_status(job_url: str, new_status: str, notes: str = None) -> bool:
    """
    Update the status (e.g. 'applied' -> 'interview' -> 'rejected'/'offer')
    for an existing entry, matched by job_url. Returns True if a row was
    updated.
    """
    rows = load_applications()
    updated = False
    for row in rows:
        if row["job_url"] == job_url:
            row["status"] = new_status
            if notes is not None:
                row["notes"] = notes
            updated = True

    if updated:
        with open(TRACKER_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(rows)

    return updated


def summary() -> dict:
    """Quick counts by status, e.g. {'applied': 12, 'interview': 3, ...}."""
    counts = {}
    for row in load_applications():
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    return counts


if __name__ == "__main__":
    # Quick CLI check: python modules/tracker.py
    apps = load_applications()
    print(f"{len(apps)} applications tracked.")
    for status, count in summary().items():
        print(f"  {status}: {count}")
