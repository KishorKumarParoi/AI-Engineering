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

load_dotenv()
importlib.reload(utils)

from utils import format_ai_message, parse_function_definition, get_type_from_annotation, parse_docstring_params, get_tool_descriptions

from intent_router_single_agent_retrieval_generation import State, AgentResponse, RAGUsedContext, ToolCall, QueryExpandResponse, AggregatorResponse, IntentRouterResponse

from api.utils.prompt_managements import prompt_template_config, prompt_template_registry

@traceable(
    name="agent_node",
    run_type="llm",
    tags=["agent", "openai"],
    metadata={"model": "gpt-4.1-mini", "ls-provider": "openai"}
)
def agent_node(state: State) -> dict:
    prompt = prompt_template_config("qa_agent.yaml", "qna_agent_prompt").render(
        available_tools=json.dumps(state.available_tools, ensure_ascii=True, indent=2)
    )
    messages = state.messages

    conversation = []

    for message in messages:
        conversation.append(convert_to_openai_messages(message))
    
    client = instructor.from_openai(OpenAI())

    response = client.chat.completions.create_with_completion(
        model="gpt-4.1-mini",
        response_model=AgentResponse,
        messages=[{"role": "system", "content": prompt}, *conversation] ,
        temperature=0.5,
        timeout=20,
    )

    if isinstance(response, (tuple, list)):
        response = response[0]

    normalized_tool_calls = []
    for tool_call in response.tool_calls:
        if isinstance(tool_call, dict):
            tool_name = tool_call.get("tool_name") or tool_call.get("name")
            arguments = dict(tool_call.get("arguments") or tool_call.get("args") or {})
        elif hasattr(tool_call, "model_dump"):
            tool_call_data = tool_call.model_dump()
            tool_name = tool_call_data.get("tool_name") or tool_call_data.get("name")
            arguments = dict(tool_call_data.get("arguments") or tool_call_data.get("args") or {})
        else:
            tool_name = getattr(tool_call, "tool_name", getattr(tool_call, "name", None))
            arguments = dict(getattr(tool_call, "arguments", getattr(tool_call, "args", {})) or {})

        normalized_tool_calls.append({
            "tool_name": tool_name,
            "arguments": arguments,
        })

    ai_message = format_ai_message(response)

    def _tool_messages(messages: list) -> list[dict]:
        items = []
        for message in messages:
            if getattr(message, "type", None) != "tool":
                continue
            items.append({
                "tool_name": getattr(message, "name", None) or getattr(message, "tool_name", None) or "tool",
                "tool_call_id": getattr(message, "tool_call_id", None),
                "content": getattr(message, "content", "") or "",
                "status": getattr(message, "status", None),
            })
        return items

    def _normalize_references(context_items: list[dict]) -> list[dict]:
        refs = []
        for item in context_items:
            content = str(item.get("content", "")).strip()
            if not content:
                continue
            refs.append({
                "id": item.get("tool_call_id") or item.get("tool_name") or "retrieved_context",
                "review": content,
                "description": content[:300],
            })
        seen = set()
        deduped = []
        for ref in refs:
            ref_id = ref.get("id")
            if ref_id in seen:
                continue
            seen.add(ref_id)
            deduped.append(ref)
        return deduped

    def _normalize_items(items: list[Any]) -> list[dict]:
        normalized = []
        for item in items or []:
            if hasattr(item, "model_dump"):
                normalized.append(item.model_dump())
            elif isinstance(item, dict):
                normalized.append(dict(item))
            else:
                normalized.append({"value": item})
        return normalized

    retrieved_context_field = getattr(state, "retrieved_context", None) or _tool_messages(list(getattr(state, "messages", None) or []))
    if not retrieved_context_field:
        retrieved_context_field = [{
            "tool_name": "get_formatted_context",
            "tool_call_id": None,
            "content": "No retrieved context available yet.",
            "status": "fallback",
        }]

    references_field = (
        getattr(response, "references", None)
        or getattr(response, "used_context", None)
        or getattr(response, "rag_used_context", None)
        or getattr(state, "references", None)
        or _normalize_references(retrieved_context_field)
    )
    if not references_field:
        references_field = [{"id": "retrieved_context", "review": "Retrieved context is available in the state.", "description": "Retrieved context is available in the state."}]
    references_field = _normalize_items(list(references_field))

    tool_calls_field = normalized_tool_calls or getattr(state, "tool_calls", None) or []
    if not tool_calls_field:
        query_seed = getattr(state, "expanded_query", []) or [getattr(state, "initial_query", "") or ""]
        query_seed = [item for item in query_seed if item]
        tool_calls_field = [
            {
                "tool_name": "get_formatted_context",
                "arguments": {"query": query_item, "top_k": 5},
            }
            for query_item in query_seed
        ] or [{"tool_name": "get_formatted_context", "arguments": {"query": getattr(state, "initial_query", "") or "", "top_k": 5}}]
    tool_calls_field = _normalize_items(list(tool_calls_field))

    available_tools_field = getattr(state, "available_tools", None) or []
    if not available_tools_field:
        available_tools_field = [{
            "name": "get_formatted_context",
            "description": "Retrieve and format top-k context chunks for a query",
            "arguments": {"query": "str", "top_k": "int"},
        }]
    available_tools_field = _normalize_items(list(available_tools_field))

    return {
        "messages": [ai_message],
        "tool_calls": tool_calls_field,
        "retrieved_context": retrieved_context_field,
        "expanded_query": getattr(state, "expanded_query", []) or [],
        "initial_query": getattr(state, "initial_query", "") or "",
        "answer": getattr(response, "answer", None) or getattr(state, "answer", "") or "",
        "question_relevant": bool(getattr(state, "question_relevant", False)),
        "available_tools": available_tools_field,
        "final_answer": len(tool_calls_field) == 0,
        "iteration": (getattr(state, "iteration", 0) or 0) + 1,
        "references": references_field,
    }



