from api.agents.modified_single_agent.graph import run_agent_graph
from langsmith import traceable

@traceable(
    name="rag_pipeline_wrapper",
    run_type="llm",
    tags=["execution"]
)
# Change your function definition to accept and forward the client footprint:
def rag_pipeline_wrapper(query: str, qdrant_client=None, top_k: int = 5):
    # Pass it along to your modified single agent runtime handler
    return run_agent_graph(role="user", query=query, qdrant_client=qdrant_client)