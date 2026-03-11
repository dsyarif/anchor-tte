"""
core.py — PDF processing logic (no UI dependency)
Used by both the Streamlit web app and can be imported elsewhere.
"""

import io
import fitz  # PyMuPDF


def inject_anchors_bytes(pdf_bytes: bytes, anchors: list[dict]) -> tuple[bool, str, bytes]:
    """
    Scan ALL pages and inject each anchor below EVERY occurrence of its
    target text found anywhere in the document.

    anchors = list of dict:
        {
          "target"   : str,    # text to search (scanned on all pages)
          "anchor"   : str,    # text to insert below each match
          "offset_x" : float,  # horizontal shift from match rect.x0
          "offset_y" : float,  # vertical shift from match rect.y1
          "width"    : float,  # box width (0 = use match width)
        }

    Returns (ok: bool, message: str, output_bytes: bytes)
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        return False, f"Gagal buka PDF: {e}", b""

    total_injected = 0
    anchor_hits: dict[str, set] = {}   # anchor_text -> set of page numbers (1-based)

    for page_num in range(len(doc)):
        page = doc[page_num]

        for a in anchors:
            target = a.get("target", "").strip()
            anchor = a.get("anchor", "").strip()
            if not target or not anchor:
                continue

            rects = page.search_for(target)
            if not rects:
                continue

            ox = float(a.get("offset_x", 0))
            oy = float(a.get("offset_y", 45))

            for r in rects:
                w   = float(a.get("width", 0)) or (r.x1 - r.x0)
                box = fitz.Rect(r.x0 + ox, r.y1 + oy,
                                r.x0 + ox + w, r.y1 + oy + 20)
                page.insert_textbox(
                    box, anchor,
                    align=fitz.TEXT_ALIGN_CENTER,
                    fontsize=10,
                )
                total_injected += 1
                anchor_hits.setdefault(anchor, set()).add(page_num + 1)

    if total_injected == 0:
        doc.close()
        return False, "Teks target tidak ditemukan di seluruh halaman", b""

    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    buf.seek(0)

    summary_parts = [
        f"{anc}→hal{sorted(pages)}"
        for anc, pages in anchor_hits.items()
    ]
    msg = f"{total_injected} inject | " + "  ".join(summary_parts)
    return True, msg, buf.read()


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
