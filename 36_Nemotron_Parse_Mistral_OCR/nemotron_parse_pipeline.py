"""
Nemotron-Parse PDF Processing Pipeline
=======================================
Converts each page of a PDF to an image and calls the NVIDIA
nemotron-parse NIM API to extract structured Markdown, bounding boxes,
and semantic class labels. All outputs are saved to a directory.

Usage:
    python nemotron_parse_pipeline.py --pdf docling_report.pdf --output ./results
    python nemotron_parse_pipeline.py --pdf path/to/doc.pdf --output ./results --pages 0 1 2
    python nemotron_parse_pipeline.py --pdf path/to/doc.pdf --output ./results --zoom 2.5

Requirements:
    pip install pymupdf requests python-dotenv tqdm
"""

import argparse
import base64
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pymupdf as fitz # PyMuPDF
import requests
from dotenv import load_dotenv
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
API_ENDPOINT = "https://integrate.api.nvidia.com/v1/chat/completions"
MODEL_ID = "nvidia/nemotron-parse"

# Output mode for nemotron-parse — passed as the "tools" field in the API payload.
# Pick ONE of the three modes:
#   "markdown_bbox"    → Markdown text + bounding boxes + semantic classes  (default, most complete)
#   "markdown_no_bbox" → Markdown text only, no spatial coordinates         (faster, smaller response)
#   "detection_only"   → Bounding boxes + classes only, no text content     (layout analysis only)
PARSE_TOOL = "markdown_bbox"

# Retry settings for transient API errors
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0  # seconds, doubles each retry

# Nemotron-parse input resolution constraints (from model card)
MIN_WIDTH, MIN_HEIGHT = 1024, 1280
MAX_WIDTH, MAX_HEIGHT = 1648, 2048

# API request body limit — NVIDIA hosted endpoints reject payloads above ~5MB.
# We target 4MB (base64-encoded) as a safe ceiling. The auto-compression loop
# in page_to_base64_jpeg will step down JPEG quality until it fits.
MAX_PAYLOAD_BYTES = 4 * 1024 * 1024  # 4 MB
JPEG_QUALITY_START = 92             # high quality starting point
JPEG_QUALITY_MIN   = 60             # floor — below this, accuracy degrades visibly
JPEG_QUALITY_STEP  = 8              # reduce by this amount each iteration

# HTTP status codes that are non-retryable (client errors)
NO_RETRY_STATUSES = {400, 401, 403, 404, 422}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class PageResult:
    page_num: int           # 0-indexed
    success: bool
    raw_response: dict = field(default_factory=dict)
    parsed_text: str = ""
    error: str = ""
    latency_s: float = 0.0


# ---------------------------------------------------------------------------
# PDF → image helpers
# ---------------------------------------------------------------------------
def compute_zoom(page: fitz.Page, zoom: float) -> fitz.Matrix:
    """
    Scale the page so its rasterized dimensions stay within the model's
    supported resolution window (1024×1280 – 1648×2048).
    The caller-supplied zoom is used as a starting point; we clamp if needed.
    """
    mat = fitz.Matrix(zoom, zoom)
    rect = page.rect
    w = rect.width * zoom
    h = rect.height * zoom

    # Clamp to max
    if w > MAX_WIDTH or h > MAX_HEIGHT:
        scale = min(MAX_WIDTH / rect.width, MAX_HEIGHT / rect.height)
        mat = fitz.Matrix(scale, scale)
        log.debug("Page too large at zoom=%.1f – clamped to scale=%.3f", zoom, scale)

    # Clamp to min
    w = rect.width * mat.a
    h = rect.height * mat.d
    if w < MIN_WIDTH or h < MIN_HEIGHT:
        scale = max(MIN_WIDTH / rect.width, MIN_HEIGHT / rect.height)
        mat = fitz.Matrix(scale, scale)
        log.debug("Page too small at zoom=%.1f – clamped to scale=%.3f", zoom, scale)

    return mat


