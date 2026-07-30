# Nemotron-Parse + Mistral OCR — Multi-Modal RAG Pipeline

A production-grade multi-modal RAG pipeline that extracts structured content from PDFs using **NVIDIA Nemotron-Parse** and **Mistral OCR**, chunks it by semantic type, generates vision captions for figures, embeds everything with NVIDIA NIM, and indexes into Qdrant for grounded Q&A.

---

## Architecture

```
PDF
 │
 ├─► nemotron_parse_pipeline.py
 │       • Rasterize each page to JPEG (auto-zoom to 1024×1280–1648×2048 px)
 │       • POST to nvidia/nemotron-parse via NVIDIA NIM
 │       • Output: results/*_raw.json  +  *_parsed.md
 │
 └─► scripts/ingest.py  (Phases 1–5)
         │
         ├─ Phase 1  parser.py          ParsedElement[] from *_raw.json
         │           stitch_continuations()  merge <tbc> cross-page splits
         │
         ├─ Phase 2  chunker.py         Chunk[]
         │           chunk_type ∈ {text_block, table, image, bibliography}
         │
         ├─ Phase 3  image_captioner.py  crop PDF bbox → vision caption
         │           model: meta/llama-3.2-90b-vision-instruct (NIM)
         │           cached to results/image_captions/
         │
         ├─ Phase 4  embedder.py         1024-dim dense vectors
         │           model: nvidia/nv-embedqa-e5-v5 (NIM)
         │
         └─ Phase 5  vector_store.py     AsyncQdrantClient upsert (cosine HNSW)

scripts/query_rag.py
    • embed query  →  Qdrant query_points()  →  meta/llama-3.1-70b-instruct
```

All NIM calls share a single `AsyncOpenAI` client pointed at `https://integrate.api.nvidia.com/v1`.

---

## Key Data Models

| Model | Fields |
|---|---|
| `ParsedElement` | `page_num`, `element_type`, `text`, `bbox`, `is_tbc` |
| `Chunk` | `chunk_id`, `chunk_type`, `text`, `page_num`, `bbox`, `section_header`, `doc_title` |
| Qdrant payload | `chunk_id`, `chunk_type`, `text`, `original_caption`, `page_num`, `bbox`, `section_header`, `doc_title`, `source_element_types` |

Chunk types: `text_block` · `table` · `image` · `bibliography`

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.12+ |
| uv | latest |
| Docker | for local Qdrant |

