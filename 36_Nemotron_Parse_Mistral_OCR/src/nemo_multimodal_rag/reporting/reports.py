"""Generate human-readable Markdown reports for each pipeline stage.

Four public functions are called from ingest.py:
  - render_parsed_document  → results/reports/00_parsed_document.md
  - save_all_image_crops    → results/images/*.jpg
  - render_chunks_report    → results/reports/01_chunks_pre_captioning.md
                            → results/reports/02_chunks_post_captioning.md

All functions are synchronous and make no API calls.
"""

from __future__ import annotations

import logging
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from nemo_multimodal_rag.ingestion.chunker import Chunk
from nemo_multimodal_rag.ingestion.image_captioner import crop_image_from_pdf
from nemo_multimodal_rag.ingestion.parser import ParsedElement

log = logging.getLogger(__name__)

_MAX_TEXT_LEN = 400  # truncate long element text in reports


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _truncate(text: str, limit: int = _MAX_TEXT_LEN) -> str:
    """Return text truncated with ellipsis if it exceeds limit."""
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "…"


def _bbox_str(bbox: dict) -> str:
    return (
        f"({bbox['xmin']:.2f}, {bbox['ymin']:.2f})"
        f" → ({bbox['xmax']:.2f}, {bbox['ymax']:.2f})"
    )


def _est_tokens(text: str) -> int:
    return len(text) // 4


def _reports_dir(results_dir: Path) -> Path:
    d = results_dir / "reports"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _images_dir(results_dir: Path) -> Path:
    d = results_dir / "images"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------------------
# Report 00 — Parsed document
# ---------------------------------------------------------------------------

def render_parsed_document(
    elements: list[ParsedElement],
    results_dir: Path,
) -> Path:
    """Write results/reports/00_parsed_document.md.

    Args:
        elements: Stitched elements from Phase 1.
        results_dir: Pipeline results root directory.

    Returns:
        Path to the written Markdown file.
    """
    out_path = _reports_dir(results_dir) / "00_parsed_document.md"

    # Gather metadata
    pages = sorted({e.page_num for e in elements})
    page_count = len(pages)
    type_counts: Counter[str] = Counter(e.element_type for e in elements)

    lines: list[str] = []
    today = date.today().isoformat()

    # Header
    lines.append("# Parsed Document")
    lines.append(
        f"Generated: {today}  |  Pages: {page_count}  |  Elements: {len(elements)}"
    )
    lines.append("")

    # Element type summary table
    lines.append("## Element Type Summary")
    lines.append("| Type | Count |")
    lines.append("|------|-------|")
    for etype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        lines.append(f"| {etype} | {count} |")
    lines.append("")
    lines.append("---")

    # Per-page per-element listing
    elements_by_page: dict[int, list[ParsedElement]] = {}
    for e in elements:
        elements_by_page.setdefault(e.page_num, []).append(e)

    for page_num in pages:
        page_elems = elements_by_page[page_num]
        lines.append(f"\n## Page {page_num}")
        for elem in page_elems:
            lines.append(f"\n### [{elem.element_type}] #{elem.element_index}")
            text = _truncate(elem.text) if elem.text.strip() else "*(no text)*"
            lines.append(f"> {text}")
            lines.append(f"`bbox: {_bbox_str(elem.bbox)}`")
            if elem.is_tbc:
                lines.append("*(stitched continuation)*")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    log.info("Report 00 written → %s", out_path)
    return out_path


# ---------------------------------------------------------------------------
# Image crops
# ---------------------------------------------------------------------------

def save_all_image_crops(
    chunks: list[Chunk],
    pdf_path: Path,
    results_dir: Path,
) -> dict[str, Path]:
    """Crop all image chunks from the PDF and save as JPEG files.

    Files are named ``page_{page:04d}_chunk_{chunk_id}.jpg`` and saved under
    ``results/images/``.

    Args:
        chunks: All chunks (only image-type ones are processed).
        pdf_path: Path to the source PDF.
        results_dir: Pipeline results root directory.

    Returns:
        Mapping of chunk_id → saved image Path (only for successfully saved crops).
    """
    images_dir = _images_dir(results_dir)
    image_chunks = [c for c in chunks if c.chunk_type == "image"]
    saved: dict[str, Path] = {}

    for chunk in image_chunks:
        out_name = f"page_{chunk.page_num:04d}_chunk_{chunk.chunk_id}.jpg"
        out_path = images_dir / out_name

        if out_path.exists():
            log.debug("Image crop already exists: %s", out_path)
            saved[chunk.chunk_id] = out_path
            continue

        jpeg_bytes = crop_image_from_pdf(pdf_path, chunk.page_num, chunk.bbox)
        if jpeg_bytes is None:
            log.warning(
                "Skipped crop for chunk %s (page %d) — too small",
                chunk.chunk_id,
                chunk.page_num,
            )
            continue

        out_path.write_bytes(jpeg_bytes)
        saved[chunk.chunk_id] = out_path
        log.debug("Saved image crop → %s", out_path)

    log.info(
        "Saved %d/%d image crops → %s", len(saved), len(image_chunks), images_dir
    )
    return saved


