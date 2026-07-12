import os
import sys

# Bootstrap python search path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, "src"))
sys.path.insert(0, os.path.abspath(os.path.join(current_dir, "../api/src")))

from fastmcp import FastMCP
from typing import List
from mcp_server_reviews.utils import retrieve_data, process_context
from qdrant_client import QdrantClient
from langchain_core.runnables import RunnableConfig

mcp = FastMCP("mcp_server")

@mcp.tool()
def get_formatted_context(query: str, top_k: int = 5, *, qdrant_client: QdrantClient | None = None, config: RunnableConfig | None = None) -> str:
    """
    Get the top k context, each representing an inventory item for a given query.
    """
    client = qdrant_client or globals().get("qdrant_client")
    
    # Extract the client out of LangGraph's background configuration layer
    if client is None and config is not None:
        client = config.get("configurable", {}).get("qdrant_client", None)
        
    # Final backup helper if it's missing everywhere
    if client is None:
        raise ValueError("qdrant_client is not available in the notebook scope")

    context = retrieve_data(query, qdrant_client=client, top_k=top_k)
    return process_context(context)


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0",port=8000)   