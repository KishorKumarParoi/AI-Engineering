import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langchain_core.messages import HumanMessage, AIMessage
from models.schema import RouterSchema, DataAgentSchema
from utils.llm_pick import pick_llm
from agents.etl_analyst import etl_analyst
from agents.sql_analyst import sql_analyst
from langgraph.graph import StateGraph, START, END

llm = pick_llm("medium")

llm_router = llm.with_structured_output(RouterSchema)


def router_node(state: DataAgentSchema):
    message = state.messages[-1].content

    route_response_dict = llm_router.invoke(message).model_dump()
    route_response = route_response_dict['answer']

    return {"route_response": route_response}


def etl_node(state: DataAgentSchema):
    message = state.messages[-1].content
    response = etl_analyst.invoke({
        "messages": [HumanMessage(content=message)]
    })
    # response is a dict whose 'messages' key holds the conversation; get the final AI message
    final_message = response["messages"][-1]
    content = final_message.content if hasattr(final_message, "content") else str(final_message)
    return {"messages": [AIMessage(content=content)]}


def sql_node(state: DataAgentSchema):
    message = state.messages[-1].content

    input_schema = {
        "user_question": message,
        "messages": []
    }

    response = sql_analyst.invoke(input_schema)
    # response is a dict with 'final_response' key from AgentSchema
    final_answer = response.get("final_response") or (response["messages"][-1].content if response.get("messages") else "")
    return {"messages": [AIMessage(content=final_answer)]}


def route_decision(state: DataAgentSchema):
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

    response = data_agent.invoke(
        {
            "messages": [HumanMessage(content="I want to extract the data from the API Endpoint: https://pokeapi.co/api/v2/pokemon/132 at data/extract/final_data.csv")],
            "route_response": "sql"
        }
    )
    print("Final Response:", response["messages"][-1].content)
    