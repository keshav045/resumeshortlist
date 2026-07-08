"""
report_generator.py
-------------------
Generates a downloadable PDF analysis report for a screened resume.
Uses ReportLab, a pure-Python PDF library.
"""

from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT


# Resolve reports directory relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "dataset" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def generate_pdf_report(resume, job_title: str) -> str:
    """
    Creates a PDF report for a screened resume.

    Args:
        resume:    SQLAlchemy Resume model instance
        job_title: title of the job description used for matching

    Returns:
        File path to the generated PDF
    """
    filename = f"report_{resume.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    filepath = REPORTS_DIR / filename

    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'Title', parent=styles['Title'],
        fontSize=22, textColor=colors.HexColor('#1a1a2e'),
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'Subtitle', parent=styles['Normal'],
        fontSize=12, textColor=colors.HexColor('#666666'),
        spaceAfter=20, alignment=TA_CENTER
    )
    heading_style = ParagraphStyle(
        'Heading', parent=styles['Heading2'],
        fontSize=13, textColor=colors.HexColor('#2d6a4f'),
        spaceBefore=16, spaceAfter=6
    )
    body_style = ParagraphStyle(
        'Body', parent=styles['Normal'],
        fontSize=10, textColor=colors.HexColor('#333333'),
        leading=16
    )

    # ── Build content ──────────────────────────────────────────────────────────
    content = []

    # Header
    content.append(Paragraph("Resume Analysis Report", title_style))
    content.append(Paragraph(
        f"Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}",
        subtitle_style
    ))
    content.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e0e0e0')))
    content.append(Spacer(1, 0.4*cm))

    # Candidate info table
    score_color = (
        colors.HexColor('#27ae60') if resume.match_score >= 70
        else colors.HexColor('#f39c12') if resume.match_score >= 40
        else colors.HexColor('#e74c3c')
    )

    info_data = [
        ["Candidate",    resume.candidate_name],
        ["Resume File",  resume.filename],
        ["Job Applied",  job_title or "N/A"],
        ["Match Score",  f"{resume.match_score:.1f}%"],
        ["Uploaded",     str(resume.uploaded_at)[:16] if resume.uploaded_at else "N/A"],
    ]
    info_table = Table(info_data, colWidths=[4*cm, 13*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5')),
        ('FONTNAME',   (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME',   (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE',   (0, 0), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#fafafa')]),
        ('GRID',       (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
        ('PADDING',    (0, 0), (-1, -1), 8),
        ('TEXTCOLOR',  (1, 3), (1, 3), score_color),   # color the score cell
        ('FONTNAME',   (1, 3), (1, 3), 'Helvetica-Bold'),
    ]))
    content.append(info_table)
    content.append(Spacer(1, 0.5*cm))

    # Resume summary
    content.append(Paragraph("Resume Summary", heading_style))
    content.append(Paragraph(resume.summary or "No summary available.", body_style))

    # Matching skills
    content.append(Paragraph("Matching Skills", heading_style))
    matching = resume.matching_skills or "None identified"
    content.append(Paragraph(matching, body_style))

    # Missing skills
    content.append(Paragraph("Missing Skills (from Job Description)", heading_style))
    missing = resume.missing_skills or "None — full coverage!"
    content.append(Paragraph(missing, body_style))

    # Recommendation
    content.append(Spacer(1, 0.4*cm))
    content.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e0e0e0')))
    content.append(Spacer(1, 0.3*cm))

    if resume.match_score >= 70:
        rec = "Strong match — recommended for interview."
        rec_color = colors.HexColor('#27ae60')
    elif resume.match_score >= 40:
        rec = "Partial match — consider for initial screening."
        rec_color = colors.HexColor('#f39c12')
    else:
        rec = "Weak match — may not meet minimum requirements."
        rec_color = colors.HexColor('#e74c3c')

    rec_style = ParagraphStyle('Rec', parent=body_style, textColor=rec_color,
                               fontSize=11, fontName='Helvetica-Bold')
    content.append(Paragraph(f"Recommendation: {rec}", rec_style))

    # Footer
    content.append(Spacer(1, 1*cm))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'],
                                  fontSize=8, textColor=colors.HexColor('#aaaaaa'),
                                  alignment=TA_CENTER)
    content.append(Paragraph("Generated by AI Resume Screening System", footer_style))

    doc.build(content)
    return str(filepath)
