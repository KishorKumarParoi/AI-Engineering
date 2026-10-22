import time
import requests
import logfire
from flashrank import Ranker, RerankRequest
from app.config import settings

# Lazy initialization - FlashRank Ranker is loaded only if Jina fails or is unavailable
_flashrank = None
_JINA_RERANK_URL = "https://api.jina.ai/v1/rerank"


def _get_flashrank() -> Ranker:
    """
    Initializes the FlashRank engine lazily as a fallback.
    FlashRank uses a local ONNX model for fast, offline reranking.
    """
    global _flashrank
    if _flashrank is None:
        logfire.info("🧠 Initializing FlashRank Model (TinyBERT) locally as fallback...")
        try:
            _flashrank = Ranker(cache_dir="/tmp/flashrank")
        except Exception:
            _flashrank = Ranker()
    return _flashrank


def _rerank_with_jina(query: str, documents: list[str], top_n: int = 5) -> list[str] | None:
    """Call Jina AI Reranker API (jina-reranker-v2-base-multilingual)."""
    if not settings.JINA_API_KEY:
        return None

    headers = {
        "Authorization": f"Bearer {settings.JINA_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "jina-reranker-v2-base-multilingual",
        "query": query,
        "documents": documents,
        "top_n": top_n
    }

    try:
        res = requests.post(_JINA_RERANK_URL, headers=headers, json=payload, timeout=10)
        if res.status_code == 200:
            data = res.json()
            results = data.get("results", [])
            reranked_docs = []
            for item in results:
                doc = item.get("document")
                if isinstance(doc, dict):
                    reranked_docs.append(doc.get("text", ""))
                elif isinstance(doc, str):
                    reranked_docs.append(doc)
                else:
                    idx = item.get("index")
                    if idx is not None and idx < len(documents):
                        reranked_docs.append(documents[idx])
            top_score = results[0]["relevance_score"] if results else "N/A"
            logfire.info(f"✅ [Jina Reranker] Succeeded. Kept top {len(reranked_docs)}. Top score: {top_score}")
            return reranked_docs
        else:
            logfire.warning(f"Jina Reranker returned HTTP {res.status_code}: {res.text}. Falling back to FlashRank.")
            return None
    except Exception as e:
        logfire.warning(f"Jina Reranker call failed ({e}). Falling back to FlashRank.")
        return None


def _rerank_with_flashrank(query: str, documents: list[str], top_n: int = 5) -> list[str]:
    """Fallback reranker using local FlashRank ONNX cross-encoder."""
    ranker = _get_flashrank()
    passages = [{"id": i, "text": doc} for i, doc in enumerate(documents)]
    request = RerankRequest(query=query, passages=passages)
    results = ranker.rerank(request)
    reranked = [res["text"] for res in results[:top_n]]
    top_score = results[0]["score"] if results else "N/A"
    logfire.info(f"✅ [FlashRank Fallback] Succeeded. Top score: {top_score}")
    return reranked


def rerank_documents(query: str, documents: list[str], top_n: int = 5) -> list[str]:
    """
    Industry-standard two-tier semantic reranking:
    1. Primary: Jina AI Reranker (jina-reranker-v2-base-multilingual)
    2. Fallback: Local FlashRank ONNX TinyBERT
    3. Last resort: Original vector order documents[:top_n]
    """
    if not documents:
        return []

    start_time = time.time()
    logfire.info(f"📡 [Reranker] Reranking {len(documents)} documents for query: '{query[:40]}...'")

    # 1. Try Jina AI Reranker first (Industry Standard)
    jina_results = _rerank_with_jina(query, documents, top_n)
    if jina_results is not None:
        duration = time.time() - start_time
        logfire.info(f"⚡ [Reranker] Jina rerank completed in {duration:.2f}s")
        return jina_results

    # 2. Try FlashRank fallback
    try:
        flash_results = _rerank_with_flashrank(query, documents, top_n)
        duration = time.time() - start_time
        logfire.info(f"⚡ [Reranker] FlashRank completed in {duration:.2f}s")
        return flash_results
    except Exception as e:
        logfire.error(f"❌ [Reranker] FlashRank failed: {e}. Returning original vector order.")
        return documents[:top_n]
