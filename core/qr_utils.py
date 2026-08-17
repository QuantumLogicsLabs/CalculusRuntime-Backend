"""
QR code generation utilities (Dev 3 scope).

Pure-Python via `segno` — no Pillow/native image deps required.
Produces both an inline SVG string and a base64 PNG data URI so the
frontend (Dev 1) can render either without extra processing.
"""

import base64
import io
import segno


def generate_qr_svg(data: str, scale: int = 6) -> str:
    """Return a standalone <svg>...</svg> string encoding `data`."""
    qr = segno.make(data, error="m")
    buf = io.BytesIO()
    qr.save(buf, kind="svg", xmldecl=False, svgns=True, scale=scale)
    return buf.getvalue().decode("utf-8")


def generate_qr_png_bytes(data: str, scale: int = 6) -> bytes:
    """Return raw PNG bytes encoding `data` (for embedding in PDFs, etc.)."""
    qr = segno.make(data, error="m")
    buf = io.BytesIO()
    qr.save(buf, kind="png", scale=scale)
    return buf.getvalue()


def generate_qr_png_base64(data: str, scale: int = 6) -> str:
    """Return a base64-encoded PNG (no data: prefix) encoding `data`."""
    return base64.b64encode(generate_qr_png_bytes(data, scale=scale)).decode("ascii")


def generate_qr_png_data_uri(data: str, scale: int = 6) -> str:
    """Return a ready-to-use `data:image/png;base64,...` string for <img src>."""
    return f"data:image/png;base64,{generate_qr_png_base64(data, scale=scale)}"
