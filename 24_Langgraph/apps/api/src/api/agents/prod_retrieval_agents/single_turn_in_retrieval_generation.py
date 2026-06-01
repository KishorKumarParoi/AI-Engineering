from modified_single_agent.graph import run_agent_graph
from langsmith import traceable

@traceable(
    name="execute_agent",
    run_type="llm",
    tags=["execution"]
)
def rag_pipeline_wrapper(query, qdrant_client, top_k=5):
    # This is a wrapper function to call the agent graph and extract the final answer
    return run_agent_graph(role="user", query=query)