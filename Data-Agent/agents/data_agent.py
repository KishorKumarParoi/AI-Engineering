import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.etl_analyst import etl_analyst
from agents.sql_analyst import sql_analyst
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from models.schema import DataAgentSchema, RouterSchema
from utils.llm_pick import pick_llm

llm = pick_llm("low")
llm_router = llm.with_structured_output(RouterSchema)


def router_node(state: DataAgentSchema) -> dict:
    """Classifies user query and routes to the SQL Analyst or ETL Analyst."""
    last_message = state.messages[-1].content if state.messages else ""

    system_prompt = (
        "You are the Chief Data Routing Supervisor in an enterprise AI system.\n"
        "Carefully analyze the user's intent and route to the correct specialist:\n\n"
        "1. 'sql' (SQL Analyst):\n"
        "   - Business intelligence, KPI reporting, counts, summaries, or database queries.\n"
        "   - Inquiries about database tables (users, rides, payments, ratings, vehicles, departments, etc.).\n"
        "   - Example: 'What is the total revenue by payment method?' or 'Show me the top 5 drivers.'\n\n"
        "2. 'etl' (ETL Analyst):\n"
        "   - Requests to extract or fetch data from HTTP URLs, public APIs, or external endpoints.\n"
        "   - Ingesting raw files, format conversion (CSV, JSON, Parquet), or Pandas transformations.\n"
        "   - Example: 'Extract data from https://pokeapi... and save as CSV' or 'Filter dataset where name is weedle.'\n\n"
        "Respond with 'sql' or 'etl' and your brief reasoning."
    )

    route_response_dict = llm_router.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=last_message)
    ]).model_dump()
    route_response = route_response_dict["answer"]

    print(f"\n[Supervisor Router] Decision: -> {route_response.upper()} | Reason: {route_response_dict['comments']}")
    return {"route_response": route_response}


def etl_node(state: DataAgentSchema) -> dict:
    """Invokes the ETL Analyst subgraph."""
    message = state.messages[-1].content if state.messages else ""
    print(f"[Data Agent] Dispatching to ETL Analyst Subgraph...")

    response = etl_analyst.invoke({
        "messages": [HumanMessage(content=message)]
    })

    final_message = response["messages"][-1]
    content = final_message.content if hasattr(final_message, "content") else str(final_message)
    return {
        "final_response": content,
        "messages": [AIMessage(content=content)]
    }


def sql_node(state: DataAgentSchema) -> dict:
    """Invokes the SQL Analyst subgraph."""
    message = state.messages[-1].content if state.messages else ""
    print(f"[Data Agent] Dispatching to SQL Analyst Subgraph...")

    input_schema = {
        "user_question": message,
        "messages": []
    }

    response = sql_analyst.invoke(input_schema)
    final_answer = response.get("final_response") or ""
    if not final_answer and response.get("messages"):
        last_sub_msg = response["messages"][-1]
        final_answer = getattr(last_sub_msg, "content", str(last_sub_msg))

    return {
        "final_response": final_answer,
        "messages": [AIMessage(content=final_answer)]
    }


def route_decision(state: DataAgentSchema) -> str:
    """Returns the target node name based on router output."""
    if state.route_response == "sql":
        return "sql_node"
    return "etl_node"


# Construct the supervisor graph
data_agent_graph = StateGraph(DataAgentSchema)
data_agent_graph.add_node("router_node", router_node)
data_agent_graph.add_node("sql_node", sql_node)
data_agent_graph.add_node("etl_node", etl_node)

data_agent_graph.add_edge(START, "router_node")
data_agent_graph.add_conditional_edges(
    "router_node",
    route_decision,
    {
        "sql_node": "sql_node",
        "etl_node": "etl_node"
    }
)
data_agent_graph.add_edge("sql_node", END)
data_agent_graph.add_edge("etl_node", END)

data_agent = data_agent_graph.compile()


if __name__ == "__main__":
    from IPython.display import Image

    try:
        img = Image(data_agent.get_graph().draw_mermaid_png())
        with open("data_agent.png", "wb") as f:
            f.write(img.data)
        print("Graph visualization saved to data_agent.png")
    except Exception as e:
        print(f"Could not save graph image: {e}")

    test_input = "Show me the top 3 cities with the most users."
    response = data_agent.invoke({
        "messages": [HumanMessage(content=test_input)]
    })
    print("\nFinal Response:\n", response.get("final_response"))