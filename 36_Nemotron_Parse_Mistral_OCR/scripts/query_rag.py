#!/usr/bin/env python3
"""CLI query interface for the Nemo Multi-Modal RAG pipeline.

Usage:
    cd /path/to/nemo-api
    python scripts/query_rag.py "What is the overall architecture of the Docling pipeline?"
    python scripts/query_rag.py "Describe the benchmark results table" --type table
    python scripts/query_rag.py "What does figure 1 show?" --type image
    python scripts/query_rag.py "How does Former handle table structure?" --top-k 8
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Ensure src/ is on sys.path when running without editable install
_src = Path(__file__).parent.parent / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from dotenv import load_dotenv
from openai import AsyncOpenAI
from rich.console import Console
from rich.logging import RichHandler
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from nemo_multimodal_rag.config import get_settings
from nemo_multimodal_rag.generation.generator import retrieve_and_answer
from nemo_multimodal_rag.retrieval.vector_store import get_qdrant_client

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.WARNING,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
)
console = Console()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

async def run(args: argparse.Namespace) -> None:
    load_dotenv()
    settings = get_settings()

    nim_client = AsyncOpenAI(
        base_url=settings.nvidia_base_url,
        api_key=settings.nvidia_api_key.get_secret_value(),
    )
    qdrant = await get_qdrant_client(settings)

    console.print(Panel(f"[bold cyan]Query:[/bold cyan] {args.query}", expand=False))

    answer, context_chunks = await retrieve_and_answer(
        query=args.query,
        client=nim_client,
        qdrant_client=qdrant,
        settings=settings,
        top_k=args.top_k,
        chunk_type_filter=args.type,
    )

    # ── Answer ─────────────────────────────────────────────────────────────
    console.print("\n")
    console.print(Panel(Markdown(answer), title="[bold green]Answer[/bold green]", expand=True))

    # ── Retrieved sources ──────────────────────────────────────────────────
    if args.show_sources and context_chunks:
        console.print("\n[bold]Retrieved Sources:[/bold]")
        tbl = Table(show_header=True, header_style="bold magenta")
        tbl.add_column("#", width=3)
        tbl.add_column("Score", width=6)
        tbl.add_column("Type", width=12)
        tbl.add_column("Page", width=5)
        tbl.add_column("Section", width=25)
        tbl.add_column("Excerpt", width=60)

        for i, chunk in enumerate(context_chunks, 1):
            score = f"{chunk.get('_score', 0):.3f}"
            chunk_type = chunk.get("chunk_type", "?")
            page = str(chunk.get("page_num", "?"))
            section = (chunk.get("section_header", "") or "")[:24]
            text = (chunk.get("text", "") or "").replace("\n", " ")[:59]
            tbl.add_row(str(i), score, chunk_type, page, section, text)

        console.print(tbl)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Query the Nemo Multi-Modal RAG knowledge base.",
    )
    parser.add_argument("query", help="Natural language question to answer")
    parser.add_argument(
        "--type",
        choices=["text_block", "table", "image", "bibliography"],
        default=None,
        help="Filter retrieved chunks to a specific type",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of context chunks to retrieve (default: 5)",
    )
    parser.add_argument(
        "--show-sources",
        action="store_true",
        default=True,
        help="Print the retrieved source chunks (default: True)",
    )
    parser.add_argument(
        "--no-sources",
        dest="show_sources",
        action="store_false",
        help="Hide retrieved source chunks",
    )
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(run(parse_args()))
