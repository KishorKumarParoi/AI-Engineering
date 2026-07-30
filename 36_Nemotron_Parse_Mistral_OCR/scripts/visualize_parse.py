"""
Nemotron-Parse Visual Inspector
================================
Upload a PDF, call nemotron-parse for any page, and see bounding boxes drawn
on top of the page image — color-coded by element type.

Usage:
    streamlit run scripts/visualize_parse.py
"""

from __future__ import annotations

import json
import sys
from io import BytesIO
from pathlib import Path

import pymupdf as fitz
import streamlit as st
from dotenv import load_dotenv
from PIL import Image, ImageDraw

# ---------------------------------------------------------------------------
# Import helpers from the main pipeline script
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent.parent))
from nemotron_parse_pipeline import (  # noqa: E402
    call_with_retries,
    compute_zoom,
    page_to_base64_jpeg,
)

load_dotenv()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ELEMENT_COLORS: dict[str, tuple[int, int, int]] = {
    "Title":           (220,  20,  60),
    "Section-header":  (255, 140,   0),
    "Text":            ( 30, 144, 255),
    "Picture":         ( 34, 139,  34),
    "Caption":         (148,   0, 211),
    "Table":           (220, 180,   0),
    "Bibliography":    (160,  82,  45),
    "List-item":       ( 64, 224, 208),
    "Footnote":        (255, 105, 180),
    "Page-footer":     (128, 128, 128),
    "Page-header":     (169, 169, 169),
    "Unknown":         (  0,   0,   0),
}

FILL_ALPHA = 40    # overlay transparency
BORDER_WIDTH = 2


# ---------------------------------------------------------------------------
# Page rendering
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def render_page_as_pil(pdf_bytes: bytes, page_idx: int, zoom: float) -> Image.Image:
    """Rasterize a PDF page to a PIL Image using the same zoom logic as the pipeline."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[page_idx]
    mat = compute_zoom(page, zoom)
    pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
    doc.close()
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    return img


# ---------------------------------------------------------------------------
# API call + element extraction
# ---------------------------------------------------------------------------
def parse_page(
    pdf_bytes: bytes,
    page_idx: int,
    api_key: str,
    zoom: float,
    max_tokens: int,
) -> tuple[list[dict], dict]:
    """
    Call nemotron-parse for one page and return (elements, raw_response).

    Elements are dicts with keys: bbox (list[float]), text (str), type (str).
    Raises on unrecoverable API errors.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[page_idx]
    b64_image, _quality, _size = page_to_base64_jpeg(page, zoom)
    doc.close()

    raw = call_with_retries(b64_image, "image/jpeg", api_key, max_tokens)
    elements = _extract_elements(raw)
    return elements, raw


def _extract_elements(raw: dict) -> list[dict]:
    """Navigate the API response and return a flat list of element dicts."""
    try:
        tool_calls = raw["choices"][0]["message"].get("tool_calls")
        if not tool_calls:
            return []
        arguments_str = tool_calls[0]["function"]["arguments"]
        outer = json.loads(arguments_str)

        # The model sometimes double-nests the bbox list; unwrap if needed.
        if isinstance(outer, list) and len(outer) == 1 and isinstance(outer[0], list):
            items = outer[0]
        elif isinstance(outer, list):
            items = outer
        elif isinstance(outer, dict):
            # Some versions wrap in a dict with a known key
            for key in ("elements", "blocks", "content", "result"):
                if key in outer and isinstance(outer[key], list):
                    items = outer[key]
                    break
            else:
                items = [outer]
        else:
            return []

        elements = []
        for item in items:
            if not isinstance(item, dict):
                continue
            bbox = item.get("bbox") or item.get("bounding_box") or []
            text = item.get("text") or item.get("content") or item.get("markdown") or ""
            etype = item.get("type") or item.get("label") or item.get("class") or "Unknown"
            elements.append({"bbox": bbox, "text": text, "type": etype})
        return elements

    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        return []


# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------
def _normalize_bbox(bbox: list | dict) -> list[float]:
    """Convert bbox to a flat [xmin, ymin, xmax, ymax] list.

    The API sometimes returns a dict with integer or string keys
    (e.g. {0: 0.1, 1: 0.2, 2: 0.8, 3: 0.9}) instead of a list.
    """
    if isinstance(bbox, dict):
        # Try integer keys 0–3 first, then string keys "0"–"3"
        try:
            return [float(bbox[k]) for k in (0, 1, 2, 3)]
        except KeyError:
            try:
                return [float(bbox[k]) for k in ("0", "1", "2", "3")]
            except KeyError:
                return list(bbox.values())[:4]
    return [float(v) for v in bbox]


