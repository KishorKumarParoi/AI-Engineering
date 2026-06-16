import os
import requests
import json

# Configuration — set TAVILY_API_KEY as an environment variable
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
SEARCH_QUERY = "Claude Code latest news 2026"

TAVILY_API_URL = "https://api.tavily.com/search"


def search_tavily(query: str) -> dict:
    """
    Search using Tavily API.

    Args:
        query: The search query string

    Returns:
        Dictionary containing search results
    """
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return {"error": "TAVILY_API_KEY environment variable is not set"}

    payload = {
        "api_key": api_key,
        "query": query,
        "include_answer": True,
        "max_results": 5,
    }

    try:
        response = requests.post(TAVILY_API_URL, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        error_info = {"error": str(e)}
        if hasattr(e, "response") and e.response is not None:
            error_info["response_text"] = e.response.text
        return error_info


if __name__ == "__main__":
    results = search_tavily(SEARCH_QUERY)
    print(json.dumps(results, indent=2))
