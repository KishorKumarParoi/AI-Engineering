# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment Setup

```bash
# Activate the pre-existing venv (Python 3.12, managed by uv)
source .venv/bin/activate

# Install all deps (including dev extras)
uv pip install -e ".[dev]"
```

Required `.env` keys:
```
NVIDIA_API_KEY=...         # for nemotron-parse, NIM vision/embed/LLM
MISTRAL_API_KEY=...        # for Mistral OCR only
UNLIMITED_OCR_URL=...      # vLLM OpenAI-compatible endpoint for Baidu Unlimited-OCR
QDRANT_URL=http://localhost:6333
```

Qdrant must be running locally before ingestion or querying:
```bash
docker run -p 6333:6333 qdrant/qdrant:v1.13.3
```

## Commands

**Lint:**
```bash
ruff check src/ scripts/ unlimited_ocr/ nemotron_parse_pipeline.py
ruff format --check src/ scripts/ unlimited_ocr/ nemotron_parse_pipeline.py
```

**Tests (no test suite yet — run manually):**
```bash
pytest
```

**Parse a PDF with Nemotron (CLI pipeline):**
```bash
python nemotron_parse_pipeline.py --pdf path/to/doc.pdf --output ./results
python nemotron_parse_pipeline.py --pdf path/to/doc.pdf --output ./results --pages 0 1 2
python nemotron_parse_pipeline.py --pdf path/to/doc.pdf --output ./results --zoom 2.5 --max-tokens 8192 --save-images
```

**Ingest into Qdrant (Phases 1–5):**
```bash
python scripts/ingest.py
python scripts/ingest.py --pdf path/to/doc.pdf --results-dir ./results
python scripts/ingest.py --skip-vision    # skip image captioning
python scripts/ingest.py --recreate       # drop and recreate Qdrant collection
```

**Query the RAG knowledge base:**
```bash
python scripts/query_rag.py "Your question here"
python scripts/query_rag.py "Describe the table" --type table
python scripts/query_rag.py "What does the figure show?" --type image --top-k 8
```

**Streamlit UIs:**
```bash
streamlit run scripts/visualize_parse.py        # Nemotron-Parse inspector
streamlit run scripts/visualize_mistral_ocr.py  # Mistral OCR inspector
streamlit run unlimited_ocr/app.py              # Unlimited-OCR inspector
```

## Architecture

Two separate subsystems share the same repo:

### 1. Standalone CLI pipeline (`nemotron_parse_pipeline.py`)
Self-contained script — no `src/` imports. Converts PDF pages to JPEG base64, POSTs to `https://integrate.api.nvidia.com/v1/chat/completions` using model `nvidia/nemotron-parse`. The API requires:
- `messages[0].content` as a plain HTML string with an embedded `<img>` tag (NOT a content array)
- `tools` as a list of dicts with `{"type": "function", "function": {"name": "<mode>"}}` where mode is one of `markdown_bbox` / `markdown_no_bbox` / `detection_only`
- Response content lives in `tool_calls[0].function.arguments` (a JSON string), not `message.content`

Outputs per page: `*_raw.json` (full API response) + `*_parsed.md` (extracted text).

### 2. Multi-modal RAG package (`src/nemo_multimodal_rag/`)

Full ingestion → retrieval → generation pipeline. All NIM calls share a single `AsyncOpenAI` client configured with `base_url=https://integrate.api.nvidia.com/v1`.

**Data flow:**

```
PDF → nemotron_parse_pipeline.py → results/*_raw.json
                                         │
                              scripts/ingest.py
                                         │
              ┌──────────────────────────┼──────────────────────────┐
         Phase 1                    Phase 2                    Phase 3
    parser.py                   chunker.py               image_captioner.py
  ParsedElement[]  →  stitch  →  Chunk[]  →  image crops  →  vision captions
  (+ <tbc> merge)              (text_block                  (meta/llama-3.2-90b
                                table, image,                vision-instruct NIM)
                                bibliography)
                                         │
                              Phase 4: embedder.py
                           (nvidia/nv-embedqa-e5-v5, dim=1024)
                                         │
                              Phase 5: vector_store.py
                               (AsyncQdrantClient, cosine, HNSW)
                                         │
                              scripts/query_rag.py
                           retrieval → meta/llama-3.1-70b-instruct
```

**Key data models:**
- `ParsedElement` — one semantic element from a PDF page (type, text, bbox, page_num)
- `Chunk` — indexable unit: `chunk_type` ∈ `{text_block, table, image, bibliography}`, merged bbox, section_header, doc_title
- Qdrant payload fields: `chunk_id`, `chunk_type`, `text`, `original_caption`, `page_num`, `bbox`, `section_header`, `doc_title`, `source_element_types`

**Retrieval filter behaviour:** bibliography chunks excluded by default; pass `--type` to filter to a specific chunk type.

**`<tbc>` stitching:** nemotron-parse appends `<tbc>` when it hits max tokens mid-element. `stitch_continuations()` in `parser.py` merges these across page boundaries before chunking.

**Image captioner caching:** captions are written to `results/image_captions/page_XXXX_chunk_YYYY_caption.txt`; re-runs reuse cached files automatically.

### 3. Streamlit visual inspectors (`scripts/`)
- `visualize_parse.py` — uploads PDF, calls nemotron-parse per page, draws color-coded bboxes by element type. Imports `call_with_retries`, `compute_zoom`, `page_to_base64_jpeg` from `nemotron_parse_pipeline.py` at the repo root.
- `visualize_mistral_ocr.py` — uploads PDF, sends entire document to Mistral OCR API in one shot, shows per-page markdown + image region overlays.

### 4. Unlimited-OCR inspector (`unlimited_ocr/`)
Standalone Streamlit app (own top-level folder, no shared imports). Calls Baidu's `Unlimited-OCR` model (MIT license) via a self-hosted vLLM OpenAI-compatible endpoint (`UNLIMITED_OCR_URL`, no API key — vLLM auth is `EMPTY`). Prompt must start with the literal `<image>` token or the model returns empty output; `window_size` is 128 for single images, 1024 for multi-page PDFs. Raw output has grounding tokens `<|ref|>`/`<|det|>` stripped by `clean_ocr_output()`. See `unlimited_ocr/README.md`.

## API Quirks

- `qdrant-client >= 1.16.0`: use `query_points()` not `search()`, `upsert()` not `upload_records()`
- nemotron-parse: image must be within 1024×1280 – 1648×2048 px; `compute_zoom()` enforces this
- JPEG quality auto-steps down from 92→60 to stay under the 4 MB payload limit
- HTTP 400/401/403/404/422 are non-retryable; 5xx retries with exponential backoff (3 attempts)
