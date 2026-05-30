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


class QueryExpandResponse(BaseModel):
    expanded_query: List[str] = Field(description="List of expanded search statements derived from the initial query")

class AggregatorResponse(BaseModel):
    answer: str = Field(description="Answer to the question based on the retrieved contexts")

class IntentRouterResponse(BaseModel):
    question_relevant: bool = Field(description="Whether the question is relevant to shopping search")
    answer: str = Field(description="Answer to the question if it is relevant, otherwise can be empty or a polite decline")

class RagGenerationResponse(BaseModel):
    answer: str = Field(description="The answer to the question")
    reasoning: str = Field(description="The reasoning behind the answer")

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

@traceable(
    name="agent_node",
    run_type="llm",
    tags=["agent", "openai"],
    metadata={"model": "gpt-4.1-mini", "ls-provider": "openai"}
)
def agent_node(state: State) -> dict:
    prompt_template = """You are an expert shopping assistant. Your task is to answer the user's question
      by reasoning step-by-step and using the available tools to retrieve necessary information.
      You will be given a conversation history, the user's initial query, and a list of tools you can use
      to answer the question.

      <Available Tools>
      {{available_tools}}
      </Available Tools>

      When making the tool calls, use this exact format:
      {
         "name" : "tool_name",
         "arguments" : {
             "arg1": "value1",
             "arg2": "value2"
             }
      }

      CRITICAL: All parameters must go inside the "arguments" object, not at the top level of the tool call.

      Examples:
      - Get formatted context for a query:
      {
         "name": "get_formatted_context",
         "arguments": {
             "query": "what is the capital of France?"
             "top_k": 5
         }
      }

      CRITICAL Rules:
      - If tool_calls has values, final answer MUST be false.
      (You can't call tools and exit the graph in the same response)
      - If final_answer is true, tool_calls MUST be empty.
      (You must wait for the tool results in the state before giving the final answer and exiting the graph)
      - If you need tool results, you can then set:
      tool_calls = [], final_answer = true
      - Use names specifically provided in the available tols, Don't add any additional text to the names.

      Instructions:
      - You need to answer the question based on the outputs from the tools using the available tools only.
      - Do not suggest the same tool call more tha once.
      - If the question can be decomposed into multiple sub-questions, suggest all of them.
      - If multiple tool calls can be used at once to answer the question, suggest all of them.
      - Do not explain your next steps in the answer, instead use tools to answer the question.
      - Nevder use word context and refer to it as the available products.
      - you should only answer question about the products in stock. If the question is not about the products in stock,
      you should ask for clarification.
      - As an output you need to return the following:
      * answer: The answer to the question based on your current knowledge and tool results.
      * references: The list of the indexes from the chunks returned from all tool calls used to generate the question.
      If more than one chunk was used to compile the answer from a single tool call, be sure to return all of them.
      * Each reference should have an id and a short description of the item based on the retrieved context
      * final_answer: True if you have all the information needed to provide a complete answer, False otherwise

      - The answer to the question should contain detailed information about the product and should be returned with detailed specification in
      bullet points.
      - The short description should have the name of the item.
      - If the user's request requires using a tool, set tool_calls with the appropriate function names and arguments.
      """ 
    
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
            "tool_name": getattr(tool_call, "tool_name", getattr(tool_call, "tool_name", None)),
            "arguments": getattr(tool_call, "arguments", {}),
        }
        for tool_call in response.tool_calls
    ]

    ai_message = format_ai_message(response)

    return {
        "messages": [ai_message],
        "tool_calls": normalized_tool_calls,
        "iteration": state.iteration + 1,
        "answer": response.answer,
        "final_answer": len(response.tool_calls) == 0,
        "references": []
    }



