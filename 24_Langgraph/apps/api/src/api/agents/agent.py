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
    prompt_template = prompt_template_config("api/prompts/qa_agent.yaml", "qa_agent_prompt")

    template = Template(prompt_template)
    prompt = template.render(
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

    normalized_tool_calls = [
        {
            "tool_name": getattr(tool_call, "tool_name", getattr(tool_call, "name", None)),
            "arguments": getattr(tool_call, "arguments", getattr(tool_call, "args", {})),
        }
        for tool_call in response.tool_calls
    ]

    ai_message = format_ai_message(response)

    # Populate references: prefer explicit references from the model response,
    # fall back to any used/retrieved context on the response or state.
    references = (
        getattr(response, "references", None)
        or getattr(response, "used_context", None)
        or getattr(response, "rag_used_context", None)
        or getattr(state, "retrieved_context", None)
        or []
    )

    return {
        "messages": [ai_message],
        "tool_calls": normalized_tool_calls,
        "iteration": state.iteration + 1,
        "answer": response.answer,
        "final_answer": len(response.tool_calls) == 0,
        "references": references
    }



