"""Phase 2: Semantic chunking of parsed elements into indexable chunks."""

from __future__ import annotations

import dataclasses
import logging
import uuid
from typing import Any

from nemo_multimodal_rag.ingestion.parser import ParsedElement

log = logging.getLogger(__name__)

# Approximate token count threshold for flushing a text block
_TOKEN_CAP = 1200

# Element types that signal special chunking behaviour
_TABLE_TYPE = "Table"
_PICTURE_TYPE = "Picture"
_CAPTION_TYPE = "Caption"
_BIBLIOGRAPHY_TYPE = "Bibliography"
_SECTION_HEADER_TYPE = "Section-header"
_LIST_ITEM_TYPE = "List-item"

# Fraction of page height used as the proximity threshold for caption absorption
_CAPTION_PROXIMITY_THRESHOLD = 0.05


@dataclasses.dataclass
class Chunk:
    """A unit of content ready for embedding and indexing."""

    chunk_id: str
    chunk_type: str  # "text_block" | "table" | "image" | "bibliography"
    text: str
    source_elements: list[ParsedElement]
    page_num: int
    bbox: dict  # merged bounding box in normalised coords
    section_header: str
    doc_title: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _est_tokens(text: str) -> int:
    """Rough token estimate — 4 characters ≈ 1 token for English text."""
    return len(text) // 4


def _merge_bboxes(bboxes: list[dict]) -> dict:
    """Return the union bounding box of a list of bbox dicts."""
    if not bboxes:
        return {"xmin": 0.0, "ymin": 0.0, "xmax": 1.0, "ymax": 1.0}
    return {
        "xmin": min(b["xmin"] for b in bboxes),
        "ymin": min(b["ymin"] for b in bboxes),
        "xmax": max(b["xmax"] for b in bboxes),
        "ymax": max(b["ymax"] for b in bboxes),
    }


def _make_chunk_id() -> str:
    return str(uuid.uuid4())[:8]


# ---------------------------------------------------------------------------
# Core chunker
# ---------------------------------------------------------------------------

