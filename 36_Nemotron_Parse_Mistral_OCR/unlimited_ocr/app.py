"""
Unlimited-OCR Visual Inspector
==============================
Upload an image or PDF and run it through Baidu's Unlimited-OCR model
(served via a vLLM OpenAI-compatible endpoint). Supports single-image
OCR and multi-page PDF batch processing with per-page progress.

Model: baidu/Unlimited-OCR (MIT license) — https://github.com/baidu/Unlimited-OCR
Served via vLLM's OpenAI-compatible /v1/chat/completions endpoint.

Usage:
    streamlit run unlimited_ocr/app.py
"""

from __future__ import annotations

import ast
import hashlib
import io
import os
import re
import time
from pathlib import Path

import pymupdf as fitz
import requests
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image, ImageDraw

load_dotenv()

DEFAULT_API_URL = os.environ.get("UNLIMITED_OCR_URL", "")
DEFAULT_MODEL = "baidu/Unlimited-OCR"

# Fixed colors for common element labels; unknown labels get a stable hash-derived color.
LABEL_COLORS = {
    "title": (220, 20, 60),
    "text": (30, 144, 255),
    "table": (255, 140, 0),
    "image": (34, 139, 34),
    "figure": (34, 139, 34),
    "caption": (148, 0, 211),
    "header": (105, 105, 105),
    "footer": (105, 105, 105),
    "formula": (218, 112, 214),
}


# ---------------------------------------------------------------------------
# PDF rendering (cached)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def pdf_to_images(pdf_bytes: bytes, dpi: int) -> list[tuple[str, bytes]]:
    """Rasterize every page of a PDF to PNG bytes at the given DPI."""
    images: list[tuple[str, bytes]] = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    for page_num in range(len(doc)):
        pix = doc[page_num].get_pixmap(matrix=mat, colorspace=fitz.csRGB)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        images.append((f"page_{page_num + 1:04d}.png", buf.getvalue()))
    doc.close()
    return images


def encode_png_b64(png_bytes: bytes) -> str:
    import base64

    return base64.b64encode(png_bytes).decode("utf-8")


# ---------------------------------------------------------------------------
# Unlimited-OCR API call
# ---------------------------------------------------------------------------
def call_unlimited_ocr(client: OpenAI, model: str, image_b64: str, is_multi_page: bool) -> str:
    """
    Call the Unlimited-OCR API with a single image.

    The prompt MUST start with the literal `<image>` token — without it
    the model returns empty output. Per the official README, single images
    use `document parsing.` while PDF/multi-page pages use `Multi page
    parsing.` — using the wrong one for a PDF page can silently drop the
    <|ref|>/<|det|> grounding tokens. `window_size` is 128 for single
    images (gundam mode) and 1024 for multi-page PDFs (base mode).
    """
    window_size = 1024 if is_multi_page else 128
    instruction = "Multi page parsing." if is_multi_page else "document parsing."

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": f"<image>{instruction}"},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                },
            ],
        }
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=8192,
        temperature=0.0,
        extra_body={
            "skip_special_tokens": False,
            "vllm_xargs": {"ngram_size": 35, "window_size": window_size},
        },
    )
    return response.choices[0].message.content or ""


