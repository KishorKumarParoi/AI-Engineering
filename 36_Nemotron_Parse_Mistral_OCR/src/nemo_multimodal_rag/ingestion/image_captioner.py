"""Phase 3: Crop PDF images and generate vision captions via NVIDIA NIM."""

from __future__ import annotations

import asyncio
import base64
import logging
from pathlib import Path

import pymupdf as fitz
from openai import AsyncOpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from nemo_multimodal_rag.config import Settings
from nemo_multimodal_rag.ingestion.chunker import Chunk

log = logging.getLogger(__name__)

# Minimum pixel dimensions — crops smaller than this are skipped
_MIN_CROP_PX = 50

# Semaphore limit for concurrent vision API calls
_CONCURRENCY = 3

# Caption cache file naming
_CACHE_PREFIX = "page_{page:04d}_chunk_{chunk_id}_caption.txt"


# ---------------------------------------------------------------------------
# Image cropping
# ---------------------------------------------------------------------------

def crop_image_from_pdf(
    pdf_path: Path,
    page_num: int,
    bbox: dict,
    zoom: float = 2.0,
) -> bytes | None:
    """Rasterize a bounding-box region of a PDF page and return JPEG bytes.

    The bbox coordinates are normalised (0.0–1.0) relative to page dimensions.
    The region is rasterised at ``zoom`` × the native resolution.

    Args:
        pdf_path: Path to the source PDF.
        page_num: 0-indexed page number.
        bbox: Normalised bbox dict with keys xmin, ymin, xmax, ymax.
        zoom: Rasterisation zoom factor (default 2.0 for good quality).

    Returns:
        JPEG bytes, or None if the crop is too small to be useful.
    """
    doc = fitz.open(str(pdf_path))
    try:
        page = doc[page_num]
        pw = page.rect.width
        ph = page.rect.height

        # Denormalise to page coordinates (points)
        x0 = bbox["xmin"] * pw
        y0 = bbox["ymin"] * ph
        x1 = bbox["xmax"] * pw
        y1 = bbox["ymax"] * ph
        clip_rect = fitz.Rect(x0, y0, x1, y1)

        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, clip=clip_rect, colorspace=fitz.csRGB)

        # Skip tiny crops
        if pix.width < _MIN_CROP_PX or pix.height < _MIN_CROP_PX:
            log.debug(
                "Skipping crop on page %d — %dx%d px is below minimum",
                page_num,
                pix.width,
                pix.height,
            )
            return None

        return pix.tobytes("jpg", jpg_quality=90)
    finally:
        doc.close()


# ---------------------------------------------------------------------------
# Vision captioning
# ---------------------------------------------------------------------------

@retry(
    retry=retry_if_exception_type(Exception),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(3),
    reraise=True,
)
async def _call_vision_api(
    jpeg_bytes: bytes,
    nearby_caption: str,
    section_context: str,
    client: AsyncOpenAI,
    settings: Settings,
) -> str:
    """Call the NIM vision model to caption a cropped image.

    Args:
        jpeg_bytes: JPEG bytes of the cropped figure.
        nearby_caption: OCR-extracted caption text near the figure (may be empty).
        section_context: Current section header for context (may be empty).
        client: Shared AsyncOpenAI NIM client.
        settings: Pipeline settings.

    Returns:
        Caption string from the vision model.
    """
    b64 = base64.b64encode(jpeg_bytes).decode("utf-8")
    data_url = f"data:image/jpeg;base64,{b64}"

    context_parts = []
    if section_context:
        context_parts.append(f"This figure appears in the section: '{section_context}'.")
    if nearby_caption:
        context_parts.append(f"The document caption reads: '{nearby_caption}'.")
    context_str = " ".join(context_parts)

    prompt = (
        "You are analyzing a figure extracted from a technical research paper about "
        "the Docling document conversion system. "
        f"{context_str} "
        "Please provide a concise, factual description (2-4 sentences) of what this "
        "figure shows, including any key data, labels, or structure visible."
    )

    response = await client.chat.completions.create(
        model=settings.nvidia_vision_model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_url}},
                    {"type": "text", "text": prompt},
                ],
            }
        ],
        max_tokens=300,
        temperature=0.1,
    )
    return response.choices[0].message.content or ""