# ---------------------------------------------------------------------------
# Reports 01 / 02 — Chunks pre- and post-captioning
# ---------------------------------------------------------------------------

def render_chunks_report(
    chunks: list[Chunk],
    results_dir: Path,
    phase: str,
    image_paths: dict[str, Path] | None = None,
) -> Path:
    """Write a chunks report Markdown file.

    Args:
        chunks: All chunks after the relevant phase.
        results_dir: Pipeline results root directory.
        phase: ``"pre_captioning"`` or ``"post_captioning"``.
        image_paths: Mapping of chunk_id → saved JPEG path from
            :func:`save_all_image_crops`.  Pass ``None`` or ``{}`` when no
            crops are available.

    Returns:
        Path to the written Markdown file.
    """
    if phase == "pre_captioning":
        filename = "01_chunks_pre_captioning.md"
        title = "Chunks Report — Pre-Captioning"
    elif phase == "post_captioning":
        filename = "02_chunks_post_captioning.md"
        title = "Chunks Report — Post-Captioning"
    else:
        raise ValueError(f"Unknown phase: {phase!r}. Expected 'pre_captioning' or 'post_captioning'.")

    out_path = _reports_dir(results_dir) / filename
    image_paths = image_paths or {}

    today = date.today().isoformat()
    type_counts: Counter[str] = Counter(c.chunk_type for c in chunks)
    total = len(chunks)

    lines: list[str] = []

    # Header
    lines.append(f"# {title}")
    lines.append(f"Generated: {today}  |  {total} chunks total")
    lines.append("")

    # Captioning summary (post only)
    if phase == "post_captioning":
        image_chunks = [c for c in chunks if c.chunk_type == "image"]
        captioned = sum(
            1 for c in image_chunks
            if c.text.strip() and not c.text.startswith("[Image")
        )
        skipped = len(image_chunks) - captioned
        lines.append("## Captioning Summary")
        lines.append(f"- {len(image_chunks)} image chunks total")
        lines.append(f"- {captioned} captioned successfully")
        lines.append(f"- {skipped} skipped (crop too small / error)")
        lines.append("")

    # Type summary table
    lines.append("## Summary")
    lines.append("| Chunk Type | Count | % of Total |")
    lines.append("|------------|-------|------------|")
    for ctype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        pct = f"{count / total * 100:.0f}%" if total else "0%"
        lines.append(f"| {ctype} | {count} | {pct} |")
    lines.append("")
    lines.append("---")

    # Per-chunk entries
    for idx, chunk in enumerate(chunks, start=1):
        section_label = f"`{chunk.section_header}`" if chunk.section_header else "*(none)*"
        lines.append(
            f"\n## Chunk {idx} — `{chunk.chunk_type}` | Page {chunk.page_num} | Section: {section_label}"
        )

        source_types = ", ".join(e.element_type for e in chunk.source_elements)
        token_est = _est_tokens(chunk.text)
        lines.append(
            f"**ID:** `{chunk.chunk_id}`  "
            f"**Source elements:** {source_types}  "
            f"**~tokens:** {token_est}"
        )

        if chunk.chunk_type == "image":
            _render_image_chunk_body(lines, chunk, phase, image_paths)
        elif chunk.chunk_type == "table":
            _render_table_chunk_body(lines, chunk)
        elif chunk.chunk_type == "bibliography":
            lines.append(f"\n> {_truncate(chunk.text, 300)}")
        else:
            # text_block
            lines.append(f"\n> {_truncate(chunk.text, 500)}")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    log.info("Report written → %s", out_path)
    return out_path


def _render_image_chunk_body(
    lines: list[str],
    chunk: Chunk,
    phase: str,
    image_paths: dict[str, Path],
) -> None:
    """Append image-chunk-specific lines to the report."""
    # Saved crop
    crop_path = image_paths.get(chunk.chunk_id)
    if crop_path:
        lines.append(f"**Saved crop:** `{crop_path}`")
    else:
        lines.append("**Saved crop:** *(not available)*")

    # Original caption from source elements
    doc_caption = " ".join(
        e.text for e in chunk.source_elements
        if e.element_type == "Caption" and e.text.strip()
    ).strip()
    if doc_caption:
        lines.append(f"**Original caption from doc:** {_truncate(doc_caption, 200)}")
    else:
        lines.append("**Original caption from doc:** *(none)*")

    # Vision caption
    if phase == "pre_captioning":
        lines.append("**Vision caption:** *(pending — run without --skip-vision)*")
    else:
        caption_text = chunk.text.strip()
        if caption_text:
            lines.append(f"**Vision caption:** {_truncate(caption_text, 400)}")
        else:
            lines.append("**Vision caption:** *(empty)*")


def _render_table_chunk_body(lines: list[str], chunk: Chunk) -> None:
    """Append table-chunk-specific lines to the report."""
    text = chunk.text.strip()
    lines.append(f"\n> {_truncate(text, 500)}")
