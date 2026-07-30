#!/usr/bin/env python3
"""Ingest pipeline: Phases 1-5.

Orchestrates the full ingestion pipeline:
  1. Parse raw nemotron-parse results
  2. Stitch <tbc> continuations
  3. Semantic chunking
  4. Vision captioning of image chunks
  5. Embedding
  6. Qdrant indexing

Usage:
    cd /path/to/nemo-api
    python scripts/ingest.py
    python scripts/ingest.py --pdf path/to/doc.pdf --results-dir ./results
    python scripts/ingest.py --skip-vision   # skip vision captioning (faster, offline)
    python scripts/ingest.py --recreate      # drop and recreate the Qdrant collection
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

# Ensure src/ is on sys.path when running without editable install
_src = Path(__file__).parent.parent / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from dotenv import load_dotenv
from openai import AsyncOpenAI
from rich.console import Console
from rich.logging import RichHandler

from nemo_multimodal_rag.config import get_settings
from nemo_multimodal_rag.ingestion.chunker import chunk_elements, chunks_to_dict
from nemo_multimodal_rag.ingestion.embedder import embed_chunks
from nemo_multimodal_rag.ingestion.image_captioner import caption_all_image_chunks
from nemo_multimodal_rag.ingestion.parser import parse_raw_results, stitch_continuations
from nemo_multimodal_rag.reporting.reports import (
    render_chunks_report,
    render_parsed_document,
    save_all_image_crops,
)
from nemo_multimodal_rag.retrieval.vector_store import (
    ensure_collection,
    get_qdrant_client,
    upsert_chunks,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
)
log = logging.getLogger("ingest")
console = Console()


# ---------------------------------------------------------------------------
# Embedding text selection per chunk type
# ---------------------------------------------------------------------------

def _chunk_embed_text(chunk) -> str:
    """Return the text to embed for a given chunk type."""
    text = chunk.text.strip()
    if not text:
        # Fallback for uncaptioned images or empty chunks
        parts = []
        if chunk.section_header:
            parts.append(chunk.section_header)
        parts.append(f"[{chunk.chunk_type}]")
        return " ".join(parts)
    return text


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

async def run(args: argparse.Namespace) -> None:
    load_dotenv()
    settings = get_settings()

    # Override paths from CLI if provided
    if args.pdf:
        settings.pdf_path = Path(args.pdf)
    if args.results_dir:
        settings.results_dir = Path(args.results_dir)

    console.rule("[bold cyan]Nemo Multi-Modal RAG — Ingestion Pipeline[/bold cyan]")

    # ── Phase 1: Parse raw results ─────────────────────────────────────────
    console.print("\n[bold]Phase 1:[/bold] Parsing raw results…")
    elements = parse_raw_results(settings.results_dir)

    # ── Phase 1b: Stitch continuations ────────────────────────────────────
    elements = stitch_continuations(elements)

    # ── Report 00: Parsed document view ───────────────────────────────────
    report_00 = render_parsed_document(elements, settings.results_dir)
    console.print(f"  Report → {report_00}")

    # ── Phase 2: Chunk ─────────────────────────────────────────────────────
    console.print("\n[bold]Phase 2:[/bold] Semantic chunking…")
    chunks = chunk_elements(elements)

    # Save chunks to disk for debugging
    chunks_dir = settings.results_dir / "chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)
    chunks_json_path = chunks_dir / "chunks.json"
    chunks_json_path.write_text(
        json.dumps(chunks_to_dict(chunks), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    console.print(f"  Saved {len(chunks)} chunks → {chunks_json_path}")

    # ── Report 01: Chunks pre-captioning + save image crops ───────────────
    image_paths: dict[str, Any] = {}
    if settings.pdf_path.exists():
        image_paths = save_all_image_crops(chunks, settings.pdf_path, settings.results_dir)
    report_01 = render_chunks_report(
        chunks, settings.results_dir, phase="pre_captioning", image_paths=image_paths
    )
    console.print(f"  Report → {report_01}")

    # ── NIM client (shared for vision, embedding, LLM) ────────────────────
    nim_client = AsyncOpenAI(
        base_url=settings.nvidia_base_url,
        api_key=settings.nvidia_api_key.get_secret_value(),
    )

    # ── Phase 3: Vision captioning ─────────────────────────────────────────
    if not args.skip_vision:
        image_chunk_count = sum(1 for c in chunks if c.chunk_type == "image")
        console.print(f"\n[bold]Phase 3:[/bold] Vision captioning {image_chunk_count} image chunk(s)…")
        if not settings.pdf_path.exists():
            console.print(
                f"  [yellow]Warning:[/yellow] PDF not found at {settings.pdf_path} — "
                "skipping vision captioning."
            )
        else:
            chunks = await caption_all_image_chunks(chunks, settings.pdf_path, settings, nim_client)
    else:
        console.print("\n[bold]Phase 3:[/bold] Skipped (--skip-vision).")

    # ── Report 02: Chunks post-captioning ──────────────────────────────────
    report_02 = render_chunks_report(
        chunks, settings.results_dir, phase="post_captioning", image_paths=image_paths
    )
    console.print(f"  Report → {report_02}")

    # ── Phase 4: Embed ─────────────────────────────────────────────────────
    console.print(f"\n[bold]Phase 4:[/bold] Embedding {len(chunks)} chunks…")
    embed_texts = [_chunk_embed_text(c) for c in chunks]
    embeddings = await embed_chunks(embed_texts, nim_client, settings, input_type="passage")

    # ── Phase 5: Qdrant indexing ───────────────────────────────────────────
    console.print("\n[bold]Phase 5:[/bold] Indexing to Qdrant…")
    qdrant = await get_qdrant_client(settings)

    if args.recreate:
        try:
            await qdrant.delete_collection(settings.qdrant_collection_name)
            console.print(f"  Dropped existing collection '{settings.qdrant_collection_name}'.")
        except Exception:
            pass

    await ensure_collection(qdrant, settings)
    await upsert_chunks(chunks, embeddings, qdrant, settings)

    console.rule(
        f"[bold green]Done — {len(chunks)} chunks indexed to "
        f"'{settings.qdrant_collection_name}'[/bold green]"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Nemo Multi-Modal RAG ingestion pipeline (Phases 1–5).",
    )
    parser.add_argument("--pdf", default=None, help="Path to source PDF (overrides config)")
    parser.add_argument(
        "--results-dir",
        default=None,
        help="Directory with *_raw.json results (overrides config)",
    )
    parser.add_argument(
        "--skip-vision",
        action="store_true",
        help="Skip Phase 3 vision captioning (useful for offline testing)",
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Drop and recreate the Qdrant collection before indexing",
    )
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(run(parse_args()))