def page_to_base64_jpeg(page: fitz.Page, zoom: float) -> tuple[str, int, int]:
    """
    Rasterize a PDF page and return a base64-encoded JPEG that fits within
    MAX_PAYLOAD_BYTES. JPEG is used instead of PNG because:
      - PNG of a 1648×2048 page is typically 3–12 MB (too large for the API).
      - JPEG at quality 92 is visually lossless for printed text and is 5–10x
        smaller than PNG, reliably landing under the 4 MB API limit.

    The function starts at JPEG_QUALITY_START and steps down by JPEG_QUALITY_STEP
    until the payload fits, stopping at JPEG_QUALITY_MIN.

    Returns:
        (b64_string, jpeg_quality_used, payload_size_bytes)
    """
    mat = compute_zoom(page, zoom)
    pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)

    quality = JPEG_QUALITY_START
    while quality >= JPEG_QUALITY_MIN:
        jpeg_bytes = pix.tobytes("jpg", jpg_quality=quality)
        b64 = base64.b64encode(jpeg_bytes).decode("utf-8")
        payload_size = len(b64)

        if payload_size <= MAX_PAYLOAD_BYTES:
            return b64, quality, payload_size

        log.debug(
            "Payload %.1f MB at quality=%d exceeds limit – reducing quality",
            payload_size / 1e6, quality,
        )
        quality -= JPEG_QUALITY_STEP

    # Last resort: send at minimum quality and warn
    log.warning(
        "Could not compress page below %.1f MB at quality=%d (limit=%.1f MB). "
        "Sending anyway – API may reject with 400.",
        payload_size / 1e6, quality + JPEG_QUALITY_STEP, MAX_PAYLOAD_BYTES / 1e6,
    )
    return b64, quality + JPEG_QUALITY_STEP, payload_size


