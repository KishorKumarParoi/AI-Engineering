from pydantic import BaseModel, Field
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from langchain_core.runnables import RunnableConfig

from langsmith import traceable, get_current_run_tree, Client
from operator import add
import yaml
from jinja2 import Template
from typing import List, Dict, Any, Annotated
import os

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
from qdrant_client.http.exceptions import UnexpectedResponse

import instructor

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
from dotenv import load_dotenv

load_dotenv()

from api.agents.modified_single_agent.utils import format_ai_message, parse_function_definition, get_type_from_annotation, parse_docstring_params, get_tool_descriptions

ls_client = Client()
ls_prompt = ls_client.pull_prompt("retrieval_generation_prompt")
ls_template = ls_prompt.messages[0].prompt.template

preprocessed_context = "- a \n - b"
question = "What is a?"

@traceable(
    name="build_prompt_with_jinja",
    run_type="prompt",
    tags=["prompt", "jinja"],
    metadata={"ls_provider": "jinja2"}
)
def build_prompt_with_jinja(preprocessed_context, question):
    jinja_template = prompt_template_config("api/agents/modified_single_agent/prompts/build_prompt_with_jinja.yaml", "build_prompt_with_jinja").render()

    template = Template(jinja_template)
    rendered_template = template.render(preprocessed_context=preprocessed_context, question=question)
    return rendered_template

@traceable(
    name="prompt_template_config",
    run_type="prompt",
    tags=["prompt", "config"],
    metadata={"ls_provider": "yaml"}
)

@traceable(
    name="prompt_template_config",
    run_type="prompt",
    tags=["prompt", "config"],
    metadata={"ls_provider": "yaml"}
)
def prompt_template_config(yaml_file, prompt_key):
    # Resolve relative to this package location dynamically
    current_dir = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.basename(yaml_file)
    
    # Check directly inside the sibling 'prompts' folder
    abs_yaml_path = os.path.join(current_dir, "prompts", filename)
    
    # Fallback to search up towards the main api folder structure if prompts isn't inside current_dir
    if not os.path.exists(abs_yaml_path):
        fallback_base = os.path.abspath(os.path.join(current_dir, "../../.."))
        abs_yaml_path = os.path.join(fallback_base, "api", "agents", "modified_single_agent", "prompts", filename)

    print(f"--> [DEBUG] Opening prompt config at verified path: {abs_yaml_path}")

    with open(abs_yaml_path, 'r') as file:
        config = yaml.safe_load(file)

    prompt_entry = config['prompts'][prompt_key]
    template_content = prompt_entry['template'] if isinstance(prompt_entry, dict) else prompt_entry

    template = Template(template_content)
    return template

@traceable(
    name="prompt_template_registry",
    run_type="prompt",
    tags=["prompt", "registry"],
    metadata={"ls_provider": "langsmith"}
)
def prompt_template_registry(prompt_name):
    template_content = ls_client.pull_prompt(prompt_name).messages[0].prompt.template
    template = Template(template_content)
    return template


# print(prompt_template_registry("retrieval_generation_prompt").render(preprocessed_context=preprocessed_context, question=question))

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
    description: str | list[str] | None = Field(default=None, description="The product description")
    # review: str = Field(description="The text of the retrieved review")
    # title: str | None = Field(default=None, description="The product title")
    # categories: list[str] = Field(default_factory=list, description="The product categories")
    # images: list[dict] = Field(default_factory=list, description="The product image variants")
    # videos: list[dict] = Field(default_factory=list, description="The product videos")
    # features: list[str] = Field(default_factory=list, description="The product feature bullets")
    # main_category: str | None = Field(default=None, description="The product main category")
    # store: str | None = Field(default=None, description="The store or brand")
    # price: float | None = Field(default=None, description="The product price")
    # rating_number: int | None = Field(default=None, description="The product rating count")
    # details: dict | None = Field(default=None, description="The product details map")

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


@traceable(
    name="get_qdrant_client",
    run_type="retriever",
    tags=["qdrant", "client"]
)
def get_qdrant_client():
    """Forces the absolute container URL bypass to test the connection."""
    # Hardcode the internal compose service domain name directly
    qdrant_url = "http://qdrant:6333"
    
    print(f"--> [DEBUG] OVERRIDE: Connecting directly to: {qdrant_url}")
    return QdrantClient(url=qdrant_url, api_key=os.getenv('QDRANT_API_KEY'))

