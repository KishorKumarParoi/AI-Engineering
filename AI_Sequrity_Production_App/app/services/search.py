import os
import logging
import httpx
from typing import Dict, Any, List, Optional
from app.config import settings

logger = logging.getLogger("SearchService")

class WebSearchService:
    """
    Enterprise-grade Web Intelligence Search Service.
    Integrates both Tavily (specialized for AI agent research)
    and Serper (Google Search API) with automatic fallback and result deduplication.
    """

    def __init__(self):
        self.tavily_key = os.getenv("TAVILY_API_KEY") or getattr(settings, "TAVILY_API_KEY", "")
        self.serper_key = os.getenv("SERPER_API_KEY") or getattr(settings, "SERPER_API_KEY", "")

    def tavily_search(self, query: str, max_results: int = 5, search_depth: str = "advanced") -> List[Dict[str, Any]]:
        """Executes deep research search via Tavily API."""
        if not self.tavily_key:
            logger.warning("TAVILY_API_KEY not configured. Skipping Tavily search.")
            return []

        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=self.tavily_key)
            response = client.search(
                query=query,
                search_depth=search_depth,
                max_results=max_results,
                include_answer=True,
            )
            results = []
            if "answer" in response and response["answer"]:
                results.append({
                    "title": "Tavily AI Direct Intelligence Summary",
                    "url": "tavily:direct_answer",
                    "snippet": response["answer"],
                    "source": "tavily_summary"
                })
            for item in response.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("content", ""),
                    "score": item.get("score", 0.0),
                    "source": "tavily"
                })
            logger.info(f"🔍 Tavily search returned {len(results)} results for '{query[:50]}'")
            return results
        except Exception as e:
            logger.error(f"Tavily search failed for query '{query[:50]}': {e}")
            return []

    def serper_search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Executes real-time Google search via Serper API."""
        if not self.serper_key:
            logger.warning("SERPER_API_KEY not configured. Skipping Serper search.")
            return []

        try:
            url = "https://google.serper.dev/search"
            payload = {"q": query, "num": max_results}
            headers = {
                "X-API-KEY": self.serper_key,
                "Content-Type": "application/json"
            }
            with httpx.Client(timeout=10.0) as client:
                res = client.post(url, json=payload, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    results = []
                    # Check knowledge graph or answer box
                    if "answerBox" in data:
                        results.append({
                            "title": data["answerBox"].get("title", "Google Answer Box"),
                            "url": "google:answer_box",
                            "snippet": data["answerBox"].get("snippet") or data["answerBox"].get("answer", ""),
                            "source": "serper_answerbox"
                        })
                    for item in data.get("organic", [])[:max_results]:
                        results.append({
                            "title": item.get("title", ""),
                            "url": item.get("link", ""),
                            "snippet": item.get("snippet", ""),
                            "source": "serper_google"
                        })
                    logger.info(f"🔍 Serper search returned {len(results)} results for '{query[:50]}'")
                    return results
                else:
                    logger.error(f"Serper API returned HTTP {res.status_code}: {res.text}")
                    return []
        except Exception as e:
            logger.error(f"Serper search failed for query '{query[:50]}': {e}")
            return []

    def hybrid_search(self, query: str, max_results: int = 6) -> List[Dict[str, Any]]:
        """
        Executes dual-engine search:
        Prefers Tavily for deep technical synthesis; cascades to Serper for real-time Google index;
        deduplicates URLs across both engines.
        """
        tavily_results = self.tavily_search(query, max_results=max_results)
        if len(tavily_results) >= max_results:
            return tavily_results[:max_results]

        serper_results = self.serper_search(query, max_results=max_results)
        
        seen_urls = set()
        merged = []
        for item in (tavily_results + serper_results):
            url = item.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                merged.append(item)
            elif not url:
                merged.append(item)

        if not merged:
            logger.info("Search engines yielded 0 results or keys not active. Returning empty candidate set.")
        return merged[:max_results]


search_service = WebSearchService()