# ---------------------------------------------------------------------------
# API call
# ---------------------------------------------------------------------------
def call_nemotron_parse(
    b64_image: str,
    mime: str,
    api_key: str,
    max_tokens: int = 4096,
    timeout: int = 120,
) -> dict:
    """
    POST one page image to the nemotron-parse NIM endpoint.

    Payload structure (per official NVIDIA sample code):
      - Exactly ONE user message — no system message allowed.
      - Content is a plain HTML string with the image embedded as an <img> tag.
      - Output mode is selected via the top-level "tools" field (a list with one string).

    Returns the raw JSON response dict.
    Raises requests.HTTPError on non-2xx responses.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # Embed the image as an HTML <img> tag inside a plain string — this is the
    # format nemotron-parse expects. A content array or system message causes 400.
    image_html = f'<img src="data:{mime};base64,{b64_image}" />'

    payload = {
        "model": MODEL_ID,
        "messages": [
            {
                "role": "user",
                "content": image_html,   # plain HTML string, NOT a content array
            }
        ],
        # tools must be a list of dicts following the OpenAI ChatCompletionToolsParam
        # schema — plain strings cause a 400 BadRequestError.
        "tools": [
            {
                "type": "function",
                "function": {"name": PARSE_TOOL},
            }
        ],
        "max_tokens": max_tokens,
    }

    resp = requests.post(API_ENDPOINT, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def call_with_retries(
    b64_image: str,
    mime: str,
    api_key: str,
    max_tokens: int = 4096,
    timeout: int = 120,
) -> dict:
    """
    Wraps call_nemotron_parse with exponential-backoff retries.

    Only retries on transient server errors (5xx) and network failures.
    Client errors (400, 401, 403, 404, 422) are raised immediately — retrying
    them is pointless and wastes time (the root cause is in the request itself).
    """
    delay = RETRY_BACKOFF
    last_exc: Optional[Exception] = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return call_nemotron_parse(b64_image, mime, api_key, max_tokens, timeout)
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else 0
            if status in NO_RETRY_STATUSES:
                body = exc.response.text[:500] if exc.response is not None else ""
                log.error(
                    "HTTP %d (non-retryable). Response body: %s",
                    status, body,
                )
                raise
            last_exc = exc
            log.warning(
                "HTTP %s on attempt %d/%d (server error) – retrying in %.1fs",
                status, attempt, MAX_RETRIES, delay,
            )
        except requests.RequestException as exc:
            last_exc = exc
            log.warning(
                "Network error on attempt %d/%d – retrying in %.1fs: %s",
                attempt, MAX_RETRIES, delay, exc,
            )

        time.sleep(delay)
        delay *= 2

    raise RuntimeError(f"All {MAX_RETRIES} retries exhausted") from last_exc


# ---------------------------------------------------------------------------
# Output extraction
# ---------------------------------------------------------------------------
def extract_text_from_response(response: dict) -> str:
    """
    Pull the parsed content from the API response.

    When a 'tools' field is present in the request, nemotron-parse returns
    its output inside tool_calls[0].function.arguments (a JSON string),
    NOT in message.content (which will be None in that case).

    The arguments value is itself a JSON string — we unwrap it to get the
    actual Markdown/bbox text.
    """
    try:
        message = response["choices"][0]["message"]

        # --- Tool-call response path (used when "tools" field is in the request) ---
        tool_calls = message.get("tool_calls")
        if tool_calls:
            arguments = tool_calls[0]["function"]["arguments"]
            # arguments is a JSON-encoded string — parse it to extract the content
            try:
                parsed = json.loads(arguments)
                # The key varies by tool mode; try common keys in order
                for key in ("content", "markdown", "text", "result"):
                    if key in parsed:
                        return parsed[key]
                # Fallback: return the raw arguments string if no known key found
                return arguments
            except (json.JSONDecodeError, TypeError):
                # arguments may already be a plain string in some versions
                return arguments

        # --- Standard chat response path (fallback) ---
        content = message.get("content")
        return content or ""

    except (KeyError, IndexError, TypeError):
        return ""


# ---------------------------------------------------------------------------
# Saving outputs
# ---------------------------------------------------------------------------
def save_page_outputs(result: PageResult, output_dir: Path, pdf_stem: str) -> None:
    """
    For each page we save:
      - <stem>_page_<N>_raw.json   : full API response (tokens, finish_reason, etc.)
      - <stem>_page_<N>_parsed.md  : the extracted Markdown text only
    """
    page_label = f"page_{result.page_num:04d}"

    # Raw JSON (full response including usage stats)
    raw_path = output_dir / f"{pdf_stem}_{page_label}_raw.json"
    raw_path.write_text(
        json.dumps(result.raw_response, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Parsed Markdown text
    md_path = output_dir / f"{pdf_stem}_{page_label}_parsed.md"
    md_path.write_text(result.parsed_text or "", encoding="utf-8")

    log.debug("Saved → %s | %s", raw_path.name, md_path.name)


def save_summary(results: list[PageResult], output_dir: Path, pdf_stem: str) -> None:
    """Write a human-readable processing summary JSON."""
    summary = {
        "pdf": pdf_stem,
        "total_pages_processed": len(results),
        "successful": sum(1 for r in results if r.success),
        "failed": sum(1 for r in results if not r.success),
        "avg_latency_s": (
            sum(r.latency_s for r in results if r.success)
            / max(1, sum(1 for r in results if r.success))
        ),
        "pages": [
            {
                "page": r.page_num,
                "success": r.success,
                "latency_s": round(r.latency_s, 3),
                "error": r.error or None,
                "output_tokens": (
                    r.raw_response.get("usage", {}).get("completion_tokens")
                    if r.success
                    else None
                ),
            }
            for r in results
        ],
    }
    summary_path = output_dir / f"{pdf_stem}_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    log.info("Summary saved → %s", summary_path)


def save_combined_markdown(results: list[PageResult], output_dir: Path, pdf_stem: str) -> None:
    """
    Concatenate all successfully parsed pages into one Markdown file.
    Useful for feeding directly into a chunker.
    """
    lines = []
    for r in sorted(results, key=lambda x: x.page_num):
        if r.success and r.parsed_text:
            lines.append(f"\n\n<!-- PAGE {r.page_num} -->\n\n")
            lines.append(r.parsed_text)

    combined_path = output_dir / f"{pdf_stem}_combined.md"
    combined_path.write_text("".join(lines), encoding="utf-8")
    log.info("Combined Markdown saved → %s", combined_path)


# ---------------------------------------------------------------------------
# Core pipeline
# ---------------------------------------------------------------------------
def process_pdf(
    pdf_path: Path,
    output_dir: Path,
    api_key: str,
    pages: Optional[list[int]] = None,
    zoom: float = 2.0,
    max_tokens: int = 4096,
    save_images: bool = False,
) -> list[PageResult]:
    """
    Main pipeline:
      1. Open PDF with PyMuPDF
      2. For each requested page: rasterize → base64 → API call → save outputs
      3. Return list of PageResult objects

    Args:
        pdf_path    : Path to the input PDF
        output_dir  : Directory where outputs are written
        api_key     : NVIDIA API key
        pages       : List of 0-indexed page numbers (None = all pages)
        zoom        : Rasterization zoom factor (auto-clamped to model limits)
        max_tokens  : Max output tokens per page (increase for dense pages)
        save_images : If True, also save each page PNG for inspection
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_stem = pdf_path.stem

    doc = fitz.open(str(pdf_path))
    total_pages = len(doc)
    log.info("Opened PDF: %s  (%d pages)", pdf_path.name, total_pages)

    # Resolve page list
    if pages is None:
        page_nums = list(range(total_pages))
    else:
        invalid = [p for p in pages if p < 0 or p >= total_pages]
        if invalid:
            log.warning("Skipping out-of-range pages: %s (PDF has %d pages)", invalid, total_pages)
        page_nums = [p for p in pages if 0 <= p < total_pages]

    if not page_nums:
        log.error("No valid pages to process.")
        return []

    log.info("Processing %d page(s) with zoom=%.1f | max_tokens=%d", len(page_nums), zoom, max_tokens)

    results: list[PageResult] = []

    for page_num in tqdm(page_nums, desc="Pages", unit="pg"):
        page = doc[page_num]
        result = PageResult(page_num=page_num, success=False)

        try:
            # --- Rasterize → JPEG with auto-compression ---
            b64_image, jpeg_quality, payload_bytes = page_to_base64_jpeg(page, zoom)
            log.debug(
                "Page %d rasterized: JPEG quality=%d payload=%.2f MB",
                page_num, jpeg_quality, payload_bytes / 1e6,
            )

            if save_images:
                img_path = output_dir / f"{pdf_stem}_page_{page_num:04d}.jpg"
                img_bytes = base64.b64decode(b64_image)
                img_path.write_bytes(img_bytes)

            # --- API call ---
            t0 = time.perf_counter()
            response = call_with_retries(b64_image, "image/jpeg", api_key, max_tokens)
            result.latency_s = time.perf_counter() - t0

            result.raw_response = response
            result.parsed_text = extract_text_from_response(response)
            result.success = bool(result.parsed_text)

            finish_reason = (
                response.get("choices", [{}])[0].get("finish_reason", "?")
            )
            usage = response.get("usage", {})
            log.info(
                "Page %4d ✓  %.2fs | tokens in=%s out=%s | finish=%s",
                page_num,
                result.latency_s,
                usage.get("prompt_tokens", "?"),
                usage.get("completion_tokens", "?"),
                finish_reason,
            )

            # Warn if the model hit the token limit mid-output
            if finish_reason == "length":
                log.warning(
                    "Page %d hit max_tokens=%d – output may be truncated. "
                    "Re-run with --max-tokens higher.",
                    page_num, max_tokens,
                )

        except requests.HTTPError as exc:
            result.error = f"HTTP {exc.response.status_code}: {exc.response.text[:200]}"
            log.error("Page %d FAILED: %s", page_num, result.error)
        except Exception as exc:
            result.error = str(exc)
            log.error("Page %d FAILED: %s", page_num, result.error)

        # Always save whatever we have (even partial/error state)
        save_page_outputs(result, output_dir, pdf_stem)
        results.append(result)

    doc.close()

    # Aggregate outputs
    save_summary(results, output_dir, pdf_stem)
    save_combined_markdown(results, output_dir, pdf_stem)

    successful = sum(1 for r in results if r.success)
    log.info(
        "Done. %d/%d pages succeeded. Outputs → %s",
        successful, len(results), output_dir,
    )
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Nemotron-Parse PDF pipeline – extract structured Markdown from PDFs via NVIDIA NIM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process entire PDF
  python nemotron_parse_pipeline.py --pdf report.pdf --output ./results

  # Process only pages 0, 1, 2 (0-indexed)
  python nemotron_parse_pipeline.py --pdf report.pdf --output ./results --pages 0 1 2

  # Higher resolution for dense pages + save page images for inspection
  python nemotron_parse_pipeline.py --pdf report.pdf --output ./results --zoom 2.5 --save-images

  # Increase token budget for very dense pages
  python nemotron_parse_pipeline.py --pdf report.pdf --output ./results --max-tokens 8192
        """,
    )
    parser.add_argument("--pdf", required=True, type=Path, help="Path to the input PDF file")
    parser.add_argument("--output", required=True, type=Path, help="Output directory for results")
    parser.add_argument(
        "--pages",
        nargs="+",
        type=int,
        default=None,
        metavar="N",
        help="0-indexed page numbers to process (default: all pages)",
    )
    parser.add_argument(
        "--zoom",
        type=float,
        default=2.0,
        help="Rasterization zoom factor (default: 2.0, auto-clamped to model resolution limits)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=4096,
        help="Max output tokens per page (default: 4096; increase for dense pages)",
    )
    parser.add_argument(
        "--save-images",
        action="store_true",
        help="Also save each page as a PNG image for visual inspection",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="NVIDIA API key (overrides NVIDIA_API_KEY env var / .env file)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # --- Resolve API key (priority: CLI arg > env var > .env file) ---
    load_dotenv()
    api_key = args.api_key or os.environ.get("NVIDIA_API_KEY")
    if not api_key:
        log.error(
            "No API key found. Set NVIDIA_API_KEY in your environment, .env file, "
            "or pass --api-key."
        )
        sys.exit(1)

    # --- Validate PDF ---
    if not args.pdf.exists():
        log.error("PDF not found: %s", args.pdf)
        sys.exit(1)
    if args.pdf.suffix.lower() != ".pdf":
        log.warning("File does not have a .pdf extension – proceeding anyway.")

    # --- Run pipeline ---
    results = process_pdf(
        pdf_path=args.pdf,
        output_dir=args.output,
        api_key=api_key,
        pages=args.pages,
        zoom=args.zoom,
        max_tokens=args.max_tokens,
        save_images=args.save_images,
    )

    # Exit with error code if any pages failed
    failed = [r for r in results if not r.success]
    if failed:
        log.warning("%d page(s) failed: %s", len(failed), [r.page_num for r in failed])
        sys.exit(2)


if __name__ == "__main__":
    main()
