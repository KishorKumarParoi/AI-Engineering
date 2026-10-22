import time
import requests
import logfire
from app.config import settings

BATCH_SIZE = 16
_JINA_DIM = 1024
_GEMINI_DIM = 3072
_FALLBACK_DIM = 768  # all-mpnet-base-v2

_active_model = None
_model_type: str | None = None  # "jina", "gemini", or "fallback"
_JINA_API_URL = "https://api.jina.ai/v1/embeddings"


# ── Model initialisation ───────────────────────────────────────────────────────

def _probe_jina() -> bool:
    """Probe Jina AI API to verify connectivity and API key validity."""
    if not settings.JINA_API_KEY:
        logfire.warning("No JINA_API_KEY found. Skipping Jina embedding probe.")
        return False
    try:
        headers = {
            "Authorization": f"Bearer {settings.JINA_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "jina-embeddings-v3",
            "task": "retrieval.query",
            "dimensions": _JINA_DIM,
            "input": ["probe"]
        }
        res = requests.post(_JINA_API_URL, headers=headers, json=payload, timeout=8)
        if res.status_code == 200:
            data = res.json()
            if data.get("data") and len(data["data"][0]["embedding"]) == _JINA_DIM:
                logfire.info("✅ Jina AI embeddings ready (jina-embeddings-v3, 1024-dim, Industry Standard).")
                return True
        logfire.warning(f"Jina probe returned HTTP {res.status_code}: {res.text}. Will try Gemini.")
        return False
    except Exception as e:
        logfire.warning(f"Jina probe failed: {e}. Will try Gemini.")
        return False


def _probe_gemini():
    """Try one embed call to verify Gemini is reachable. Returns model or None."""
    if not settings.GEMINI_API_KEY:
        return None
    try:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        model = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-2-preview",
            google_api_key=settings.GEMINI_API_KEY,
        )
        model.embed_query("probe")
        logfire.info("Gemini embeddings ready (gemini-embedding-2-preview, 3072-dim).")
        return model
    except Exception as e:
        logfire.warning(f"Gemini probe failed: {e}. Will use sentence-transformers fallback.")
        return None


def _load_fallback():
    from sentence_transformers import SentenceTransformer
    logfire.info("Loading sentence-transformers fallback (all-mpnet-base-v2, 768-dim).")
    return SentenceTransformer("all-mpnet-base-v2")


def _init():
    """Initialise embedding model once per process (Jina -> Gemini -> SentenceTransformer)."""
    global _active_model, _model_type
    if _model_type is not None:
        return

    # 1. Primary: Jina AI (Industry standard)
    if _probe_jina():
        _model_type = "jina"
        _active_model = "jina"
        return

    # 2. Secondary: Gemini
    gemini = _probe_gemini()
    if gemini:
        _active_model = gemini
        _model_type = "gemini"
        return

    # 3. Tertiary: Local sentence-transformers
    _active_model = _load_fallback()
    _model_type = "fallback"


# ── Public helpers ─────────────────────────────────────────────────────────────

def get_embedding_dim() -> int:
    """Return the vector dimension for the active model. Call after _init()."""
    _init()
    if _model_type == "jina":
        return _JINA_DIM
    elif _model_type == "gemini":
        return _GEMINI_DIM
    else:
        return _FALLBACK_DIM


# ── Jina Embedding API Caller with Retry ───────────────────────────────────────

def _embed_jina(texts: list[str], task: str = "retrieval.passage") -> list[list[float]]:
    headers = {
        "Authorization": f"Bearer {settings.JINA_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "jina-embeddings-v3",
        "task": task,
        "dimensions": _JINA_DIM,
        "input": texts
    }

    for attempt in range(4):
        try:
            res = requests.post(_JINA_API_URL, headers=headers, json=payload, timeout=20)
            if res.status_code == 200:
                body = res.json()
                return [item["embedding"] for item in body["data"]]
            elif res.status_code in (429, 500, 502, 503, 504) and attempt < 3:
                wait = 2 ** attempt
                logfire.warning(f"Jina API HTTP {res.status_code} — retrying in {wait}s (attempt {attempt+1}/4)")
                time.sleep(wait)
            else:
                res.raise_for_status()
        except Exception as e:
            if attempt < 3:
                wait = 2 ** attempt
                logfire.warning(f"Jina API error ({e}) — retrying in {wait}s (attempt {attempt+1}/4)")
                time.sleep(wait)
            else:
                logfire.error(f"Jina embedding failed after 4 attempts: {e}")
                raise
    raise RuntimeError("Jina embedding failed after max retries.")


# ── Batch embedding with retry ─────────────────────────────────────────────────

def _embed_batch(batch: list[str]) -> list[list[float]]:
    if _model_type == "jina":
        return _embed_jina(batch, task="retrieval.passage")
    elif _model_type == "gemini":
        for attempt in range(4):
            try:
                return _active_model.embed_documents(batch)
            except Exception as e:
                err_msg = str(e)
                err = err_msg.lower()
                should_retry = any(x in err for x in (
                    "429", "rate", "quota", "resource_exhausted",
                    "timeout", "timed out", "time out", "connection",
                    "socket", "temp", "transient"
                ))
                if should_retry and attempt < 3:
                    wait = 2 ** attempt
                    logfire.warning(
                        f"Gemini embedding error/timeout hit — retrying in {wait}s "
                        f"(attempt {attempt + 1}/4): {err_msg}"
                    )
                    time.sleep(wait)
                else:
                    logfire.error(f"Gemini embedding failed: {err_msg}")
                    raise
        raise RuntimeError("Gemini embedding error persisted after 4 attempts.")
    else:
        return _active_model.encode(batch, show_progress_bar=False).tolist()


# ── Public API ────────────────────────────────────────────────────────────────

def embed_query(query: str) -> list[float]:
    _init()
    if _model_type == "jina":
        return _embed_jina([query], task="retrieval.query")[0]
    elif _model_type == "gemini":
        return _active_model.embed_query(query)
    return _active_model.encode([query])[0].tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    _init()
    all_embeddings: list[list[float]] = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        with logfire.span("Embed batch", model=_model_type, start=i, size=len(batch)):
            all_embeddings.extend(_embed_batch(batch))
    return all_embeddings