@traceable(
        name="query_expand_node",
        run_type="llm",
        metadata={"ls_provider": "openai", "ls_model_name": "gpt-4.1-mini"},
        tags=["query", "expand", "jinja", "openai", "expand_tags"]
)
def query_expand_node(state: State) -> dict:
    import re

    state_data = state.model_dump() if hasattr(state, "model_dump") else state
    query_text = state_data.get("initial_query", "") if isinstance(state_data, dict) else getattr(state, "initial_query", "")
    if not query_text:
        return {"expanded_query": []}

    prompt_template = prompt_template_config("api/agents/modified_single_agent/prompts/query_expand_node.yaml", "query_expand_node_prompt").render()

    def _extract_products(text: str) -> list[str]:
        text = re.sub(
            r"(?i)^\s*(?:expand this query:\s*)?(?:can i get|can i buy|i need|i want|find me|looking for|need|want(?: to get)?|i'd like to get)\s+",
            "",
            text.strip(),
        )

        quoted = re.findall(r'"([^"]+)"', text)
        phrase_matches = re.findall(
            r"\b(?:a|an)\s+([A-Za-z][A-Za-z0-9\- ]{1,40}?)(?=\s+(?:for|,|and|$))",
            text,
            flags=re.IGNORECASE,
        )

        clause = re.split(r"\bfor\b", text, maxsplit=1, flags=re.IGNORECASE)[0]
        bare_candidates = [
            item.strip(" .?!,")
            for item in re.split(r"\s*(?:,|\band\b)\s*", clause, flags=re.IGNORECASE)
        ]

        candidates = quoted + phrase_matches + bare_candidates

        cleaned = []
        for item in candidates:
            value = re.sub(r"\s+", " ", item).strip(" .,")
            value = re.sub(r"(?i)^\s*(?:a|an|the)\s+", "", value).strip(" .,")
            if value and len(value) > 1 and not re.fullmatch(
                r"(?i)(?:can|i|get|buy|need|want|find|looking|for|me|my|family|kid|wife|and)",
                value,
            ):
                cleaned.append(value)

        seen = set()
        ordered = []
        for item in cleaned:
            key = item.lower()
            if key not in seen:
                seen.add(key)
                ordered.append(item)
        return ordered

    template = Template(prompt_template)
    explicit_products = _extract_products(query_text)
    prompt = template.render(
        query=query_text,
        explicit_products=", ".join(explicit_products) if explicit_products else "None",
    )

    client = instructor.from_openai(OpenAI())

    response = client.chat.completions.create_with_completion(
        model="gpt-4.1-mini",
        response_model=QueryExpandResponse,
        messages=[{"role": "system", "content": prompt}],
        temperature=0.1,
    )

    if isinstance(response, (tuple, list)):
        response = response[0]

    if hasattr(response, "model_dump"):
        response_data = response.model_dump()
    elif hasattr(response, "dict"):
        response_data = response.dict()
    else:
        response_data = dict(response)

    statements = response_data.get("statements") or response_data.get("queries") or response_data.get("expanded_query") or []

    if explicit_products:
        filtered_statements = [
            statement for statement in statements
            if any(product.lower() in statement.lower() for product in explicit_products)
        ]
        if filtered_statements:
            return {"expanded_query": filtered_statements}

        return {
            "expanded_query": [
                f"Search for {product} options for the specified user or family member"
                for product in explicit_products
            ]
        }

    return {"expanded_query": statements}


@traceable(
    name="query_expand_conditional_edges",
    run_type="llm",
    tags=["query", "expand", "conditional_edges"],
)
def query_expand_conditional_edges(state):
    import re

    def _extract_focus_product(query_text: str) -> str:
        text = re.sub(r"(?i)^\s*search for\s+", "", query_text).strip()
        text = re.sub(r"(?i)\s+options?\s+for\s+the\s+specified\s+user\s+or\s+family\s+member\s*$", "", text).strip()
        text = re.sub(r"(?i)\s+options?\s*$", "", text).strip()
        text = re.sub(r"(?i)^\s*(?:a|an|the)\s+", "", text).strip()
        return text if text else query_text

    state_data = state.model_dump() if hasattr(state, "model_dump") else state
    expanded_query = state_data.get("expanded_query", []) if isinstance(state_data, dict) else []

    send_messages = []
    for query_text in expanded_query:
        send_messages.append(
            Send(
                "retriever_node_parallel",
                {
                    "k": 10,
                    "query_text": query_text,
                    "qdrant_client": state_data.get("qdrant_client", None) if isinstance(state_data, dict) else getattr(state, "qdrant_client", None),
                    "focus_product": _extract_focus_product(query_text),
                }
            )
        )

    return send_messages