def chunk_elements(
    elements: list[ParsedElement],
    doc_title: str = "Docling Technical Report",
) -> list[Chunk]:
    """Convert a flat list of ParsedElements into semantic Chunk objects.

    Processing is done page by page in element order, applying these rules:
    - Tables are atomic; the immediately following Caption is absorbed as prefix.
    - Pictures become ``chunk_type="image"`` chunks; nearby Caption absorbed.
    - Section-headers flush the current block and update the section context.
    - List-items append with a ``-`` prefix.
    - Consecutive Bibliography elements merge into one bibliography chunk.
    - Orphan Captions append to the current text block.
    - Text blocks are flushed when they exceed the 1200-token cap.

    Args:
        elements: Stitched elements in reading order (output of stitch_continuations).
        doc_title: Document title stored as metadata on every chunk.

    Returns:
        List of Chunk objects ready for embedding.
    """
    chunks: list[Chunk] = []
    section_header: str = ""
    current_block_texts: list[str] = []
    current_block_elements: list[ParsedElement] = []

    def flush_block() -> None:
        nonlocal current_block_texts, current_block_elements
        if not current_block_texts:
            return
        text = "\n\n".join(current_block_texts)
        bbox = _merge_bboxes([e.bbox for e in current_block_elements])
        page = current_block_elements[0].page_num if current_block_elements else 0
        chunks.append(
            Chunk(
                chunk_id=_make_chunk_id(),
                chunk_type="text_block",
                text=text,
                source_elements=list(current_block_elements),
                page_num=page,
                bbox=bbox,
                section_header=section_header,
                doc_title=doc_title,
            )
        )
        current_block_texts = []
        current_block_elements = []

    def maybe_flush_on_token_cap() -> None:
        combined = "\n\n".join(current_block_texts)
        if _est_tokens(combined) >= _TOKEN_CAP:
            flush_block()

    def _nearby_caption(
        base_elem: ParsedElement,
        candidates: list[ParsedElement],
    ) -> ParsedElement | None:
        """Return the first Caption candidate within proximity of base_elem.

        Checks both above (caption before element) and below (caption after)
        because academic papers often place table/figure captions above the
        element itself.
        """
        for cand in candidates:
            if cand.element_type != _CAPTION_TYPE:
                return None
            # Minimum gap in either direction
            gap = min(
                abs(cand.bbox["ymin"] - base_elem.bbox["ymax"]),
                abs(base_elem.bbox["ymin"] - cand.bbox["ymax"]),
            )
            if gap <= _CAPTION_PROXIMITY_THRESHOLD:
                return cand
        return None

    i = 0
    while i < len(elements):
        elem = elements[i]
        etype = elem.element_type

        # ── Section-header ────────────────────────────────────────────────
        if etype == _SECTION_HEADER_TYPE:
            flush_block()
            # Store clean header (strip leading markdown #) for metadata
            section_header = elem.text.lstrip("#").strip()
            # Begin new block with the formatted header so it's part of the text
            current_block_texts.append(f"## {section_header}")
            current_block_elements.append(elem)
            i += 1

        # ── Table ─────────────────────────────────────────────────────────
        elif etype == _TABLE_TYPE:
            flush_block()
            # Lookahead for a nearby Caption
            lookahead = elements[i + 1 : i + 2]
            caption_elem = _nearby_caption(elem, lookahead)

            table_text = elem.text
            src: list[ParsedElement] = [elem]
            if caption_elem is not None:
                table_text = f"Caption: {caption_elem.text}\n\n{table_text}"
                src.append(caption_elem)
                i += 1  # consume the caption

            chunks.append(
                Chunk(
                    chunk_id=_make_chunk_id(),
                    chunk_type="table",
                    text=table_text,
                    source_elements=src,
                    page_num=elem.page_num,
                    bbox=_merge_bboxes([e.bbox for e in src]),
                    section_header=section_header,
                    doc_title=doc_title,
                )
            )
            i += 1

        # ── Picture ───────────────────────────────────────────────────────
        elif etype == _PICTURE_TYPE:
            flush_block()
            # Lookahead for a nearby Caption
            lookahead = elements[i + 1 : i + 2]
            caption_elem = _nearby_caption(elem, lookahead)

            src = [elem]
            if caption_elem is not None:
                src.append(caption_elem)
                i += 1  # consume the caption

            chunks.append(
                Chunk(
                    chunk_id=_make_chunk_id(),
                    chunk_type="image",
                    text="",  # filled in by Phase 3 image captioning
                    source_elements=src,
                    page_num=elem.page_num,
                    bbox=elem.bbox,  # use Picture bbox (not merged) for cropping
                    section_header=section_header,
                    doc_title=doc_title,
                )
            )
            i += 1

        # ── Bibliography ──────────────────────────────────────────────────
        elif etype == _BIBLIOGRAPHY_TYPE:
            flush_block()
            bib_elements = [elem]
            bib_texts = [elem.text]
            i += 1
            while i < len(elements) and elements[i].element_type == _BIBLIOGRAPHY_TYPE:
                bib_elements.append(elements[i])
                bib_texts.append(elements[i].text)
                i += 1

            chunks.append(
                Chunk(
                    chunk_id=_make_chunk_id(),
                    chunk_type="bibliography",
                    text="\n\n".join(bib_texts),
                    source_elements=bib_elements,
                    page_num=bib_elements[0].page_num,
                    bbox=_merge_bboxes([e.bbox for e in bib_elements]),
                    section_header=section_header,
                    doc_title=doc_title,
                )
            )
            # i already advanced past last bibliography element

        # ── List-item ─────────────────────────────────────────────────────
        elif etype == _LIST_ITEM_TYPE:
            current_block_texts.append(f"- {elem.text}")
            current_block_elements.append(elem)
            maybe_flush_on_token_cap()
            i += 1

        # ── Orphan Caption ────────────────────────────────────────────────
        elif etype == _CAPTION_TYPE:
            # Caption not absorbed by Table/Picture — treat as inline label
            current_block_texts.append(elem.text)
            current_block_elements.append(elem)
            i += 1

        # ── Text, Title, and everything else ─────────────────────────────
        else:
            current_block_texts.append(elem.text)
            current_block_elements.append(elem)
            maybe_flush_on_token_cap()
            i += 1

    # Flush any remaining text
    flush_block()

    log.info(
        "Chunked %d elements → %d chunks (%s)",
        len(elements),
        len(chunks),
        ", ".join(
            f"{t}={sum(1 for c in chunks if c.chunk_type == t)}"
            for t in ("text_block", "table", "image", "bibliography")
        ),
    )
    return chunks


def chunks_to_dict(chunks: list[Chunk]) -> list[dict[str, Any]]:
    """Serialise chunks to JSON-safe dicts (for saving to results/chunks/chunks.json)."""
    out = []
    for c in chunks:
        out.append(
            {
                "chunk_id": c.chunk_id,
                "chunk_type": c.chunk_type,
                "text": c.text,
                "page_num": c.page_num,
                "bbox": c.bbox,
                "section_header": c.section_header,
                "doc_title": c.doc_title,
                "source_element_types": [e.element_type for e in c.source_elements],
            }
        )
    return out
