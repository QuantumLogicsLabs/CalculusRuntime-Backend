"""
PDF certificate rendering (Dev 3 scope — Team Epsilon).

Pure-Python via fpdf2 (no C build tools required, unlike some PDF libs —
this matters because this backend gets deployed to small containers).
"""

import io
from datetime import datetime, timezone

from fpdf import FPDF

# Brand colors (approx. match the CalcVoyager amber/cream theme)
GOLD = (200, 150, 62)
INK = (28, 23, 18)
MUTED = (122, 114, 103)
CREAM = (250, 246, 237)
LINE = (224, 214, 200)

ORG_NAME = "CalcVoyager"
MENTOR_NAME = "Course Mentor, CalcVoyager"


def _fmt_date(issued_at_epoch: int) -> str:
    dt = datetime.fromtimestamp(issued_at_epoch, tz=timezone.utc)
    return dt.strftime("%B %d, %Y")


def build_certificate_pdf(
    *,
    full_name: str,
    course_title: str,
    cert_id: str,
    issued_at_epoch: int,
    verify_url: str,
    qr_png_bytes: bytes,
    score: int | None = None,
    total: int | None = None,
) -> bytes:
    """Render a single-page landscape PDF certificate. Returns raw PDF bytes."""
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(False)
    pdf.add_page()
    pdf.set_fill_color(*CREAM)
    pdf.rect(0, 0, 297, 210, style="F")

    # Decorative border
    pdf.set_draw_color(*GOLD)
    pdf.set_line_width(1.2)
    pdf.rect(8, 8, 281, 194)
    pdf.set_line_width(0.3)
    pdf.rect(11, 11, 275, 188)

    # Org "logo" (text mark — swap for pdf.image(logo_path, ...) if a real
    # logo file is added later, e.g. assets/logo.png)
    pdf.set_xy(0, 20)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(*GOLD)
    pdf.cell(297, 10, ORG_NAME.upper(), align="C")

    pdf.set_xy(0, 34)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*MUTED)
    pdf.cell(297, 6, "MULTIVARIABLE TOOLS", align="C")

    # Title
    pdf.set_xy(0, 55)
    pdf.set_font("Helvetica", "B", 30)
    pdf.set_text_color(*INK)
    pdf.cell(297, 14, "Certificate of Completion", align="C")

    pdf.set_xy(0, 72)
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(*MUTED)
    pdf.cell(297, 8, "This certifies that", align="C")

    # Full name
    pdf.set_xy(0, 84)
    pdf.set_font("Helvetica", "B", 26)
    pdf.set_text_color(*GOLD)
    pdf.cell(297, 14, full_name, align="C")

    # Course line
    pdf.set_xy(0, 102)
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(*MUTED)
    pdf.cell(297, 8, "has successfully completed", align="C")

    pdf.set_xy(20, 112)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*INK)
    pdf.cell(257, 10, course_title, align="C")

    if score is not None and total:
        pct = round(score / total * 100)
        pdf.set_xy(0, 124)
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(*MUTED)
        pdf.cell(
            297, 6,
            f"Certification quiz score: {score}/{total} ({pct}%)",
            align="C",
        )

    # Date + Certificate ID
    pdf.set_xy(0, 138)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*MUTED)
    pdf.cell(297, 6, f"Issued on {_fmt_date(issued_at_epoch)}", align="C")
    pdf.set_xy(0, 144)
    pdf.cell(297, 6, f"Certificate ID: {cert_id}", align="C")

    # Mentor signature (bottom-left)
    pdf.set_xy(30, 168)
    pdf.set_font("Helvetica", "I", 16)
    pdf.set_text_color(*INK)
    pdf.cell(90, 8, "Q. L. Mentor", align="L")
    pdf.set_draw_color(*LINE)
    pdf.line(30, 178, 120, 178)
    pdf.set_xy(30, 180)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*MUTED)
    pdf.cell(90, 6, MENTOR_NAME, align="L")

    # QR code (bottom-right)
    qr_size = 32
    qr_x = 297 - 30 - qr_size
    qr_y = 158
    pdf.image(io.BytesIO(qr_png_bytes), x=qr_x, y=qr_y, w=qr_size, h=qr_size)
    pdf.set_xy(qr_x - 20, qr_y + qr_size + 2)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*MUTED)
    pdf.cell(qr_size + 40, 5, "Scan to verify", align="C")

    out = pdf.output()
    return bytes(out)