def draw_bboxes_on_image(pil_img: Image.Image, elements: list[dict]) -> Image.Image:
    """
    Overlay color-coded bounding boxes on the image.

    Bboxes are normalized [xmin, ymin, xmax, ymax] in [0, 1].
    Inverted bboxes (xmin > xmax or ymin > ymax) are silently fixed.
    Degenerate boxes (< 2px after clamp) are skipped.
    """
    img_rgba = pil_img.convert("RGBA")
    overlay = Image.new("RGBA", img_rgba.size, (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    draw_border = ImageDraw.Draw(img_rgba)

    w, h = pil_img.size

    for elem in elements:
        raw_bbox = elem.get("bbox", [])
        if not raw_bbox or len(raw_bbox) < 4:
            continue
        bbox = _normalize_bbox(raw_bbox)
        if len(bbox) < 4:
            continue

        etype = elem.get("type", "Unknown")
        rgb = ELEMENT_COLORS.get(etype, ELEMENT_COLORS["Unknown"])

        # Fix inverted bboxes
        xmin = min(bbox[0], bbox[2])
        ymin = min(bbox[1], bbox[3])
        xmax = max(bbox[0], bbox[2])
        ymax = max(bbox[1], bbox[3])

        # Denormalize
        x0 = int(xmin * w)
        y0 = int(ymin * h)
        x1 = int(xmax * w)
        y1 = int(ymax * h)

        # Clamp to image bounds
        x0 = max(0, min(x0, w - 1))
        y0 = max(0, min(y0, h - 1))
        x1 = max(0, min(x1, w - 1))
        y1 = max(0, min(y1, h - 1))

        # Skip degenerate
        if (x1 - x0) < 2 or (y1 - y0) < 2:
            continue

        fill_color = rgb + (FILL_ALPHA,)
        border_color = rgb + (255,)

        draw_overlay.rectangle([x0, y0, x1, y1], fill=fill_color)
        for i in range(BORDER_WIDTH):
            draw_border.rectangle(
                [x0 + i, y0 + i, x1 - i, y1 - i],
                outline=border_color,
            )

    result = Image.alpha_composite(img_rgba, overlay).convert("RGB")
    return result


# ---------------------------------------------------------------------------
# Elements → dataframe rows
# ---------------------------------------------------------------------------
def elements_to_rows(elements: list[dict]) -> list[dict]:
    """Convert elements to display-friendly dicts, adding an Inverted flag."""
    rows = []
    for i, elem in enumerate(elements):
        raw_bbox = elem.get("bbox", [])
        bbox = _normalize_bbox(raw_bbox) if raw_bbox else []
        inverted = False
        if len(bbox) >= 4:
            inverted = bbox[0] > bbox[2] or bbox[1] > bbox[3]
        rows.append({
            "#": i,
            "Type": elem.get("type", "Unknown"),
            "Inverted": inverted,
            "xmin": round(bbox[0], 4) if len(bbox) > 0 else None,
            "ymin": round(bbox[1], 4) if len(bbox) > 1 else None,
            "xmax": round(bbox[2], 4) if len(bbox) > 2 else None,
            "ymax": round(bbox[3], 4) if len(bbox) > 3 else None,
            "Text": (elem.get("text") or "")[:120],
        })
    return rows


# ---------------------------------------------------------------------------
# Sidebar legend
# ---------------------------------------------------------------------------
def render_legend() -> None:
    st.sidebar.markdown("### Element color legend")
    rows_html = ""
    for etype, rgb in ELEMENT_COLORS.items():
        hex_color = "#{:02x}{:02x}{:02x}".format(*rgb)
        rows_html += (
            f'<tr>'
            f'<td style="width:20px;background:{hex_color};border-radius:3px">&nbsp;&nbsp;&nbsp;</td>'
            f'<td style="padding-left:6px;font-size:13px">{etype}</td>'
            f'</tr>'
        )
    st.sidebar.markdown(
        f'<table style="border-collapse:collapse">{rows_html}</table>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Session-state helpers
# ---------------------------------------------------------------------------
def _reset_parsed_pages() -> None:
    st.session_state.parsed_pages = {}


def _init_state() -> None:
    if "parsed_pages" not in st.session_state:
        st.session_state.parsed_pages = {}
    if "pdf_name" not in st.session_state:
        st.session_state.pdf_name = ""
    if "pdf_bytes" not in st.session_state:
        st.session_state.pdf_bytes = b""


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------
def main() -> None:
    st.set_page_config(page_title="Nemotron-Parse Inspector", layout="wide")
    _init_state()

    # ── Sidebar ──────────────────────────────────────────────────────────────
    import os
    default_key = os.environ.get("NVIDIA_API_KEY", "")
    api_key = st.sidebar.text_input(
        "NVIDIA_API_KEY",
        value=default_key,
        type="password",
        help="Your NVIDIA API key for nemotron-parse",
    )

    zoom = st.sidebar.slider("Zoom", min_value=1.0, max_value=3.0, value=2.0, step=0.1)
    max_tokens = st.sidebar.number_input(
        "Max tokens", min_value=1024, max_value=8192, value=4096, step=256
    )

    render_legend()

    # ── Title & upload ────────────────────────────────────────────────────────
    st.title("Nemotron-Parse PDF Inspector")
    uploaded = st.file_uploader("Upload PDF", type=["pdf"])

    if uploaded is None:
        st.info("Upload a PDF to get started.")
        return

    pdf_bytes = uploaded.read()

    # Detect file change → reset parsed cache
    if uploaded.name != st.session_state.pdf_name:
        st.session_state.pdf_name = uploaded.name
        st.session_state.pdf_bytes = pdf_bytes
        _reset_parsed_pages()
    else:
        pdf_bytes = st.session_state.pdf_bytes  # use cached bytes

    # Count pages
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total_pages = len(doc)
    doc.close()

    # ── Two-column layout ─────────────────────────────────────────────────────
    left_col, right_col = st.columns([1, 3])

    with left_col:
        st.markdown("#### Page")
        page_options = list(range(total_pages))
        if total_pages <= 20:
            page_idx = st.radio(
                "Select page",
                options=page_options,
                format_func=lambda p: f"Page {p + 1}",
                label_visibility="collapsed",
            )
        else:
            page_idx = st.selectbox(
                "Select page",
                options=page_options,
                format_func=lambda p: f"Page {p + 1}",
                label_visibility="collapsed",
            )

        parsed_count = len(st.session_state.parsed_pages)
        st.caption(f"{parsed_count} / {total_pages} page(s) parsed")

        parse_disabled = not api_key
        if not api_key:
            st.warning("Enter your NVIDIA_API_KEY in the sidebar to enable parsing.")

        if st.button("Parse this page", disabled=parse_disabled, use_container_width=True):
            with st.spinner(f"Parsing page {page_idx + 1}…"):
                try:
                    elements, raw = parse_page(pdf_bytes, page_idx, api_key, zoom, max_tokens)
                    st.session_state.parsed_pages[page_idx] = {
                        "elements": elements,
                        "raw": raw,
                    }
                    finish_reason = (
                        raw.get("choices", [{}])[0].get("finish_reason", "")
                    )
                    if finish_reason == "length":
                        st.warning("Output truncated — raise Max tokens in the sidebar.")
                    if not elements:
                        st.info("No elements returned for this page.")
                except Exception as exc:
                    err_str = str(exc)
                    if "401" in err_str or "403" in err_str:
                        st.error("Invalid API key — check your NVIDIA_API_KEY.")
                    else:
                        st.error(f"API failed: {exc}")
                    st.session_state.parsed_pages[page_idx] = {"elements": [], "raw": {}}

        if st.button(
            "Parse ALL pages",
            disabled=parse_disabled,
            use_container_width=True,
        ):
            progress = st.progress(0, text="Starting…")
            for i, p in enumerate(range(total_pages)):
                progress.progress(i / total_pages, text=f"Parsing page {p + 1} / {total_pages}")
                if p in st.session_state.parsed_pages:
                    continue
                try:
                    elements, raw = parse_page(pdf_bytes, p, api_key, zoom, max_tokens)
                    st.session_state.parsed_pages[p] = {"elements": elements, "raw": raw}
                except Exception as exc:
                    st.session_state.parsed_pages[p] = {"elements": [], "raw": {}}
                    st.warning(f"Page {p + 1} failed: {exc}")
            progress.progress(1.0, text="Done!")
            st.rerun()

        # Download raw JSON for current page (if parsed)
        if page_idx in st.session_state.parsed_pages:
            raw_json = st.session_state.parsed_pages[page_idx].get("raw", {})
            st.sidebar.download_button(
                label="Download raw JSON",
                data=json.dumps(raw_json, indent=2, ensure_ascii=False),
                file_name=f"page_{page_idx + 1:04d}_raw.json",
                mime="application/json",
            )

    with right_col:
        pil_img = render_page_as_pil(pdf_bytes, page_idx, zoom)

        if page_idx in st.session_state.parsed_pages:
            page_data = st.session_state.parsed_pages[page_idx]
            elements = page_data["elements"]

            if elements:
                annotated = draw_bboxes_on_image(pil_img, elements)
                st.image(annotated, use_container_width=True)

                rows = elements_to_rows(elements)
                st.dataframe(rows, use_container_width=True, hide_index=True)

                # Highlight inverted bbox warning
                inverted_count = sum(1 for r in rows if r["Inverted"])
                if inverted_count:
                    st.warning(
                        f"{inverted_count} inverted bbox(es) detected and auto-fixed for display."
                    )
            else:
                st.image(pil_img, use_container_width=True)
                st.info("No elements returned for this page.")
        else:
            st.image(pil_img, use_container_width=True)
            st.info("Press **Parse this page** to run nemotron-parse.")


if __name__ == "__main__":
    main()
