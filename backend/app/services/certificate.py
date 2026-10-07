from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph
from reportlab.pdfgen import canvas
from xml.sax.saxutils import escape

PAGE_W, PAGE_H = landscape(A4)

class CertificateGenerator:
    """Single predefined certificate design required by the assignment."""

    def generate(self, output_path: Path, *, certificate_title: str, event_name: str, issuer_name: str, issue_date: str, recipient_name: str, designation: str | None, organization: str | None, certificate_code: str) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        c = canvas.Canvas(str(output_path), pagesize=(PAGE_W, PAGE_H))
        c.setTitle(certificate_title)

        c.setFillColor(colors.HexColor("#F7F9FC"))
        c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        c.setStrokeColor(colors.HexColor("#17324D"))
        c.setLineWidth(5)
        c.rect(10 * mm, 10 * mm, PAGE_W - 20 * mm, PAGE_H - 20 * mm, fill=0, stroke=1)
        c.setStrokeColor(colors.HexColor("#C8A951"))
        c.setLineWidth(1.5)
        c.rect(16 * mm, 16 * mm, PAGE_W - 32 * mm, PAGE_H - 32 * mm, fill=0, stroke=1)

        c.setFillColor(colors.HexColor("#C8A951"))
        for x, y in [(25, PAGE_H/mm-25), (PAGE_W/mm-25, PAGE_H/mm-25), (25, 25), (PAGE_W/mm-25, 25)]:
            c.circle(x * mm, y * mm, 4 * mm, fill=1, stroke=0)

        title_style = ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=27, leading=31, textColor=colors.HexColor("#17324D"), alignment=TA_CENTER)
        subtitle_style = ParagraphStyle("subtitle", fontName="Helvetica", fontSize=11, leading=15, textColor=colors.HexColor("#556575"), alignment=TA_CENTER)
        name_style = ParagraphStyle("name", fontName="Helvetica-Bold", fontSize=28, leading=34, textColor=colors.HexColor("#111827"), alignment=TA_CENTER)

        title_para = Paragraph(escape(certificate_title.upper()), title_style)
        title_para.wrapOn(c, PAGE_W - 70 * mm, 40 * mm)
        title_para.drawOn(c, 35 * mm, PAGE_H - 70 * mm)

        line = Paragraph("This certificate is proudly presented to", subtitle_style)
        line.wrapOn(c, PAGE_W - 70 * mm, 20 * mm)
        line.drawOn(c, 35 * mm, PAGE_H - 86 * mm)

        name_para = Paragraph(escape(recipient_name), name_style)
        name_para.wrapOn(c, PAGE_W - 80 * mm, 40 * mm)
        name_para.drawOn(c, 40 * mm, PAGE_H - 125 * mm)

        c.setStrokeColor(colors.HexColor("#C8A951"))
        c.setLineWidth(1)
        c.line(PAGE_W / 2 - 52 * mm, PAGE_H - 130 * mm, PAGE_W / 2 + 52 * mm, PAGE_H - 130 * mm)

        details = escape(event_name)
        if designation:
            details += f" · {escape(designation)}"
        if organization:
            details += f" · {escape(organization)}"
        detail_para = Paragraph(details, subtitle_style)
        detail_para.wrapOn(c, PAGE_W - 60 * mm, 30 * mm)
        detail_para.drawOn(c, 30 * mm, PAGE_H - 150 * mm)

        issuer_para = Paragraph(f"Issued by <b>{escape(issuer_name)}</b> · {escape(issue_date)}", subtitle_style)
        issuer_para.wrapOn(c, PAGE_W - 60 * mm, 30 * mm)
        issuer_para.drawOn(c, 30 * mm, 38 * mm)

        code_style = ParagraphStyle("code", fontName="Helvetica", fontSize=8.5, textColor=colors.HexColor("#6B7280"), alignment=TA_CENTER)
        code_para = Paragraph(f"Certificate ID: {escape(certificate_code)}", code_style)
        code_para.wrapOn(c, PAGE_W - 80 * mm, 20 * mm)
        code_para.drawOn(c, 40 * mm, 24 * mm)
        c.showPage()
        c.save()
