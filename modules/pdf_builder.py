"""
Renders tailored CV content and a cover letter into formatted PDFs.
Uses ReportLab (pure-Python, no system dependencies — installs cleanly on
Windows and in minimal container/deploy environments).
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
)

styles = getSampleStyleSheet()
from reportlab.lib.enums import TA_CENTER
NAME_STYLE = ParagraphStyle("Name", parent=styles["Title"], fontSize=16, fontName="Helvetica-Bold", spaceAfter=2)
SUBTITLE_STYLE = ParagraphStyle("Subtitle", parent=styles["Normal"], alignment=TA_CENTER, fontSize=11, spaceAfter=8, fontName="Helvetica-Bold", textColor="#333333")
CONTACT_STYLE = ParagraphStyle("Contact", parent=styles["Normal"], alignment=TA_CENTER, fontSize=9,
                                textColor="#444444", spaceAfter=12)
SECTION_STYLE = ParagraphStyle("Section", parent=styles["Heading2"], fontSize=12,
                                spaceBefore=14, spaceAfter=4, textColor="#1a1a1a")
BODY_STYLE = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, leading=14)
JOB_HEADER_STYLE = ParagraphStyle("JobHeader", parent=styles["Normal"], fontSize=10.5,
                                   leading=13, spaceBefore=8, fontName="Helvetica-Bold")
JOB_SUBHEADER_STYLE = ParagraphStyle("JobSub", parent=styles["Normal"], fontSize=9.5,
                                      leading=12, textColor="#555555")


def build_cv_pdf(contact: dict, tailored: dict, education: list, output_path: str, certifications: list = None):
    if certifications is None:
        certifications = []

    doc = SimpleDocTemplate(output_path, pagesize=A4,
                             topMargin=18 * mm, bottomMargin=18 * mm,
                             leftMargin=18 * mm, rightMargin=18 * mm)
    story = []

    story.append(Paragraph("KELVIN NDIRANGU", NAME_STYLE))
    story.append(Paragraph("GENAI | DEVOPS", SUBTITLE_STYLE))
    
    # Extract github correctly if it's a list
    github = contact.get("github")
    github_str = github[0] if isinstance(github, list) and github else github
    
    contact_line = " | ".join(filter(None, [
        contact.get("email"), 
        contact.get("location"),
        github_str,
        contact.get("linkedin")
    ]))
    story.append(Paragraph(contact_line, CONTACT_STYLE))

    story.append(Paragraph("<u>SUMMARY</u>", SECTION_STYLE))
    story.append(Paragraph(tailored["summary"], BODY_STYLE))

    story.append(Paragraph("<u>KEY SKILLS</u>", SECTION_STYLE))
    story.append(Paragraph(" &nbsp;|&nbsp; ".join(tailored["skills_to_highlight"]), BODY_STYLE))

    story.append(Paragraph("<u>EXPERIENCE</u>", SECTION_STYLE))
    for job in tailored["experience"]:
        header = f"{job.get('title', '')} — {job.get('company', '')}"
        subheader = f"{job.get('location', '')}   {job.get('start_date', '')} – {job.get('end_date', '')}"
        story.append(Paragraph(header, JOB_HEADER_STYLE))
        story.append(Paragraph(subheader, JOB_SUBHEADER_STYLE))
        story.append(ListFlowable(
            [ListItem(Paragraph(b, BODY_STYLE)) for b in job.get("bullets", [])],
            bulletType="bullet", start="•", leftIndent=12,
        ))

    if education or certifications:
        story.append(Paragraph("<u>EDUCATION + CERTIFICATIONS</u>", SECTION_STYLE))
        for edu in education:
            year = edu.get('year', '')
            year_str = f", {year}" if year else ""
            line = f"{edu.get('degree', '')} — {edu.get('institution', '')}{year_str}"
            story.append(Paragraph(line, BODY_STYLE))
        
        if certifications:
            story.append(Spacer(1, 2 * mm))
            story.append(ListFlowable(
                [ListItem(Paragraph(cert, BODY_STYLE)) for cert in certifications],
                bulletType="bullet", start="•", leftIndent=12,
            ))

    doc.build(story)


def build_cover_letter_pdf(contact: dict, company: str, role_title: str,
                            body_text: str, output_path: str):
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                             topMargin=25 * mm, bottomMargin=25 * mm,
                             leftMargin=25 * mm, rightMargin=25 * mm)
    story = []

    story.append(Paragraph("KELVIN NDIRANGU", NAME_STYLE))
    story.append(Paragraph("GENAI | DEVOPS", SUBTITLE_STYLE))
    
    github = contact.get("github")
    github_str = github[0] if isinstance(github, list) and github else github
    
    contact_line = " | ".join(filter(None, [
        contact.get("email"), 
        contact.get("location"),
        github_str,
        contact.get("linkedin")
    ]))
    story.append(Paragraph(contact_line, CONTACT_STYLE))
    story.append(Spacer(1, 10 * mm))

    story.append(Paragraph(f"Re: Application for {role_title} at {company}", BODY_STYLE))
    story.append(Spacer(1, 4 * mm))

    for para in body_text.split("\n\n"):
        if para.strip():
            story.append(Paragraph(para.strip(), BODY_STYLE))
            story.append(Spacer(1, 3 * mm))

    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Kind regards,", BODY_STYLE))
    story.append(Paragraph(contact.get("full_name", ""), BODY_STYLE))

    doc.build(story)
