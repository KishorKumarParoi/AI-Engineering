"""
Mistral OCR Visual Inspector
=============================
Upload a PDF, call the Mistral OCR API, and inspect the extracted markdown
plus image bounding boxes overlaid on rendered pages.

Mistral OCR processes the whole PDF in one shot and returns a pages[] list.
Only images get coordinate overlays (not individual text blocks).

Usage:
    streamlit run scripts/visualize_mistral_ocr.py
"""

from __future__ import annotations

import base64
import os
from io import BytesIO
from pathlib import Path

import pymupdf as fitz
import streamlit as st
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

load_dotenv()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
IMAGE_FILL_ALPHA = 40
IMAGE_BORDER_COLOR = (34, 139, 34)   # green
IMAGE_BORDER_WIDTH = 2
MAX_FILE_SIZE_MB = 50


# ---------------------------------------------------------------------------
# Page rendering (cached)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def render_page_as_pil(pdf_bytes: bytes, page_idx: int, zoom: float = 2.0) -> Image.Image:
    """Rasterize a PDF page to a PIL Image using PyMuPDF."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[page_idx]
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
    doc.close()
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


# ---------------------------------------------------------------------------
# Mistral OCR API call
# ---------------------------------------------------------------------------
def run_ocr(
    pdf_bytes: bytes,
    api_key: str,
    model: str,
    table_format: str,
    include_images: bool,
    extract_header: bool,
    extract_footer: bool,
):
    """
    Send pdf_bytes to the Mistral OCR API and return the full response object.

    Raises on auth errors with a human-readable message.
    """
    from mistralai.client import Mistral
    from mistralai.client.errors import SDKError

    b64 = base64.b64encode(pdf_bytes).decode("utf-8")
    document = {
        "type": "document_url",
        "document_url": f"data:application/pdf;base64,{b64}",
    }

    client = Mistral(api_key=api_key)

    kwargs: dict = {
        "model": model,
        "document": document,
        "include_image_base64": include_images,
        "table_format": table_format,
        "extract_header": extract_header,
        "extract_footer": extract_footer,
    }

    try:
        response = client.ocr.process(**kwargs)
    except SDKError as exc:
        status = getattr(exc, "status_code", None)
        if status in (401, 403):
            raise ValueError("Invalid Mistral API key — check MISTRAL_API_KEY.") from exc
        raise

    return response


# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------
def draw_image_bboxes(pil_img: Image.Image, page_data) -> Image.Image:
    """
    Overlay green bounding boxes for each image region on pil_img.

    OCRImageObject fields (mistralai v2):
      top_left_x, top_left_y, bottom_right_x, bottom_right_y  — pixel space
    OCRPageDimensions: width, height — OCR pixel dimensions of the page
    """
    images = getattr(page_data, "images", None) or []
    if not images:
        return pil_img

    dimensions = getattr(page_data, "dimensions", None)
    pil_w, pil_h = pil_img.size

    # Scale factors: OCR pixel space → PIL render space
    if dimensions and getattr(dimensions, "width", None) and getattr(dimensions, "height", None):
        scale_x = pil_w / dimensions.width
        scale_y = pil_h / dimensions.height
    else:
        scale_x = scale_y = 1.0

    img_rgba = pil_img.convert("RGBA")
    overlay = Image.new("RGBA", img_rgba.size, (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    draw_border = ImageDraw.Draw(img_rgba)

    r, g, b = IMAGE_BORDER_COLOR

    for img_info in images:
        # mistralai v2: top_left_x/y, bottom_right_x/y
        tlx = getattr(img_info, "top_left_x", None)
        tly = getattr(img_info, "top_left_y", None)
        brx = getattr(img_info, "bottom_right_x", None)
        bry = getattr(img_info, "bottom_right_y", None)

        if any(v is None for v in (tlx, tly, brx, bry)):
            continue

        x0 = int(tlx * scale_x)
        y0 = int(tly * scale_y)
        x1 = int(brx * scale_x)
        y1 = int(bry * scale_y)

        # Clamp
        x0 = max(0, min(x0, pil_w - 1))
        y0 = max(0, min(y0, pil_h - 1))
        x1 = max(0, min(x1, pil_w - 1))
        y1 = max(0, min(y1, pil_h - 1))

        if (x1 - x0) < 2 or (y1 - y0) < 2:
            continue

        fill_color = (r, g, b, IMAGE_FILL_ALPHA)
        border_color = (r, g, b, 255)

        draw_overlay.rectangle([x0, y0, x1, y1], fill=fill_color)
        for i in range(IMAGE_BORDER_WIDTH):
            draw_border.rectangle(
                [x0 + i, y0 + i, x1 - i, y1 - i],
                outline=border_color,
            )

        # Label (img.id) in top-left of box
        label = getattr(img_info, "id", "") or ""
        if label:
            try:
                font = ImageFont.load_default()
            except Exception:
                font = None
            draw_border.text((x0 + 3, y0 + 2), label, fill=(r, g, b, 255), font=font)

    result = Image.alpha_composite(img_rgba, overlay).convert("RGB")
    return result


# ---------------------------------------------------------------------------
# Markdown / table helpers
# ---------------------------------------------------------------------------
def full_markdown(ocr_response) -> str:
    """Concatenate all page markdown with page-separator lines."""
    parts: list[str] = []
    for page in ocr_response.pages:
        parts.append(page.markdown or "")
    return "\n\n---\n\n".join(parts)


# ---------------------------------------------------------------------------
# Session-state helpers
# ---------------------------------------------------------------------------
def _init_state() -> None:
    defaults = {
        "ocr_result": None,
        "pdf_name": "",
        "pdf_bytes": b"",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------
def main() -> None:
    st.set_page_config(page_title="Mistral OCR Inspector", layout="wide")
    _init_state()

    # ── Sidebar ──────────────────────────────────────────────────────────────
    st.sidebar.title("Mistral OCR Settings")

    default_key = os.environ.get("MISTRAL_API_KEY", "")
    api_key = st.sidebar.text_input(
        "MISTRAL_API_KEY",
        value=default_key,
        type="password",
        help="Your Mistral API key",
    )

    model = st.sidebar.selectbox(
        "Model",
        options=["mistral-ocr-latest", "mistral-ocr-2512"],
        index=0,
    )

    table_format = st.sidebar.selectbox(
        "Table format",
        options=["markdown", "html"],
        index=0,
    )

    include_images = st.sidebar.checkbox("Include extracted images", value=True)
    extract_header = st.sidebar.checkbox("Extract headers", value=False)
    extract_footer = st.sidebar.checkbox("Extract footers", value=False)

    run_disabled = not api_key
    if not api_key:
        st.sidebar.warning("Enter your MISTRAL_API_KEY above to enable OCR.")

    run_clicked = st.sidebar.button(
        "Run OCR",
        disabled=run_disabled,
        use_container_width=True,
        type="primary",
    )

    # Usage info (shown after a run)
    if st.session_state.ocr_result is not None:
        usage = getattr(st.session_state.ocr_result, "usage_info", None)
        if usage:
            pages_processed = getattr(usage, "pages_processed", "?")
            total_tokens = getattr(usage, "total_tokens", "?")
            st.sidebar.markdown(
                f"**Pages processed:** {pages_processed}  \n"
                f"**Total tokens:** {total_tokens}"
            )

        full_md = full_markdown(st.session_state.ocr_result)
        pdf_stem = Path(st.session_state.pdf_name).stem or "output"
        st.sidebar.download_button(
            label="Download full markdown",
            data=full_md.encode("utf-8"),
            file_name=f"{pdf_stem}_mistral_ocr.md",
            mime="text/markdown",
        )

    # ── Title & upload ────────────────────────────────────────────────────────
    st.title("Mistral OCR PDF Inspector")
    uploaded = st.file_uploader("Upload PDF", type=["pdf"])

    if uploaded is None:
        st.info("Upload a PDF, then press **Run OCR** in the sidebar.")
        return

    pdf_bytes = uploaded.read()

    # Detect file change → reset OCR result
    if uploaded.name != st.session_state.pdf_name:
        st.session_state.pdf_name = uploaded.name
        st.session_state.pdf_bytes = pdf_bytes
        st.session_state.ocr_result = None
    else:
        pdf_bytes = st.session_state.pdf_bytes

    # File size guard
    file_size_mb = len(pdf_bytes) / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        st.warning(
            f"File is {file_size_mb:.1f} MB — Mistral OCR limit is {MAX_FILE_SIZE_MB} MB. "
            "Please use a smaller file."
        )
        return

    # ── Run OCR ───────────────────────────────────────────────────────────────
    if run_clicked:
        with st.spinner("Running Mistral OCR on entire document…"):
            try:
                result = run_ocr(
                    pdf_bytes,
                    api_key,
                    model,
                    table_format,
                    include_images,
                    extract_header,
                    extract_footer,
                )
                st.session_state.ocr_result = result
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(f"Mistral API error: {exc}")

    if st.session_state.ocr_result is None:
        # Count pages and show a plain render while waiting
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(doc)
        doc.close()
        st.info(
            f"PDF loaded ({total_pages} page(s)). "
            "Press **Run OCR** in the sidebar to process."
        )
        pil_img = render_page_as_pil(pdf_bytes, 0, zoom=2.0)
        st.image(pil_img, use_container_width=True, caption="Page 1 preview")
        return

    # ── Two-column layout (after OCR) ─────────────────────────────────────────
    ocr_pages = st.session_state.ocr_result.pages
    total_pages = len(ocr_pages)

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

        page_data = ocr_pages[page_idx]
        images_on_page = getattr(page_data, "images", None) or []
        tables_on_page = getattr(page_data, "tables", None) or []
        page_markdown = page_data.markdown or ""
        word_count = len(page_markdown.split())

        st.caption(
            f"**Images:** {len(images_on_page)}  |  "
            f"**Tables:** {len(tables_on_page)}  |  "
            f"**Words:** {word_count}"
        )

        # Per-page tabs
        tab_md, tab_imgs, tab_tables = st.tabs(["Markdown", "Images", "Tables"])

        with tab_md:
            if page_markdown:
                st.markdown(page_markdown)
            else:
                st.info("No markdown content for this page.")

        with tab_imgs:
            if not images_on_page:
                st.info("No images extracted from this page.")
            else:
                for img_info in images_on_page:
                    # mistralai v2: field is .id (not .image_id)
                    img_id = getattr(img_info, "id", "unknown") or "unknown"
                    tlx = getattr(img_info, "top_left_x", "?")
                    tly = getattr(img_info, "top_left_y", "?")
                    brx = getattr(img_info, "bottom_right_x", "?")
                    bry = getattr(img_info, "bottom_right_y", "?")
                    coord_str = f"({tlx}, {tly}) → ({brx}, {bry})"

                    annotation = getattr(img_info, "image_annotation", None)
                    if annotation:
                        st.caption(f"**{img_id}** — {coord_str}  \n_{annotation}_")
                    else:
                        st.caption(f"**{img_id}** — {coord_str}")

                    # mistralai v2: field is .image_base64 (not .base64)
                    b64_data = getattr(img_info, "image_base64", None)
                    if b64_data and str(b64_data) not in ("UNSET", ""):
                        try:
                            raw = str(b64_data)
                            # Strip data URI prefix if present: "data:image/...;base64,"
                            if "base64," in raw:
                                raw = raw.split("base64,", 1)[1]
                            img_bytes = base64.b64decode(raw)
                            st.image(img_bytes, use_container_width=True)
                        except Exception as e:
                            st.warning(f"Could not decode image {img_id}: {e}")
                    elif not include_images:
                        st.info("Re-run with **Include extracted images** enabled to see image data.")
                    else:
                        st.info(f"No base64 data returned for {img_id}.")

        with tab_tables:
            if not tables_on_page:
                st.info("No tables detected on this page.")
            else:
                for i, tbl in enumerate(tables_on_page, 1):
                    tbl_id = getattr(tbl, "id", f"table-{i}")
                    content = getattr(tbl, "content", "") or ""
                    fmt = getattr(tbl, "format_", table_format)
                    st.caption(f"**{tbl_id}**")
                    if fmt == "html":
                        st.markdown(content, unsafe_allow_html=True)
                    else:
                        st.markdown(content)

    with right_col:
        pil_img = render_page_as_pil(pdf_bytes, page_idx, zoom=2.0)

        if images_on_page:
            annotated = draw_image_bboxes(pil_img, page_data)
            st.image(annotated, use_container_width=True)
            st.caption(
                f"{len(images_on_page)} image region(s) highlighted in green. "
                "See **Images** tab for extracted content."
            )
        else:
            st.image(pil_img, use_container_width=True)
            st.info("No image regions on this page.")


if __name__ == "__main__":
    main()