async def caption_image_with_nim(
    jpeg_bytes: bytes,
    nearby_caption: str,
    section_context: str,
    client: AsyncOpenAI,
    settings: Settings,
) -> str:
    """Public wrapper around the vision API call.

    Args:
        jpeg_bytes: JPEG bytes of the cropped figure.
        nearby_caption: Caption text from the source document.
        section_context: Section header for context.
        client: AsyncOpenAI NIM client.
        settings: Pipeline settings.

    Returns:
        Generated caption string.
    """
    return await _call_vision_api(jpeg_bytes, nearby_caption, section_context, client, settings)


# ---------------------------------------------------------------------------
# Batch processing with caching
# ---------------------------------------------------------------------------

def _caption_cache_path(cache_dir: Path, page_num: int, chunk_id: str) -> Path:
    return cache_dir / _CACHE_PREFIX.format(page=page_num, chunk_id=chunk_id)


async def _caption_one_chunk(
    chunk: Chunk,
    pdf_path: Path,
    cache_dir: Path,
    client: AsyncOpenAI,
    settings: Settings,
    semaphore: asyncio.Semaphore,
) -> None:
    """Caption a single image chunk in-place, using cache if available."""
    cache_file = _caption_cache_path(cache_dir, chunk.page_num, chunk.chunk_id)

    # Return cached result
    if cache_file.exists():
        chunk.text = cache_file.read_text(encoding="utf-8").strip()
        log.debug("Caption cache hit: %s", cache_file.name)
        return

    # Extract nearby caption text from source elements
    nearby_caption = " ".join(
        e.text
        for e in chunk.source_elements
        if e.element_type == "Caption" and e.text.strip()
    )

    # Crop image
    jpeg_bytes = crop_image_from_pdf(pdf_path, chunk.page_num, chunk.bbox)
    if jpeg_bytes is None:
        log.warning(
            "Chunk %s (page %d): crop too small, skipping vision captioning",
            chunk.chunk_id,
            chunk.page_num,
        )
        chunk.text = nearby_caption or "[Image: crop too small to process]"
        return

    async with semaphore:
        try:
            caption = await caption_image_with_nim(
                jpeg_bytes,
                nearby_caption,
                chunk.section_header,
                client,
                settings,
            )
        except Exception as exc:
            log.error(
                "Vision captioning failed for chunk %s (page %d): %s",
                chunk.chunk_id,
                chunk.page_num,
                exc,
            )
            caption = nearby_caption or "[Image: captioning failed]"

    chunk.text = caption

    # Persist to cache
    cache_file.write_text(caption, encoding="utf-8")
    log.info("Captioned chunk %s (page %d): %.60s…", chunk.chunk_id, chunk.page_num, caption)


async def caption_all_image_chunks(
    chunks: list[Chunk],
    pdf_path: Path,
    settings: Settings,
    client: AsyncOpenAI,
) -> list[Chunk]:
    """Caption all image-type chunks in the chunk list.

    Uses a semaphore to limit concurrent API calls and caches results to
    ``results/image_captions/`` for idempotent re-runs.

    Args:
        chunks: All chunks (only image-type ones are processed).
        pdf_path: Source PDF path for cropping.
        settings: Pipeline settings (cache dir derived from results_dir).
        client: AsyncOpenAI NIM client.

    Returns:
        The same chunk list with image chunk ``text`` fields populated.
    """
    cache_dir = settings.results_dir / "image_captions"
    cache_dir.mkdir(parents=True, exist_ok=True)

    image_chunks = [c for c in chunks if c.chunk_type == "image"]
    if not image_chunks:
        log.info("No image chunks to caption.")
        return chunks

    semaphore = asyncio.Semaphore(_CONCURRENCY)
    tasks = [
        _caption_one_chunk(chunk, pdf_path, cache_dir, client, settings, semaphore)
        for chunk in image_chunks
    ]
    await asyncio.gather(*tasks)

    captioned = sum(1 for c in image_chunks if c.text and not c.text.startswith("[Image"))
    log.info("Captioned %d/%d image chunks.", captioned, len(image_chunks))
    return chunks
