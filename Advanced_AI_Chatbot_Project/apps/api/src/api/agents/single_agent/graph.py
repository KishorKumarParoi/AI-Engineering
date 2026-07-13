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
import sys
from pathlib import Path
import utils
from dotenv import load_dotenv

SRC_ROOT = Path(__file__).resolve().parents[3]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

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
    prompt_template = prompt_template_config("intent_router_agent.yaml", "intent_router_agent_prompt")

    prompt = prompt_template.render()

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


def _normalize_used_context(retrieved_context: Any) -> list[dict]:
    used_context = []

    if isinstance(retrieved_context, dict):
        retrieved_context_ids = retrieved_context.get("retrieved_context_ids", []) or []
        retrieved_contexts = retrieved_context.get("retrieved_contexts", []) or []
        similarity_scores = retrieved_context.get("similarity_scores", []) or []
        retrieved_context_ratings = retrieved_context.get("retrieved_context_ratings", []) or []
        retrieved_context_prices = retrieved_context.get("retrieved_context_prices", []) or []
        retrieved_context_images = retrieved_context.get("retrieved_context_images", []) or []
        retrieved_context_rating_numbers = retrieved_context.get("retrieved_context_rating_numbers", []) or []

        for index, context_id in enumerate(retrieved_context_ids):
            review = retrieved_contexts[index] if index < len(retrieved_contexts) else ""
            images = retrieved_context_images[index] if index < len(retrieved_context_images) else []
            image_list = []
            if isinstance(images, list):
                for image in images:
                    if isinstance(image, dict):
                        image_list.append(image)
                    elif isinstance(image, str) and image:
                        image_list.append({"large": image, "thumb": image, "hi_res": image})
            elif isinstance(images, str) and images:
                image_list.append({"large": images, "thumb": images, "hi_res": images})

            used_context.append({
                "id": context_id,
                "review": review,
                "title": review[:80] if review else str(context_id),
                "description": review,
                "images": image_list,
                "videos": [],
                "features": [],
                "categories": [],
                "main_category": "",
                "store": "",
                "price": retrieved_context_prices[index] if index < len(retrieved_context_prices) else None,
                "rating_number": retrieved_context_rating_numbers[index] if index < len(retrieved_context_rating_numbers) else None,
                "score": similarity_scores[index] if index < len(similarity_scores) else None,
                "average_rating": retrieved_context_ratings[index] if index < len(retrieved_context_ratings) else None,
                "details": {},
            })

    elif isinstance(retrieved_context, list):
        for item in retrieved_context:
            if not isinstance(item, dict):
                continue
            snippets = item.get("retrieved_contexts", []) or []
            ids = item.get("retrieved_context_ids", []) or []
            ratings = item.get("retrieved_context_ratings", []) or []
            prices = item.get("retrieved_context_prices", []) or []
            images = item.get("retrieved_context_images", []) or []
            for index, context_id in enumerate(ids):
                snippet = snippets[index] if index < len(snippets) else ""
                image_source = images[index] if index < len(images) else []
                image_list = []
                if isinstance(image_source, list):
                    for image in image_source:
                        if isinstance(image, dict):
                            image_list.append(image)
                        elif isinstance(image, str) and image:
                            image_list.append({"large": image, "thumb": image, "hi_res": image})
                elif isinstance(image_source, str) and image_source:
                    image_list.append({"large": image_source, "thumb": image_source, "hi_res": image_source})

                used_context.append({
                    "id": context_id,
                    "review": snippet,
                    "title": snippet[:80] if snippet else str(context_id),
                    "description": snippet,
                    "images": image_list,
                    "videos": [],
                    "features": [],
                    "categories": [],
                    "main_category": "",
                    "store": "",
                    "price": prices[index] if index < len(prices) else None,
                    "rating_number": None,
                    "score": None,
                    "average_rating": ratings[index] if index < len(ratings) else None,
                    "details": {},
                })

    return used_context


def rag_pipeline_wrapper(question, qdrant_client=None, top_k=5):
    graph, tool_descriptions = compile_agent()

    if qdrant_client is not None:
        get_formatted_context.__globals__["qdrant_client"] = qdrant_client

    initial_state = {
        "initial_query": question,
        "messages": [{"role": "user", "content": question}],
        "available_tools": tool_descriptions,
    }

    result = graph.invoke(State(**initial_state))
    retrieved_context = result.get("retrieved_context", {})
    used_context = _normalize_used_context(retrieved_context)

    references = result.get("references", []) or []
    if isinstance(references, list):
        references = [ref.model_dump() if hasattr(ref, "model_dump") else ref for ref in references]

    return {
        "question": question,
        "answer": result.get("answer", ""),
        "used_context": used_context,
        "retrieved_context": retrieved_context,
        "retrieved_context_ids": result.get("retrieved_context_ids", []),
        "similarity_scores": result.get("similarity_scores", []),
        "references": references,
        "expanded_query": result.get("expanded_query", []),
        "messages": result.get("messages", []),
        "tool_calls": result.get("tool_calls", []),
        "final_answer": bool(result.get("final_answer", False)),
        "initial_query": result.get("initial_query", question),
    }


# display(Image(graph.get_graph().draw_mermaid_png()))

def run_agent(role, content: str):
    result = rag_pipeline_wrapper(content)
    print(result)
    return result


if __name__ == "__main__":
    run_agent("user",
    "Can you suggest a earpods?")