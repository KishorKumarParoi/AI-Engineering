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
from api.utils.prompt_managements import prompt_template_config, prompt_template_registry

load_dotenv()
importlib.reload(utils)

from utils import format_ai_message, parse_function_definition, get_type_from_annotation, parse_docstring_params, get_tool_descriptions

class QueryExpandResponse(BaseModel):
    expanded_query: List[str] = Field(description="List of expanded search statements derived from the initial query")

class AggregatorResponse(BaseModel):
    answer: str = Field(description="Answer to the question based on the retrieved contexts")

class IntentRouterResponse(BaseModel):
    question_relevant: bool = Field(description="Whether the question is relevant to shopping search")
    answer: str = Field(description="Answer to the question if it is relevant, otherwise can be empty or a polite decline")

# class RagGenerationResponse(BaseModel):
#     answer: str = Field(description="The answer to the question")
#     reasoning: str = Field(description="The reasoning behind the answer")

class RAGUsedContext(BaseModel):
    id: str | int = Field(description="The ID of the retrieved review")
    review: str = Field(description="The text of the retrieved review")
    title: str | None = Field(default=None, description="The product title")
    description: str | list[str] | None = Field(default=None, description="The product description")
    categories: list[str] = Field(default_factory=list, description="The product categories")
    images: list[dict] = Field(default_factory=list, description="The product image variants")
    videos: list[dict] = Field(default_factory=list, description="The product videos")
    features: list[str] = Field(default_factory=list, description="The product feature bullets")
    main_category: str | None = Field(default=None, description="The product main category")
    store: str | None = Field(default=None, description="The store or brand")
    price: float | None = Field(default=None, description="The product price")
    rating_number: int | None = Field(default=None, description="The product rating count")
    details: dict | None = Field(default=None, description="The product details map")

class RagGenerationResponseReference(BaseModel):
    answer: str = Field(description="The answer to the question")
    reasoning: str = Field(description="The reasoning behind the answer")
    used_context: list[RAGUsedContext] = Field(description="The list of retrieved reviews used to generate the answer")
    references: list[RAGUsedContext] = Field(description="The list of references used to generate the answer")
    
class ToolCall(BaseModel):
    tool_name: str = Field(description="The name of the tool to call")
    arguments: dict = Field(description="The arguments to pass to the tool")

class AgentResponse(BaseModel):
    answer: str
    tool_calls: List[ToolCall] = Field(default_factory=list)
    references: List[RAGUsedContext] = Field(default_factory=list)
    final_answer: bool = False

class State(BaseModel):
    expanded_query: List[str] = Field(default_factory=list)
    messages: Annotated[List[Any], add] = Field(default_factory=list)
    retrieved_context: Annotated[List[dict], add] = Field(default_factory=list)
    initial_query: str = ""
    answer: str = ""
    question_relevant: bool = False
    available_tools: Annotated[List[dict], add] = Field(default_factory=list)
    final_answer: bool = False
    iteration: int = 0
    tool_calls: List[ToolCall] = Field(default_factory=list)
    references: Annotated[List[RAGUsedContext], add] = Field(default_factory=list)
    
load_dotenv()

# Retrieve API keys from environment variables
openai_api_key = os.getenv('OPENAI_API_KEY')
google_api_key = os.getenv('GEMINI_API_KEY')
qdrant_url = os.getenv('QDRANT_URL')
qdrant_api_key = os.getenv('QDRANT_API_KEY')
langsmith_api_key = os.getenv('LANGSMITH_API_KEY')
if qdrant_url and "qdrant:6333" in qdrant_url:
    # Docker service host is not resolvable from a local notebook kernel
    qdrant_url = qdrant_url.replace("qdrant:6333", "localhost:6333")

# Verify keys are loaded
print(f"OpenAI API Key present: {bool(openai_api_key)}")
print(f"Google API Key present: {bool(google_api_key)}")
print(f"Qdrant URL present: {bool(qdrant_url)}")
print(f"Qdrant API Key present: {bool(qdrant_api_key)}")
print(f"Langsmith API Key present: {bool(langsmith_api_key)}")

qdrant_client = QdrantClient(
    url=qdrant_url,
    api_key=qdrant_api_key,
)

