# Job Application Agent

Researches a job posting, tailors your CV + cover letter to it, and outputs
ready-to-send PDFs.

## Setup

```bash
pip install -r requirements.txt
playwright install chromium

cp .env.example .env          # then paste in your GEMINI_API_KEY
cp profile/profile_template.json profile/profile_data.json
```

Now fill in `profile/profile_data.json` with your real CV content, LinkedIn
URL, and contact details. **This file stays local — it's your source of
truth and should never be committed to a public repo** (it's already in
`.gitignore` below).

Add a `.gitignore`:
```
.env
profile/profile_data.json
output/
```

## Run

Direct job URL:
```bash
python main.py --url "https://company.com/careers/job/123"
```

Search mode (opens a browser, searches, lets you pick a result):
```bash
python main.py --search "financial analyst" --location "Nairobi"
```

Output lands in `output/` as `CV_<company>_<role>.pdf` and
`CoverLetter_<company>_<role>.pdf`. Every run also logs a row in
`output/job_tracker.csv` (company, role, location, URL, PDF paths, status,
date). Running the same job URL again asks before reprocessing.

Check on your pipeline any time:
```bash
python modules/tracker.py
```

Update a status once you hear back (e.g. after an interview or rejection):
```python
from modules import tracker
tracker.update_status("https://company.com/careers/job/123", "interview")
```

## Using this in Antigravity

Open this folder as your workspace. Because everything is modular
(`browser_research.py`, `job_analyzer.py`, `tailor.py`, `pdf_builder.py`),
you can ask the Antigravity agent to work on one file at a time — e.g.
"improve the CV PDF layout in pdf_builder.py" or "make search_job_listings
also check company careers pages directly" — without it needing to
re-reason about the whole pipeline each time. Antigravity's own browser
tool can also be used interactively to test a scraper against a real job
page before you lock in the Playwright selectors.

## Design notes / things worth tightening as you go

- **Truthfulness guardrail**: `tailor.py`'s system instructions explicitly
  forbid inventing experience — it can only reorder/reword what's in your
  real profile. Worth spot-checking outputs against your actual CV
  periodically, especially numbers.
- **Scraping scope**: `browser_research.py` works generically against public
  job pages. Avoid pointing it at anything behind a login (e.g. don't
  automate your personal LinkedIn session) — use LinkedIn's own apply flow
  for those, or feed the agent a job description you've copied yourself.
  For company career sites (Greenhouse, Lever, Workday), check if they
  expose a public JSON API before scraping — often faster and more robust.
- **Model choice**: currently `gemini-3-pro` for the reasoning/tailoring
  calls in `config.py`. Swap to `gemini-3.5-flash` if you want speed/cost
  over quality, or run both — flash for job_analyzer's mostly-extractive
  task, pro for tailor.py's actual writing.
- **PDF styling**: `pdf_builder.py` is intentionally plain/ATS-friendly
  right now (no columns, no graphics) so it parses well through applicant
  tracking systems. Ask Antigravity to add a styled variant once the
  content pipeline works.