@traceable(
        name="get_embedding",
        tags=["embedding", "openai"],
        run_type="embedding",
        metadata={"model": "text-embedding-3-small", "ls-provider": "openai"}
)
def get_embedding(text, model="text-embedding-3-small"):
    response = openai.embeddings.create(
        input=text,
        model=model
    )

    current_run = get_current_run_tree()
    # Safely extract usage metadata whether response is an object or dict
    usage_obj = getattr(response, "usage", None)
    if usage_obj is None and isinstance(response, dict):
        usage_obj = response.get("usage")

    if current_run and usage_obj:
        try:
            input_tokens = getattr(usage_obj, "prompt_tokens", None) if not isinstance(usage_obj, dict) else usage_obj.get("prompt_tokens")
            total_tokens = getattr(usage_obj, "total_tokens", None) if not isinstance(usage_obj, dict) else usage_obj.get("total_tokens")
            current_run.add_metadata({
                "usage_metadata": {
                    "input_tokens": input_tokens,
                    "total_tokens": total_tokens,
                    "embedding_model": model,
                }
            })
        except Exception:
            # Fallback: ignore metadata errors to avoid breaking embedding
            logger = __import__("logging").getLogger(__name__)
            logger.debug("Failed to add embedding usage metadata to run")
    return response.data[0].embedding

@traceable(
        name="get_embeddings_batch",
        tags=["embedding", "openai"],
        run_type="embedding",
        metadata={"model": "text-embedding-3-small", "ls-provider": "openai"}
)
def get_embeddings_batch(text_list, model= "text-embedding-3-small", batch_size=100):
    if(len(text_list) <= batch_size):
        response = openai.embeddings.create(input=text_list, model=model)
        return [embedding.embedding for embedding in response.data]
    all_embeddings = []
    counter = 1
    for i in range(0, len(text_list), batch_size):
        batch = text_list[i:i+batch_size]
        response = openai.embeddings.create(input=batch, model=model)
        all_embeddings.extend([embedding.embedding for embedding in response.data])
        print(f"Processed batch {counter} / {len(text_list) // batch_size + 1}")
        counter += 1
    return all_embeddings

@traceable(
        name="retrieve_data",
        tags=["retrieval", "qdrant"],
        run_type="retriever"
)
def retrieve_data(query, qdrant_client, top_k=5):
    client = qdrant_client or (globals().get("qdrant_client") or get_qdrant_client())
    query_embedding = get_embedding(query)
    try:
        search_result = client.query_points(
            collection_name=os.getenv("collection_name", "Amazon_Electronics_Products"),
            query=query_embedding,
            using="text-embedding-3-small",
            limit=top_k,
            with_payload=True,
        )
    except UnexpectedResponse as e:
        status_code = getattr(e, 'status_code', None)
        if status_code == 404:
            # Create collection with expected vector params to avoid future 404s
            collection_name = os.getenv("collection_name", "Amazon_Electronics_Products")
            try:
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config={
                        "text-embedding-3-small": VectorParams(size=1536, distance=Distance.COSINE)
                    },
                    sparse_vectors_config={
                        "bm25": SparseVectorParams(modifier=models.Modifier.IDF)
                    }
                )
            except Exception:
                # If create fails, re-raise original UnexpectedResponse
                raise

            # Return empty structured result so caller can continue gracefully
            return {
                "retrieved_context_ids": [],
                "retrieved_contexts": [],
                "similarity_scores": [],
                "retrieved_context_ratings": [],
                "retrieved_context_prices": [],
                "retrieved_context_images": [],
                "retrieved_context_rating_numbers": [],
            }
        else:
            raise

    retrieved_context_ids = []
    retrieved_contexts = []
    similarity_scores = []
    retrieved_context_ratings = []
    retrieved_context_prices = []
    retrieved_context_images = []
    retrieved_context_rating_numbers = []
    retrieved_context_titles = []
    retrieved_context_details = []
    retrieved_context_features = []
    retrieved_context_brands = []
    retrieved_context_sizes = []
    retrieved_context_colors = []
    retrieved_context_main_categories = []

    for result in search_result.points:
        payload = result.payload or {}
        retrieved_context_ids.append(payload.get('parent_asin') or payload.get('product_id') or result.id)
        retrieved_contexts.append(
            payload.get('processed_description')
            or payload.get('description')
            or payload.get('text')
            or payload.get('title')
            or ""
        )
        similarity_scores.append(result.score)
        retrieved_context_ratings.append(payload.get('average_rating'))
        retrieved_context_prices.append(payload.get('price'))
        retrieved_context_images.append(payload.get('image_url') or payload.get('images') or [])
        retrieved_context_rating_numbers.append(payload.get('rating_number'))
        retrieved_context_titles.append(payload.get('title') or payload.get('text') or "")
        retrieved_context_details.append(payload.get('details') or {})
        retrieved_context_features.append(payload.get('features') or [])
        retrieved_context_brands.append(payload.get('brand') or payload.get('store') or "")
        details = payload.get('details') or {}
        if isinstance(details, dict):
            retrieved_context_sizes.append(details.get('size') or "")
            retrieved_context_colors.append(details.get('color') or "")
            retrieved_context_main_categories.append(payload.get('main_category') or details.get('main_category') or "")
        else:
            retrieved_context_sizes.append("")
            retrieved_context_colors.append("")
            retrieved_context_main_categories.append(payload.get('main_category') or "")

    return {
        "retrieved_context_ids": retrieved_context_ids,
        "retrieved_contexts": retrieved_contexts,
        "similarity_scores": similarity_scores,
        "retrieved_context_ratings": retrieved_context_ratings,
        "retrieved_context_prices": retrieved_context_prices,
        "retrieved_context_images": retrieved_context_images,
        "retrieved_context_rating_numbers": retrieved_context_rating_numbers
        ,"retrieved_context_titles": retrieved_context_titles,
        "retrieved_context_details": retrieved_context_details,
        "retrieved_context_features": retrieved_context_features,
        "retrieved_context_brands": retrieved_context_brands,
        "retrieved_context_sizes": retrieved_context_sizes,
        "retrieved_context_colors": retrieved_context_colors,
        "retrieved_context_main_categories": retrieved_context_main_categories,
    }