API keys required:
- `NVIDIA_API_KEY` — [build.nvidia.com](https://build.nvidia.com)
- `MISTRAL_API_KEY` — [console.mistral.ai](https://console.mistral.ai) *(Mistral OCR UI only)*
- `UNLIMITED_OCR_URL` — your own self-hosted vLLM endpoint *(Unlimited-OCR UI only, no API key needed)*

---

## Setup

```bash
# 1. Clone
git clone https://github.com/sourangshupal/nemotron-parse-mistral-ocr.git
cd nemotron-parse-mistral-ocr

# 2. Virtual environment (Python 3.12)
uv venv --python 3.12
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install dependencies
uv pip install -e ".[dev]"

# 4. Configure environment
cp .env.example .env               # then fill in your keys
```

`.env` template:
```dotenv
NVIDIA_API_KEY=nvapi-...
MISTRAL_API_KEY=...
UNLIMITED_OCR_URL=http://<your-vllm-host>:8000/v1
QDRANT_URL=http://localhost:6333
```

```bash
# 5. Start Qdrant
docker run -p 6333:6333 qdrant/qdrant:v1.13.3
```

---

## Usage

### Step 1 — Parse PDF with Nemotron-Parse

```bash
# All pages
python nemotron_parse_pipeline.py --pdf path/to/doc.pdf --output ./results

# Specific pages (0-indexed)
python nemotron_parse_pipeline.py --pdf path/to/doc.pdf --output ./results --pages 0 1 2

# Higher resolution for dense pages
python nemotron_parse_pipeline.py --pdf path/to/doc.pdf --output ./results --zoom 2.5

# Increase token budget for pages with lots of content
python nemotron_parse_pipeline.py --pdf path/to/doc.pdf --output ./results --max-tokens 8192

# Save page images for inspection
python nemotron_parse_pipeline.py --pdf path/to/doc.pdf --output ./results --save-images
```

Outputs per page: `results/<stem>_page_NNNN_raw.json` + `results/<stem>_page_NNNN_parsed.md`

---

### Step 2 — Ingest into Qdrant (Phases 1–5)

```bash
# Default (reads results/ and docling_report.pdf from config)
python scripts/ingest.py

# Custom paths
python scripts/ingest.py --pdf path/to/doc.pdf --results-dir ./results

# Skip vision captioning (faster, no meta/llama-3.2-90b calls)
python scripts/ingest.py --skip-vision

# Drop and recreate the Qdrant collection
python scripts/ingest.py --recreate
```

Reports saved to `results/reports/`:
- `00_parsed_document.md` — all elements from Phase 1
- `01_chunks_pre_captioning.md` — chunks before vision captions
- `02_chunks_post_captioning.md` — chunks after vision captions

---

### Step 3 — Query the RAG Knowledge Base

```bash
# Basic question
python scripts/query_rag.py "What is the overall architecture?"

# Filter to a specific chunk type
python scripts/query_rag.py "Describe the benchmark table" --type table
python scripts/query_rag.py "What does the figure show?" --type image
python scripts/query_rag.py "List key references" --type bibliography

# Retrieve more context
python scripts/query_rag.py "How does the pipeline handle images?" --top-k 8

# Hide source chunks
python scripts/query_rag.py "Summarize the paper" --no-sources
```

---

### Streamlit Visual Inspectors — Classroom Quickstart

Three independent, standalone inspectors — one per OCR engine. All share the same `.venv` / `uv`-managed dependencies; no extra install needed beyond the Setup steps above. Pick whichever engine you want to demo and run its command — each opens in the browser at `http://localhost:8501` (Streamlit picks the next free port if you run more than one at once).

| # | Engine | What it shows | Command |
|---|---|---|---|
| 1 | **Nemotron-Parse** (NVIDIA NIM) | Upload a PDF, parse page-by-page, see color-coded bounding boxes by element type (title/text/table/image/...) | `streamlit run scripts/visualize_parse.py` |
| 2 | **Mistral OCR** | Upload a PDF, run full-document OCR in one shot, inspect markdown + image-region overlays per page | `streamlit run scripts/visualize_mistral_ocr.py` |
| 3 | **Unlimited-OCR** (Baidu, self-hosted vLLM) | Upload an image or PDF, run OCR against your own vLLM server, inspect clean/raw markdown + color-coded bounding boxes per page | `streamlit run unlimited_ocr/app.py` |

**1 — Nemotron-Parse Inspector** (needs `NVIDIA_API_KEY` in `.env`):
```bash
streamlit run scripts/visualize_parse.py
```

**2 — Mistral OCR Inspector** (needs `MISTRAL_API_KEY` in `.env`, or paste it into the sidebar):
```bash
streamlit run scripts/visualize_mistral_ocr.py
```

**3 — Unlimited-OCR Inspector** (needs a running vLLM server + `UNLIMITED_OCR_URL` in `.env`):
```bash
# One-time: start the model server on a GPU host (see unlimited_ocr/README.md for full details)
docker run -d --gpus all \
  --privileged --ipc=host \
  -p 8000:8000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  --name unlimited-ocr \
  vllm/vllm-openai:unlimited-ocr \
  baidu/Unlimited-OCR \
  --trust-remote-code \
  --logits_processors vllm.model_executor.models.unlimited_ocr:NGramPerReqLogitsProcessor \
  --no-enable-prefix-caching \
  --mm-processor-cache-gb 0 \
  --tensor-parallel-size 1

# Then run the app
streamlit run unlimited_ocr/app.py
```

See `unlimited_ocr/README.md` for troubleshooting (missing bounding boxes, empty output, token-repeat loops).

---

## Development

```bash
# Lint
ruff check src/ scripts/ unlimited_ocr/ nemotron_parse_pipeline.py

# Format check
ruff format --check src/ scripts/ unlimited_ocr/ nemotron_parse_pipeline.py

# Auto-fix formatting
ruff format src/ scripts/ unlimited_ocr/ nemotron_parse_pipeline.py

# Tests
pytest
```

---

## NIM Models Used

| Role | Model |
|---|---|
| PDF parsing | `nvidia/nemotron-parse` |
| Vision captioning | `meta/llama-3.2-90b-vision-instruct` |
| Embeddings | `nvidia/nv-embedqa-e5-v5` (1024-dim) |
| Answer generation | `meta/llama-3.1-70b-instruct` |
| Mistral OCR | `mistral-ocr-latest` |
| Unlimited-OCR | `baidu/Unlimited-OCR` (MIT, self-hosted vLLM — not an NVIDIA NIM) |

---

## Important API Constraints

- **nemotron-parse image size**: must be 1024×1280 – 1648×2048 px. `compute_zoom()` auto-clamps.
- **Payload limit**: 4 MB per request. JPEG quality steps down 92→60 automatically to fit.
- **Retries**: 5xx errors retry 3× with exponential backoff. 400/401/403/404/422 fail immediately.
- **Qdrant client ≥ 1.16**: use `query_points()` (not `search()`), `upsert()` (not `upload_records()`).
- **`<tbc>` stitching**: nemotron-parse appends `<tbc>` when token limit hit mid-element. `stitch_continuations()` merges cross-page splits before chunking.
- **Vision caption cache**: re-runs skip already-captioned images (`results/image_captions/`).

---

## Project Structure

```
nemotron-parse-mistral-ocr/
├── nemotron_parse_pipeline.py     # standalone PDF → JSON/MD CLI
├── pyproject.toml
├── scripts/
│   ├── ingest.py                  # phases 1–5 orchestrator
│   ├── query_rag.py               # RAG query CLI
│   ├── visualize_parse.py         # Streamlit: Nemotron inspector
│   └── visualize_mistral_ocr.py   # Streamlit: Mistral OCR inspector
├── unlimited_ocr/
│   ├── app.py                     # Streamlit: Unlimited-OCR inspector
│   └── README.md
└── src/nemo_multimodal_rag/
    ├── config.py                  # pydantic-settings (all env vars)
    ├── ingestion/
    │   ├── parser.py              # Phase 1: JSON → ParsedElement + <tbc> stitch
    │   ├── chunker.py             # Phase 2: ParsedElement → Chunk
    │   ├── image_captioner.py     # Phase 3: bbox crop → vision caption
    │   └── embedder.py            # Phase 4: text → 1024-dim vectors
    ├── retrieval/
    │   └── vector_store.py        # Phase 5: Qdrant upsert + query_points
    ├── generation/
    │   └── generator.py           # RAG answer generation
    └── reporting/
        └── reports.py             # Markdown reports + image crops
```
