"""
PDF TTD Injector — Web Edition
Streamlit app for injecting TTE anchors into RKA PDF documents.
"""

import io
import zipfile
import streamlit as st
import fitz  # PyMuPDF

from core import inject_anchors_bytes, merge_pdf_bytes

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="PDF Anchor TTE Injector",
    page_icon="✒️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
#  CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Dark background */
.stApp { background-color: #0F1117; color: #E8EAF0; }

/* Header */
.app-header {
    background: linear-gradient(135deg, #1A1D27 0%, #141720 100%);
    border: 1px solid #2A2D3E;
    border-radius: 12px;
    padding: 20px 28px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    gap: 16px;
}
.app-title { font-family: 'JetBrains Mono', monospace; font-size: 26px; font-weight: 700; color: #E8EAF0; margin: 0; }
.app-sub   { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #6B7280; margin: 0; }
.app-badge { background: #00C8A0; color: #0F1117; font-size: 11px; font-weight: 700;
             padding: 3px 10px; border-radius: 20px; font-family: 'JetBrains Mono', monospace; }

/* Section cards */
.section-card {
    background: #1A1D27;
    border: 1px solid #2A2D3E;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 16px;
}
.section-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.5px;
    margin-bottom: 14px;
}
.accent-green  { color: #00C8A0; }
.accent-purple { color: #6C63FF; }
.accent-amber  { color: #F59E0B; }

/* Log area */
.log-box {
    background: #111318;
    border: 1px solid #2A2D3E;
    border-radius: 8px;
    padding: 14px 16px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    max-height: 300px;
    overflow-y: auto;
    line-height: 1.7;
}
.log-ok   { color: #34D399; }
.log-err  { color: #F87171; }
.log-warn { color: #FBBF24; }
.log-info { color: #00C8A0; }
.log-dim  { color: #4B5563; }

/* Anchor table */
.anchor-table th {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #6B7280;
    font-weight: 700;
    letter-spacing: 0.5px;
}

/* Override Streamlit elements */
div[data-testid="stFileUploader"] {
    background: #1A1D27;
    border: 1px dashed #2A2D3E;
    border-radius: 8px;
}
.stTabs [data-baseweb="tab-list"] {
    background: #1A1D27;
    border-radius: 8px;
    gap: 4px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    color: #6B7280;
    border-radius: 6px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    font-weight: 700;
}
.stTabs [aria-selected="true"] {
    background: #00C8A0 !important;
    color: #0F1117 !important;
}
div[data-testid="stExpander"] {
    background: #1A1D27;
    border: 1px solid #2A2D3E;
    border-radius: 8px;
}
.stButton > button {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    border-radius: 6px;
}
.stDownloadButton > button {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    background: #00C8A0;
    color: #0F1117;
    border: none;
    border-radius: 6px;
}
.stDownloadButton > button:hover { background: #00a884; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  SESSION STATE INIT
# ─────────────────────────────────────────────
def _init_state():
    if "anchor_rows" not in st.session_state:
        st.session_state.anchor_rows = [
            {"target": "Kasubag. Perencanaan, Evaluasi dan Keuangan",
             "anchor": "${ttd_pengirim2}", "offset_x": 0, "offset_y": 45, "width": 120},
            {"target": "Penata Kelola Sistem dan Teknologi Informasi",
             "anchor": "${ttd_pengirim1}", "offset_x": 0, "offset_y": 45, "width": 120},
        ]
    if "results" not in st.session_state:
        st.session_state.results = []   # list of (filename, bytes, ok, msg)

_init_state()


# ─────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="app-header">
  <div style="font-size:36px">⬡</div>
  <div style="flex:1">
    <p class="app-title">PDF Anchor TTE Injector</p>
    <p class="app-sub">Sisipkan anchor tanda tangan elektronik ke Dokumen Anda — web edition</p>
  </div>
  <span class="app-badge">v4.0 WEB</span>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  MAIN LAYOUT  (left config | right results)
# ─────────────────────────────────────────────
col_cfg, col_res = st.columns([1.1, 0.9], gap="large")

# ══════════════════════════════════════════════
#  LEFT — CONFIGURATION
# ══════════════════════════════════════════════
with col_cfg:

    # ── 1. Upload PDF ──────────────────────────
    st.markdown('<div class="section-title accent-green">① UPLOAD FILE PDF</div>',
                unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Pilih satu atau beberapa file PDF",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded:
        st.caption(f"📎 {len(uploaded)} file dipilih: "
                   + ", ".join(f.name for f in uploaded[:5])
                   + ("…" if len(uploaded) > 5 else ""))

    st.divider()

    # ── 2. Mode TTD (tabs) ─────────────────────
    st.markdown('<div class="section-title accent-green">② MODE Anchor</div>',
                unsafe_allow_html=True)

    tab_single, tab_multi = st.tabs(["✒  Single Anchor", "✒✒  Multi Anchor"])

    # ── Single Anchor tab ──────────────────────
    with tab_single:
        st.markdown("")
        s_target = st.text_input(
            "🔍 Teks Target",
            value="Kepala Badan Kepegawaian dan Pengembangan Sumber Daya Manusia",
            key="s_target",
            help="Teks yang dicari di halaman terakhir PDF",
        )
        s_anchor = st.text_input(
            "✒️ Teks Anchor",
            value="${ttd_pengirim}",
            key="s_anchor",
            help="Teks anchor yang akan disisipkan di bawah teks target",
        )
        col_oy, col_w = st.columns(2)
        with col_oy:
            s_offset_y = st.number_input("↕ Offset Y (pt)", value=45, min_value=0,
                                         max_value=500, key="s_offset_y")
        with col_w:
            s_width = st.number_input("↔ Lebar box (0=auto)", value=0, min_value=0,
                                      max_value=1000, key="s_width")

    # ── Multi Anchor tab ───────────────────────
    with tab_multi:
        st.markdown("")

        # Column headers
        hc = st.columns([3, 2, 1, 1, 1, 0.4])
        for col, lbl in zip(hc, ["Teks Target", "Teks Anchor", "Offset X", "Offset Y", "Lebar", ""]):
            col.markdown(f"<small style='color:#6B7280;font-weight:700'>{lbl}</small>",
                         unsafe_allow_html=True)

        # Render existing rows
        to_delete = None
        for idx, row in enumerate(st.session_state.anchor_rows):
            rc = st.columns([3, 2, 1, 1, 1, 0.4])
            row["target"]   = rc[0].text_input("tgt", value=row["target"],
                                                key=f"m_tgt_{idx}", label_visibility="collapsed")
            row["anchor"]   = rc[1].text_input("anc", value=row["anchor"],
                                                key=f"m_anc_{idx}", label_visibility="collapsed")
            row["offset_x"] = rc[2].number_input("ox", value=row["offset_x"],
                                                   key=f"m_ox_{idx}", label_visibility="collapsed")
            row["offset_y"] = rc[3].number_input("oy", value=row["offset_y"],
                                                   key=f"m_oy_{idx}", label_visibility="collapsed")
            row["width"]    = rc[4].number_input("w", value=row["width"], min_value=0,
                                                   key=f"m_w_{idx}", label_visibility="collapsed")
            if rc[5].button("✕", key=f"del_{idx}"):
                to_delete = idx

        if to_delete is not None:
            st.session_state.anchor_rows.pop(to_delete)
            st.rerun()

        if st.button("＋ Tambah Baris Anchor", use_container_width=True):
            st.session_state.anchor_rows.append(
                {"target": "", "anchor": "", "offset_x": 0, "offset_y": 45, "width": 0})
            st.rerun()

    st.divider()

    # ── 3. Opsi ────────────────────────────────
    st.markdown('<div class="section-title accent-green">③ OPSI PROSES</div>',
                unsafe_allow_html=True)

    do_merge   = st.checkbox("Gabung semua output jadi 1 PDF", value=True)
    merge_name = st.text_input("Nama file merged", disabled=not do_merge)

    st.divider()

    # ── 4. Tombol Proses ───────────────────────
    run_col, _ = st.columns([1, 2])
    with run_col:
        run_clicked = st.button("▶  JALANKAN PROSES", type="primary",
                                use_container_width=True,
                                disabled=not bool(uploaded))


# ══════════════════════════════════════════════
#  PROCESS (runs when button clicked)
# ══════════════════════════════════════════════
def build_anchors(active_tab: str) -> list[dict] | None:
    """Build anchor list from UI state."""
    # Streamlit tabs don't expose which is active directly,
    # so we detect by checking if single-anchor fields are filled
    # We use a separate radio to track mode cleanly.
    # Actually we stored mode in session_state via the tab mechanism.
    # We'll pass active_tab string from caller.
    if active_tab == "single":
        tgt  = st.session_state.get("s_target", "").strip()
        anch = st.session_state.get("s_anchor", "").strip()
        oy   = st.session_state.get("s_offset_y", 45)
        w    = st.session_state.get("s_width", 0)
        if not tgt or not anch:
            return None
        return [{"target": tgt, "anchor": anch, "offset_x": 0, "offset_y": oy, "width": w}]
    else:
        rows = [r for r in st.session_state.anchor_rows
                if r["target"].strip() and r["anchor"].strip()]
        return rows if rows else None


# We track which tab is active via a hidden radio in session state
if "ttd_mode" not in st.session_state:
    st.session_state.ttd_mode = "single"

# Detect active tab from the tabs above (workaround: use a selectbox in sidebar)
with st.sidebar:
    st.markdown("### ⚙️ Mode TTD Aktif")
    st.caption("Pilih mode sesuai tab yang Anda gunakan di atas")
    st.session_state.ttd_mode = st.radio(
        "Mode TTD",
        options=["single", "multi"],
        format_func=lambda x: "✒ Single Anchor" if x == "single" else "✒✒ Multi Anchor",
        label_visibility="collapsed",
    )


if run_clicked and uploaded:
    anchors = build_anchors(st.session_state.ttd_mode)

    if not anchors:
        st.error("⚠️ Konfigurasi anchor tidak lengkap. Cek teks target dan anchor.")
    else:
        results = []
        log_lines = []

        mode_label = "Single Anchor" if len(anchors) == 1 else f"Multi Anchor ({len(anchors)} anchor)"
        log_lines.append(("info", f"MODE TTD  : {mode_label}"))
        log_lines.append(("info", f"Jumlah file: {len(uploaded)}"))
        log_lines.append(("dim",  "─" * 50))

        prog = st.progress(0, text="Memproses...")

        for i, uf in enumerate(uploaded):
            pdf_bytes = uf.read()
            ok, msg, out_bytes = inject_anchors_bytes(pdf_bytes, anchors)
            results.append((uf.name, out_bytes, ok, msg))

            if ok:
                log_lines.append(("ok",   f"  ✔  {uf.name}  [{msg}]"))
            elif "tidak" in msg.lower():
                log_lines.append(("warn", f"  ↷  {uf.name}  [{msg}]"))
            else:
                log_lines.append(("err",  f"  ✘  {uf.name}  [{msg}]"))

            prog.progress((i + 1) / len(uploaded),
                          text=f"Memproses {i+1}/{len(uploaded)}: {uf.name}")

        prog.empty()

        success = sum(1 for _, _, ok, _ in results if ok)
        skipped = sum(1 for _, _, ok, m in results if not ok and "tidak" in m.lower())
        errors  = sum(1 for _, _, ok, m in results if not ok and "tidak" not in m.lower())

        log_lines.append(("dim",  "─" * 50))
        log_lines.append(("info", f"Selesai: ✔ {success} berhasil  ↷ {skipped} dilewati  ✘ {errors} error"))

        st.session_state.results   = results
        st.session_state.log_lines = log_lines
        st.session_state.do_merge  = do_merge
        st.session_state.merge_name = merge_name
        st.session_state.anchors   = anchors


# ══════════════════════════════════════════════
#  RIGHT — RESULTS
# ══════════════════════════════════════════════
with col_res:
    st.markdown('<div class="section-title accent-green">④ HASIL & DOWNLOAD</div>',
                unsafe_allow_html=True)

    results    = st.session_state.get("results", [])
    log_lines  = st.session_state.get("log_lines", [])

    # ── Log output ────────────────────────────
    if log_lines:
        COLOR = {"ok": "#34D399", "err": "#F87171", "warn": "#FBBF24",
                 "info": "#00C8A0", "dim": "#4B5563"}
        html_lines = "".join(
            f'<div style="color:{COLOR.get(tag, "#E8EAF0")}">{line}</div>'
            for tag, line in log_lines
        )
        st.markdown(f'<div class="log-box">{html_lines}</div>', unsafe_allow_html=True)
        st.markdown("")
    else:
        st.markdown(
            '<div class="log-box"><span style="color:#4B5563">Log proses akan tampil di sini…</span></div>',
            unsafe_allow_html=True)
        st.markdown("")

    # ── Download buttons ──────────────────────
    if results:
        success_results = [(n, b) for n, b, ok, _ in results if ok]

        st.markdown('<div class="section-title accent-green" style="margin-top:16px">⑤ UNDUH FILE</div>',
                    unsafe_allow_html=True)

        # Merge download
        if st.session_state.get("do_merge") and len(success_results) > 0:
            merged_bytes = merge_pdf_bytes([b for _, b in success_results])
            mname = st.session_state.get("merge_name", "RKA_2026_TTD.pdf")
            st.download_button(
                label=f"⬇  Unduh Merged PDF ({len(success_results)} file)",
                data=merged_bytes,
                file_name=mname,
                mime="application/pdf",
                use_container_width=True,
            )
            st.markdown("")

        # ZIP of all individual files
        if success_results:
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for fname, fbytes in success_results:
                    zf.writestr(fname, fbytes)
            zip_buf.seek(0)
            st.download_button(
                label=f"⬇  Unduh Semua sebagai ZIP ({len(success_results)} file)",
                data=zip_buf.getvalue(),
                file_name="RKA_TTD_output.zip",
                mime="application/zip",
                use_container_width=True,
            )
            st.markdown("")

        # Individual downloads (collapsible)
        with st.expander(f"📄 Unduh file satu per satu ({len(success_results)} file berhasil)"):
            for fname, fbytes in success_results:
                st.download_button(
                    label=f"⬇  {fname}",
                    data=fbytes,
                    file_name=fname,
                    mime="application/pdf",
                    key=f"dl_{fname}",
                )

        # Failed files info
        failed = [(n, m) for n, _, ok, m in results if not ok]
        if failed:
            with st.expander(f"⚠️ {len(failed)} file gagal / dilewati"):
                for fname, msg in failed:
                    st.caption(f"↷  **{fname}** — {msg}")

    # ── Anchor preview ────────────────────────
    anchors = st.session_state.get("anchors")
    if anchors:
        st.divider()
        st.markdown('<div class="section-title accent-amber">ANCHOR YANG DIGUNAKAN</div>',
                    unsafe_allow_html=True)
        for i, a in enumerate(anchors, 1):
            st.markdown(
                f"`{i}.` Target: **{a['target'][:50]}{'…' if len(a['target'])>50 else ''}**  \n"
                f"&nbsp;&nbsp;&nbsp;&nbsp;Anchor: `{a['anchor']}`  |  "
                f"Offset X: `{a['offset_x']}`  |  Y: `{a['offset_y']}`  |  Lebar: `{a['width'] or 'auto'}`"
            )


# ─────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────
st.divider()
st.markdown(
    '<p style="text-align:center;font-family:JetBrains Mono,monospace;font-size:11px;color:#4B5563">'
    'PDF TTD Injector v4.0 Web  ·  BKPSDM Kota Pekalongan  ·  Powered by PyMuPDF + Streamlit'
    '</p>',
    unsafe_allow_html=True,
)