@traceable(
    name="retrieve_node",
    run_type="retriever",
    tags=["retrieval", "qdrant"]
)
def retriever_node(state) -> dict:
    import re

    def _extract_focus_product(query_text: str) -> str:
        text = re.sub(r"(?i)^\s*search for\s+", "", query_text).strip()
        text = re.sub(r"(?i)\s+options?\s+for\s+the\s+specified\s+user\s+or\s+family\s+member\s*$", "", text).strip()
        text = re.sub(r"(?i)\s+options?\s*$", "", text).strip()
        text = re.sub(r"(?i)^\s*(?:a|an|the)\s+", "", text).strip()
        return text if text else query_text

    def _run_single_retrieval(query_text: str, top_k: int) -> dict:
        result = retrieve_data(query_text, qdrant_client=qdrant_client, top_k=top_k)
        result["focus_product"] = _extract_focus_product(query_text)
        result["query_used"] = query_text
        result["top_k"] = top_k
        return result

    state_data = state.model_dump() if hasattr(state, "model_dump") else state
    if not isinstance(state_data, dict):
        state_data = {}

    query_text = state_data.get("query_text")
    top_k = state_data.get("k", 5)

    def _normalize_queries(raw_queries):
        if isinstance(raw_queries, dict):
            raw_queries = raw_queries.get("expanded_query", [])
        if isinstance(raw_queries, str):
            raw_queries = [raw_queries]
        if not isinstance(raw_queries, list):
            return []
        return [item.strip() for item in raw_queries if isinstance(item, str) and item.strip()]

    if query_text:
        return {
            "retrieved_context": [_run_single_retrieval(query_text, top_k)]
        }

    queries = _normalize_queries(state_data.get("expanded_query", []))
    if not queries:
        fallback_query = state_data.get("initial_query", "")
        queries = [fallback_query] if fallback_query else []

    retrieved_context = [_run_single_retrieval(query_item, top_k) for query_item in queries]
    return {
        "retrieved_context": retrieved_context
    }


