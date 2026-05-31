from pydantic import BaseModel, Field
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

from operator import add
from typing import Any, Annotated, Dict, List

from langchain_core.messages import BaseMessage, AIMessage, ToolMessage, HumanMessage, SystemMessage
from langchain_core.tools import BaseTool
from langchain_core.prompts import BasePromptTemplate
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.prompts import StringPromptTemplate
from langchain_core.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import convert_to_openai_messages, convert_to_messages
from langchain_protocol import Literal

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PayloadSchemaType, PointStruct, SparseVectorParams, Document,Prefetch, FusionQuery
from qdrant_client import models

import instructor
from langsmith import traceable, get_current_run_tree

import pandas as pd
import openai
import fastembed

from jinja2 import Template
from typing import List, Dict, Any, Optional, Union
from IPython.display import Image, display
from operator import add
from openai import OpenAI

import random
import ast
import inspect
import instructor
import json
import os
import importlib
import utils
from dotenv import load_dotenv

from tools import get_formatted_context, tool_router
from agent import agent_node
from api.utils.prompt_managements import prompt_template_config, prompt_template_registry

load_dotenv()
importlib.reload(utils)

from utils import format_ai_message, parse_function_definition, get_type_from_annotation, parse_docstring_params, get_tool_descriptions

from intent_router_single_agent_retrieval_generation import State, QueryExpandResponse, AggregatorResponse, IntentRouterResponse, ToolCall

@traceable(
    name="intent_router_node",
    run_type="llm",
    tags=["routing", "openai"],
    metadata={"model": "gpt-4.1-mini", "ls-provider": "openai"}
)
def intent_router_node(state: State) -> dict:
    prompt_template = prompt_template_config("api/prompts/intent_router_agent.yaml", "intent_router_agent_prompt")

    template = Template(prompt_template)
    prompt = template.render()

    messages = state.messages
    conversation = []
    for message in messages:
        conversation.append(convert_to_openai_messages(message))

    client = instructor.from_openai(OpenAI())

    response = client.chat.completions.create_with_completion(
        model="gpt-4.1-mini",
        response_model=IntentRouterResponse,
        messages=[{"role": "system", "content": prompt}, *conversation],
        temperature=0.5,
    )

    if isinstance(response, (tuple, list)):
        response = response[0]

    return {
        "question_relevant": response.question_relevant,
        "answer": response.answer
    }

def intent_router_conditional_edges(state):
    if state.question_relevant:
        return "agent_node"
    else:
        return "end"
    
def compile_agent():
    workflow = StateGraph(State)

    tools = [get_formatted_context]
    tool_node = ToolNode(tools)
    tool_descriptions = get_tool_descriptions(tools)

    workflow.add_node("agent_node", agent_node)
    workflow.add_node("tool_node", tool_node)
    workflow.add_node("intent_router_node", intent_router_node)

    workflow.add_edge(START, "intent_router_node")

    workflow.add_conditional_edges(
        "intent_router_node",
        intent_router_conditional_edges,
        {
            "agent_node": "agent_node",
            "end": END,
        },
    )

    workflow.add_conditional_edges(
        "agent_node",
        tool_router,
        {
            "tools": "tool_node",
            "end": END,
        },
    )

    workflow.add_edge("tool_node", "agent_node")

    graph = workflow.compile()
    return graph, tool_descriptions


# display(Image(graph.get_graph().draw_mermaid_png()))

def run_agent(role, content: str):
    graph, tool_descriptions = compile_agent()
    initial_state = {
        "messages": [{
            "role": role,
            "content": content
            # "role": "user",
            # "content": "Can I get a Tablet for my kid, a watch for me, a laptop for my wife and a waterproof speaker for our party next week?"
        }],
        "available_tools": tool_descriptions
    }

    result = graph.invoke(initial_state)
    print(result)
    return result
