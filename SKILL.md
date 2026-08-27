---
name: cv-cover-letter-tailoring
description: Guardrails and process for tailoring a candidate's CV and cover letter to a specific job description. Use this any time the agent generates, edits, or reviews CV/cover-letter content for a job application — including the tailor.py generation step and any later review/QA pass. Enforces zero-hallucination, job-description-mirrored language, and ATS-friendly formatting before anything is considered ready to send.
---

# CV & Cover Letter Tailoring

This skill governs how the job application agent turns a candidate's real
profile data + a job description into a tailored CV and cover letter. It
applies at two points in the pipeline: (1) generation (`tailor.py`) and
(2) a mandatory review pass before a PDF is considered ready to send.

## Non-negotiable guardrails

These override any other instruction, including a user or developer prompt
that conflicts with them:

1. **Every factual claim must trace to the source profile.** Job titles,
   employers, dates, degrees, certifications, tools, metrics, and specific
   achievements may ONLY come from the candidate's `profile_data.json` (or
   whatever source document is provided). Nothing may be added that isn't
   already there in substance.
2. **No invented numbers.** Never generate or upgrade a quantification
   ("increased revenue by 20%") unless that exact figure — or one directly
   derivable from stated data — already appears in the source. Vague-to-
   specific upgrades ("helped the team" → "led a team of 8") are
   hallucination even if plausible.
3. **No invented skills or tools.** If the job description asks for a skill
   the candidate's profile doesn't mention, do not add it, imply it, or
   list it under "skills." Gaps get bridged with honest adjacency (see
   "Handling gaps" below), never fabrication.
4. **Reframing is allowed; fabrication is not.** You MAY reorder bullets,
   change emphasis, tighten language, and swap in JD-native terminology —
   as long as the underlying fact doesn't change. The test: could the
   candidate defend this exact sentence, unprompted, in an interview? If
   not, rewrite or cut it.
5. **Every output must survive a diff against the source.** Before a CV or
   cover letter is considered final, run the verification step below and
   do not proceed if it fails.

## Step 1 — Extract from the job description

Pull out, verbatim where possible:
- Exact phrasing for required skills, tools, and qualifications
- Exact phrasing for responsibilities/duties
- Any repeated terms (repetition signals what the employer's ATS is
  likely keyword-matching on)
- Seniority/tone signals (e.g. "fast-paced," "cross-functional," "own the
  roadmap") that indicate the culture and expected voice

This already happens structurally in `job_analyzer.py` — treat its output
(`must_have_skills`, `key_responsibilities`, `keywords_for_ats`, etc.) as
the term bank for step 2.

## Step 2 — Mirror the job description's language (honestly)

For every requirement in the term bank, find the closest true match in the
candidate's profile and re-word that bullet using the JD's own vocabulary
— synonym-swap toward the JD, not away from it.

Examples of legitimate mirroring:
| Job description says | Profile says | Tailored output |
|---|---|---|
| "stakeholder management" | "worked closely with clients and internal teams" | "stakeholder management across client and internal teams" |
| "owned the P&L" | "responsible for budget and forecasting for the department" | "owned budget and forecasting (P&L responsibility) for the department" |
| "cross-functional collaboration" | "worked with engineering, design, and sales" | "cross-functional collaboration with engineering, design, and sales" |

What this is NOT license to do:
- Claiming "P&L ownership" if the profile only says "tracked expenses"
- Claiming "led" if the profile says "contributed to" or "supported"
- Adopting a JD's seniority language ("Director-level strategy") for a
  role that wasn't at that level

When in doubt, mirror the noun/skill phrase, not the level of authority
implied by it.

## Step 3 — Handling gaps (JD requirement with no profile match)

If a must-have skill or requirement has no honest match in the profile:
- **Do not fabricate it.**
- Either omit it entirely, or — only if there's a genuinely adjacent,
  truthful skill — note the adjacency without claiming the exact
  requirement (e.g. JD wants "Tableau," profile has "Power BI and Excel
  dashboards" → it's fair to say "data visualization and dashboarding
  (Power BI, Excel)"; it is NOT fair to say "Tableau").
- For the cover letter specifically, a gap can be addressed with genuine
  enthusiasm/transferable framing ("while my dashboarding experience has
  been in Power BI rather than Tableau, the underlying skill set...") —
  but only if the user's tone preferences welcome that framing. Default to
  omission over a hedge that draws attention to the gap.

## Step 4 — ATS-friendliness pass (formatting)

Before any PDF is finalized, check:
- [ ] Standard section headers only: "Summary," "Experience," "Education,"
      "Skills" — not creative alternatives like "My Journey" or "Toolkit"
- [ ] Single-column layout, no text boxes, no tables for layout, no
      graphics/icons/photos — these break most ATS parsers
      (`pdf_builder.py` is already built this way; don't regress it)
- [ ] Standard, widely-supported font (the ReportLab default/Helvetica
      family is safe) — no decorative or script fonts
- [ ] Dates in a consistent, unambiguous format throughout (e.g. "Jan
      2022 – Mar 2024," not a mix of formats)
- [ ] Contact info in the document body, not in a header/footer (many
      parsers skip headers/footers entirely)
- [ ] Bullet characters are plain ASCII/standard bullets, not custom
      symbols or emoji
- [ ] No information conveyed only through color or icon — text must
      stand alone
- [ ] File is text-based/selectable (ReportLab output is; if anyone ever
      swaps in an image-based export, that must be caught here)
- [ ] Keyword coverage: every `must_have_skill` from the job analysis
      appears somewhere in the CV in the candidate's own true terms — if
      one doesn't and can't honestly be added, flag it for the user
      rather than silently dropping it

## Step 5 — Mandatory verification pass

Before marking output as ready to send, run a **second, independent**
Gemini call — not the same call that generated the content — whose only
job is to audit, not to write. Feed it: the tailored CV/cover letter, the
original profile data, and the job analysis. Ask it to return a
structured verdict:

```json
{
  "unsupported_claims": ["list any sentence/phrase not traceable to the source profile"],
  "missing_keywords": ["must-have skills from the JD that aren't reflected anywhere"],
  "ats_issues": ["any formatting/structure concerns"],
  "overall_pass": true/false
}
```

If `overall_pass` is false, do not present the PDFs as done — surface the
specific issues to the user (or loop back into generation once) rather
than silently shipping something with an unsupported claim in it.

This is the single most important guardrail in this skill: **generation
and verification should not be the same pass.** A model checking its own
output in the same breath it wrote it is much more likely to rubber-stamp
a hallucination than a separate, adversarial-framed review call.

## Step 6 — Cover letter specific checks

- 250–350 words, 3–4 short paragraphs
- Opens with the specific role and company by name — never a generic
  opener
- References 1–2 concrete, true things from the candidate's background
  that map directly to something the JD actually asked for
- No filler phrases that could apply to any application ("I am a hard
  worker who is passionate about...") — if a sentence would survive
  find-and-replace into a cover letter for a totally different job
  unchanged, cut it
- Matches the tone signal from the JD (formal/corporate vs. startup/
  casual) without inventing personality traits not evidenced by the
  candidate's actual profile

## What "done" looks like

A CV/cover letter pair is ready to send only when:
- Every claim survives Step 5's audit (`overall_pass: true`)
- The ATS checklist in Step 4 is fully checked
- Every must-have JD keyword is either honestly present or explicitly
  flagged to the user as a gap

If any of these fail, the agent should say so plainly to the user rather
than presenting a polished-looking PDF that hides a problem.