@traceable(
    name="retriever_node_parallel",
    run_type="retriever",
    tags=["retrieval", "qdrant"]
)
def retriever_node_parallel(state: State, k: int = 5, qdrant_client: QdrantClient = None, query_text: str = None) -> dict:
    import re

    def _extract_focus_product(query_text: str) -> str:
        text = re.sub(r"(?i)^\s*search for\s+", "", query_text).strip()
        text = re.sub(r"(?i)\s+options?\s+for\s+the\s+specified\s+user\s+or\s+family\s+member\s*$", "", text).strip()
        text = re.sub(r"(?i)\s+options?\s*$", "", text).strip()
        text = re.sub(r"(?i)^\s*(?:a|an|the)\s+", "", text).strip()
        return text if text else query_text

    state_data = state.model_dump() if hasattr(state, "model_dump") else state
    if not isinstance(state_data, dict):
        state_data = {}

    payload_query = state_data.get("query_text", "")
    fallback_query = state_data.get("initial_query", "")
    top_k = state_data.get("k", k)

    q = (query_text or payload_query or fallback_query).strip()
    if not q:
        return {"retrieved_context": []}

    result = retrieve_data(q, qdrant_client=qdrant_client, top_k=top_k)
    result["focus_product"] = _extract_focus_product(q)
    result["query_used"] = q
    result["top_k"] = top_k
    return {"retrieved_context": [result]}

@traceable(
    name="process_context_node",
    run_type="prompt",
    tags=["prompt", "context"]
)
def process_context(context):
    formatted_contexts = ""
    for id, chunk, rating in zip(context["retrieved_context_ids"], context["retrieved_contexts"], context["retrieved_context_ratings"]):
        formatted_contexts += f"Product ID: {id}\nDescription: {chunk}\nRating: {rating}\n\n"
    return formatted_contexts


@traceable(
    name="get_formatted_context",
    run_type="retriever",
    tags=["retrieval", "formatting", "qdrant"]
)
def get_formatted_context(query: str, top_k: int = 5, *, qdrant_client: QdrantClient = None, config: RunnableConfig = None) -> str:
    """
    Get the top k context, each representing an inventory item for a given query.
    """
    client = qdrant_client or globals().get("qdrant_client")
    
    # Extract the client out of LangGraph's background configuration layer
    if client is None and config is not None:
        client = config.get("configurable", {}).get("qdrant_client", None)
        
    # Final backup helper if it's missing everywhere
    if client is None:
        raise ValueError("qdrant_client is not available in the notebook scope")

    context = retrieve_data(query, qdrant_client=client, top_k=top_k)
    return process_context(context)

@traceable(
    name="aggregator_node",
    run_type="llm",
    tags=["aggregation", "openai"],
    metadata={"model": "gpt-4.1-mini", "ls-provider": "openai"}
)
def aggregator_node(state: State) -> dict:
    context_blocks = []
    for item in state.retrieved_context:
        if not isinstance(item, dict):
            continue

        snippets = item.get("retrieved_contexts", [])
        prices = item.get("retrieved_context_prices", [])
        ratings = item.get("retrieved_context_ratings", [])

        compact_items = []
        for idx, snippet in enumerate(snippets[:3]):
            compact_items.append({
                "snippet": str(snippet)[:450],
                "price": prices[idx] if idx < len(prices) else None,
                "rating": ratings[idx] if idx < len(ratings) else None,
            })

        context_blocks.append({
            "focus_product": item.get("focus_product"),
            "query_used": item.get("query_used"),
            "matches": compact_items,
        })

    preprocessed_context = json.dumps(context_blocks, ensure_ascii=True, indent=2)

    prompt_template = prompt_template_config("api/agents/modified_single_agent/prompts/aggregator_node.yaml", "aggregator_node_prompt").render()

    template = Template(prompt_template)
    prompt = template.render(
        expanded_query=json.dumps(state.expanded_query, ensure_ascii=True),
        preprocessed_context=preprocessed_context,
    )

    try:
        client = instructor.from_openai(OpenAI())
        response = client.chat.completions.create_with_completion(
            model="gpt-4.1-mini",
            response_model=AggregatorResponse,
            messages=[{"role": "system", "content": prompt}],
            temperature=0.5,
            timeout=20,
        )

        if isinstance(response, (tuple, list)):
            response = response[0]

        return {"answer": response.answer}
    except Exception:
        fallback_lines = []
        for block in context_blocks:
            query_label = block.get("query_used") or "query"
            first = block.get("matches", [])
            if first:
                top = first[0]
                fallback_lines.append(
                    f"- Query: {query_label}\n"
                    f"  - Best option: {top.get('snippet', 'N/A')[:100]}\n"
                    f"  - Why: Based on retrieved context.\n"
                    f"  - Price/Ratings: price={top.get('price')}, rating={top.get('rating')}"
                )
            else:
                fallback_lines.append(
                    f"- Query: {query_label}\n"
                    f"  - Best option: Insufficient evidence\n"
                    f"  - Why: No context returned.\n"
                    f"  - Price/Ratings: N/A"
                )

        return {"answer": "\n\n".join(fallback_lines)}