def clean_ocr_output(raw_text: str) -> str:
    """Strip grounding/page-wrapper tokens, keeping the actual text content."""
    cleaned = re.sub(r"</?PAGE>", "", raw_text)
    cleaned = re.sub(r"<\|det\|>.*?<\|/det\|>", "", cleaned)
    cleaned = re.sub(r"<\|ref\|>", "", cleaned)
    cleaned = re.sub(r"<\|/ref\|>", "", cleaned)
    cleaned = re.sub(r"<\|.*?\|>", "", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


# Observed server output nests the label + box inside one <|det|>...<|/det|> tag,
# e.g. `<|det|>title [344, 280, 654, 306]<|/det|>Docling Technical Report`.
# A `<|ref|>label<|/ref|>` wrapper (the format documented in the model's own
# transformers reference code) is also accepted in case a different serving
# path produces it.
DET_BLOCK_PATTERN = re.compile(r"(?:<\|ref\|>(.*?)<\|/ref\|>)?<\|det\|>(.*?)<\|/det\|>", re.DOTALL)
LABEL_BOX_PATTERN = re.compile(r"([A-Za-z_][\w-]*)\s*(\[.*\])$", re.DOTALL)


def parse_refs(raw_text: str) -> list[dict]:
    """
    Extract (label, boxes) pairs from grounding tokens. Coordinates are
    normalized 0-999 relative to the original image. A block may hold one
    flat box `[x1,y1,x2,y2]` or several `[[x1,y1,x2,y2], ...]`.
    """
    refs = []
    for ref_label, block in DET_BLOCK_PATTERN.findall(raw_text):
        label = ref_label.strip()
        box_str = block.strip()
        if not label:
            m = LABEL_BOX_PATTERN.match(box_str)
            if not m:
                continue
            label, box_str = m.group(1), m.group(2)
        try:
            parsed = ast.literal_eval(box_str)
        except (ValueError, SyntaxError):
            nums = [float(n) for n in re.findall(r"-?\d+\.?\d*", box_str)]
            parsed = [nums[i : i + 4] for i in range(0, len(nums) - 3, 4)]
        if not parsed:
            continue
        if isinstance(parsed[0], int | float):
            parsed = [parsed]
        boxes = [tuple(b) for b in parsed if len(b) == 4]
        if boxes:
            refs.append({"label": label, "boxes": boxes})
    return refs


def _color_for_label(label: str) -> tuple[int, int, int]:
    if label in LABEL_COLORS:
        return LABEL_COLORS[label]
    h = int(hashlib.md5(label.encode()).hexdigest(), 16)
    return (80 + h % 150, 80 + (h // 150) % 150, 80 + (h // 22500) % 150)


def draw_bboxes(pil_image: Image.Image, refs: list[dict]) -> Image.Image:
    """Overlay color-coded bounding boxes (scaled from 0-999 to image pixels)."""
    img = pil_image.convert("RGB")
    draw = ImageDraw.Draw(img)
    w, h = img.size
    for ref in refs:
        color = _color_for_label(ref["label"])
        for box in ref["boxes"]:
            x1, y1, x2, y2 = (
                box[0] / 999 * w,
                box[1] / 999 * h,
                box[2] / 999 * w,
                box[3] / 999 * h,
            )
            x1, x2 = sorted((max(0, min(int(x1), w - 1)), max(0, min(int(x2), w - 1))))
            y1, y2 = sorted((max(0, min(int(y1), h - 1)), max(0, min(int(y2), h - 1))))
            draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
            draw.text((x1 + 3, max(0, y1 - 12)), ref["label"], fill=color)
    return img


def check_health(api_url: str) -> tuple[bool, str]:
    """Hit the vLLM server's /health endpoint (sibling of /v1, not under it)."""
    base = api_url[: -len("/v1")] if api_url.endswith("/v1") else api_url
    health_url = base.rstrip("/") + "/health"
    try:
        resp = requests.get(health_url, timeout=10)
        if resp.status_code == 200:
            return True, "API is healthy"
        return False, f"API returned {resp.status_code}"
    except Exception as exc:
        return False, f"Connection failed: {exc}"


# ---------------------------------------------------------------------------
# Session-state helpers
# ---------------------------------------------------------------------------
def _init_state() -> None:
    defaults = {
        "uo_file_name": "",
        "uo_results": None,  # list[dict] for PDFs, float (elapsed) for single image
        "uo_raw": None,
        "uo_image_png": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------
def main() -> None:
    st.set_page_config(page_title="Unlimited OCR", page_icon="📄", layout="wide")
    _init_state()

    st.sidebar.title("Unlimited-OCR Settings")

    api_url = st.sidebar.text_input(
        "API Base URL",
        value=DEFAULT_API_URL,
        help="vLLM OpenAI-compatible endpoint, e.g. https://.../v1",
    )
    model_name = st.sidebar.text_input("Model Name", value=DEFAULT_MODEL)

    output_mode = st.sidebar.radio(
        "Output Format",
        options=["Clean Markdown", "Raw OCR (with grounding tokens)"],
        index=0,
    )
    pdf_dpi = st.sidebar.slider("PDF Render DPI", min_value=150, max_value=300, value=200, step=50)

    if st.sidebar.button("🔄 Check API Health", use_container_width=True):
        if not api_url:
            st.sidebar.error("Set an API Base URL first.")
        else:
            ok, msg = check_health(api_url)
            (st.sidebar.success if ok else st.sidebar.error)(msg)

    st.sidebar.markdown("---")
    st.sidebar.caption(
        "Model: [baidu/Unlimited-OCR](https://github.com/baidu/Unlimited-OCR) (MIT), "
        "served via vLLM."
    )

    st.title("📄 Unlimited-OCR Inspector")
    st.caption("One-shot long-horizon document parsing powered by Baidu Unlimited-OCR")

    uploaded_file = st.file_uploader(
        "Upload an image or PDF",
        type=["png", "jpg", "jpeg", "bmp", "tiff", "pdf"],
    )

    if uploaded_file is None:
        st.info("Upload a file to begin.")
        return

    if uploaded_file.name != st.session_state.uo_file_name:
        st.session_state.uo_file_name = uploaded_file.name
        st.session_state.uo_results = None
        st.session_state.uo_raw = None
        st.session_state.uo_image_png = None

    if not api_url:
        st.warning("Set the API Base URL in the sidebar (or `UNLIMITED_OCR_URL` in `.env`).")
        return

    client = OpenAI(api_key="EMPTY", base_url=api_url, timeout=3600)
    is_pdf = uploaded_file.type == "application/pdf"

    st.markdown("---")

    # ── PDF ──
    if is_pdf:
        pdf_bytes = uploaded_file.getvalue()
        pages = pdf_to_images(pdf_bytes, pdf_dpi)
        st.success(f"Converted {len(pages)} page(s)")

        cols = st.columns(min(4, len(pages)))
        for i, (name, png) in enumerate(pages[:4]):
            with cols[i % 4]:
                st.image(png, caption=name, use_container_width=True)
        if len(pages) > 4:
            st.caption(f"... and {len(pages) - 4} more page(s)")

        if st.button("🚀 Process All Pages", type="primary", use_container_width=True):
            results = []
            progress = st.progress(0)
            status = st.empty()

            for idx, (name, png) in enumerate(pages):
                status.info(f"⏳ Processing page {idx + 1} of {len(pages)}...")
                progress.progress((idx + 1) / len(pages))
                start = time.time()
                try:
                    raw = call_unlimited_ocr(
                        client, model_name, encode_png_b64(png), is_multi_page=True
                    )
                    elapsed = time.time() - start
                    content = clean_ocr_output(raw) if output_mode == "Clean Markdown" else raw
                    results.append(
                        {
                            "page": idx + 1,
                            "name": name,
                            "content": content,
                            "raw": raw,
                            "time": elapsed,
                        }
                    )
                except Exception as exc:
                    results.append(
                        {
                            "page": idx + 1,
                            "name": name,
                            "content": f"ERROR: {exc}",
                            "raw": "",
                            "time": 0,
                        }
                    )

            progress.empty()
            status.empty()
            st.session_state.uo_results = results

        if st.session_state.uo_results:
            results = st.session_state.uo_results
            st.markdown("---")
            st.subheader("📋 OCR Results")

            total_time = sum(r["time"] for r in results)
            success = sum(1 for r in results if not r["content"].startswith("ERROR"))

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Pages", len(results))
            c2.metric("Successful", success)
            c3.metric("Failed", len(results) - success)
            c4.metric("Total Time", f"{total_time:.1f}s")

            combined_md = "\n\n---\n\n".join(
                f"## Page {r['page']}\n\n{r['content']}" for r in results
            )
            st.markdown("#### Combined Markdown Output")
            st.markdown(combined_md)

            stem = Path(uploaded_file.name).stem
            d1, d2 = st.columns(2)
            d1.download_button(
                "📥 Download Markdown (.md)",
                data=combined_md,
                file_name=f"{stem}_unlimited_ocr.md",
                mime="text/markdown",
                use_container_width=True,
            )
            raw_combined = "\n\n---\n\n".join(
                f"=== PAGE {r['page']} ===\n{r['content']}" for r in results
            )
            d2.download_button(
                "📥 Download Text (.txt)",
                data=raw_combined,
                file_name=f"{stem}_unlimited_ocr.txt",
                mime="text/plain",
                use_container_width=True,
            )

            with st.expander("🔍 Per-page details"):
                for r in results:
                    st.markdown(f"**Page {r['page']}** — {r['time']:.1f}s")
                    st.code(r["content"], language="markdown")

            st.markdown("---")
            st.subheader("🗺️ Bounding Box Viewer")
            page_options = [r["page"] for r in results]
            page_choice = st.selectbox(
                "Select page", options=page_options, format_func=lambda p: f"Page {p}"
            )
            sel = results[page_choice - 1]
            sel_png = pages[page_choice - 1][1]
            refs = parse_refs(sel["raw"])

            bb_col1, bb_col2 = st.columns([1, 1])
            with bb_col1:
                if refs:
                    annotated = draw_bboxes(Image.open(io.BytesIO(sel_png)), refs)
                    st.image(
                        annotated,
                        use_container_width=True,
                        caption=f"{len(refs)} element(s) detected",
                    )
                else:
                    st.image(sel_png, use_container_width=True)
                    st.warning(
                        "No <|ref|>/<|det|> grounding tokens in the raw output. "
                        "If this persists after re-processing, the vLLM server likely isn't "
                        "the dedicated `vllm/vllm-openai:unlimited-ocr` image, or wasn't started "
                        "with `--logits_processors vllm.model_executor.models.unlimited_ocr:"
                        "NGramPerReqLogitsProcessor` — see `unlimited_ocr/README.md`."
                    )
            with bb_col2:
                st.markdown(sel["content"] or "No content.")

    # ── Single image ──
    else:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)
        with col2:
            st.write(f"**Name:** {uploaded_file.name}")
            st.write(f"**Type:** {uploaded_file.type}")
            st.write(f"**Size:** {uploaded_file.size / 1024:.1f} KB")

        if st.button("🚀 Process Image", type="primary", use_container_width=True):
            with st.spinner("Running OCR... this may take 10-30 seconds"):
                image = Image.open(uploaded_file)
                buf = io.BytesIO()
                image.convert("RGB").save(buf, format="PNG")
                start = time.time()
                try:
                    raw = call_unlimited_ocr(
                        client, model_name, encode_png_b64(buf.getvalue()), is_multi_page=False
                    )
                    st.session_state.uo_raw = raw
                    st.session_state.uo_results = time.time() - start
                    st.session_state.uo_image_png = buf.getvalue()
                except Exception as exc:
                    st.error(f"❌ OCR failed: {exc}")
                    st.info("Make sure the API server is running and the URL is correct.")

        if st.session_state.uo_raw is not None:
            raw = st.session_state.uo_raw
            elapsed = st.session_state.uo_results
            st.success(f"✅ OCR completed in {elapsed:.1f} seconds")

            final_output = clean_ocr_output(raw) if output_mode == "Clean Markdown" else raw
            refs = parse_refs(raw)

            tab1, tab2, tab3 = st.tabs(
                ["📝 Formatted Markdown", "🔍 Raw Output", "🗺️ Bounding Boxes"]
            )
            with tab1:
                st.markdown(final_output)
            with tab2:
                st.code(raw, language="markdown")
            with tab3:
                if refs and st.session_state.uo_image_png:
                    annotated = draw_bboxes(
                        Image.open(io.BytesIO(st.session_state.uo_image_png)), refs
                    )
                    st.image(
                        annotated,
                        use_container_width=True,
                        caption=f"{len(refs)} element(s) detected",
                    )
                else:
                    st.warning(
                        "No <|ref|>/<|det|> grounding tokens in the raw output. "
                        "If this persists after re-processing, the vLLM server likely isn't "
                        "the dedicated `vllm/vllm-openai:unlimited-ocr` image, or wasn't started "
                        "with `--logits_processors vllm.model_executor.models.unlimited_ocr:"
                        "NGramPerReqLogitsProcessor` — see `unlimited_ocr/README.md`."
                    )

            stem = Path(uploaded_file.name).stem
            d1, d2 = st.columns(2)
            d1.download_button(
                "📥 Download Markdown",
                data=final_output,
                file_name=f"{stem}_unlimited_ocr.md",
                mime="text/markdown",
                use_container_width=True,
            )
            d2.download_button(
                "📥 Download Raw Text",
                data=raw,
                file_name=f"{stem}_unlimited_ocr_raw.txt",
                mime="text/plain",
                use_container_width=True,
            )

    st.markdown("---")
    st.caption(
        "Powered by [Baidu Unlimited-OCR](https://github.com/baidu/Unlimited-OCR) | Served via vLLM"
    )


if __name__ == "__main__":
    main()
