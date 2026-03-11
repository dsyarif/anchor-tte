"""
core.py — PDF processing logic (no UI dependency)
Used by both the Streamlit web app and can be imported elsewhere.
"""

import io
import fitz  # PyMuPDF


def inject_anchors_bytes(pdf_bytes: bytes, anchors: list[dict]) -> tuple[bool, str, bytes]:
    """
    Inject anchor texts into the last page of a PDF given as bytes.

    anchors = list of dict:
        {
          "target"   : str,    # text to search on the last page
          "anchor"   : str,    # text to insert below it
          "offset_x" : float,  # horizontal shift from target rect.x0
          "offset_y" : float,  # vertical shift from target rect.y1
          "width"    : float,  # box width (0 = use target width)
        }

    Returns (ok: bool, message: str, output_bytes: bytes)
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        return False, f"Gagal buka PDF: {e}", b""

    page     = doc[-1]
    injected = 0

    for a in anchors:
        target = a.get("target", "").strip()
        anchor = a.get("anchor", "").strip()
        if not target or not anchor:
            continue

        rects = page.search_for(target)
        if not rects:
            continue

        r  = rects[0]
        ox = float(a.get("offset_x", 0))
        oy = float(a.get("offset_y", 45))
        w  = float(a.get("width", 0)) or (r.x1 - r.x0)

        box = fitz.Rect(r.x0 + ox, r.y1 + oy,
                        r.x0 + ox + w, r.y1 + oy + 20)
        page.insert_textbox(
            box, anchor,
            align=fitz.TEXT_ALIGN_CENTER,
            fontsize=10,
        )
        injected += 1

    if injected == 0:
        doc.close()
        return False, "Teks target tidak ditemukan", b""

    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    buf.seek(0)
    return True, f"{injected} anchor disisipkan", buf.read()


def merge_pdf_bytes(pdf_bytes_list: list[bytes]) -> bytes:
    """
    Merge a list of PDF byte strings into a single PDF.
    Returns merged PDF as bytes.
    """
    merged = fitz.open()
    for pb in pdf_bytes_list:
        src = fitz.open(stream=pb, filetype="pdf")
        merged.insert_pdf(src)
        src.close()
    buf = io.BytesIO()
    merged.save(buf)
    merged.close()
    buf.seek(0)
    return buf.read()
