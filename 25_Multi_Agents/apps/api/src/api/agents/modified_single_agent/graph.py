import json
import os
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from langgraph.checkpoint.postgres import PostgresSaver 
from pydantic import BaseModel, Field
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from langsmith import traceable, get_current_run_tree, Client
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from api.agents.modified_single_agent.tools import AgentResponse, IntentRouterResponse, RAGUsedContext, prompt_template_config, prompt_template_registry, QueryExpandResponse, AggregatorResponse, State, RagGenerationResponseReference, ToolCall, query_expand_conditional_edges, query_expand_node, retriever_node_parallel, aggregator_node, get_formatted_context, get_formatted_reviews_context, get_formatted_items_context
from api.agents.modified_single_agent.utils import format_ai_message, parse_function_definition, get_type_from_annotation, parse_docstring_params, get_tool_descriptions
from api.agents.modified_single_agent.agent import agent_node, intent_router_node, intent_router_conditional_edges, tool_router, intent_router_route

@traceable(
    name="old_compile_graph",
    run_type="llm",
    tags=["graph_compilation"],
)
def old_compile_graph():
    workflow = StateGraph(State)
    workflow.add_node("query_expand_node", query_expand_node)
    workflow.add_node("retriever_node_parallel", retriever_node_parallel)
    workflow.add_node("aggregator_node", aggregator_node)
    workflow.add_node("intent_router_node", intent_router_node)

    workflow.add_edge(START, "intent_router_node")
    workflow.add_conditional_edges(
        "intent_router_node",
        intent_router_route,
        {
            "query_expand_node": "query_expand_node",
            "end": END,
        },
    )
    workflow.add_conditional_edges("query_expand_node", query_expand_conditional_edges)
    workflow.add_edge("retriever_node_parallel", "aggregator_node")
    workflow.add_edge("aggregator_node", END)

    graph = workflow.compile()
    return graph

def old_run_graph(query = "Can I get a Tablet for my kid, a watch for me, a laptop for my wife and a waterproof speaker for our party next week?", initial_state=None):
    from typing import Any
    initial_state_data: Any = {
        "initial_query": query
    }

    graph = old_compile_graph()
    result = graph.invoke(initial_state_data)
    print(result.get("answer", []))
    return result.get("answer", "")

def compile_agent_graph(qdrant_client=None, checkpointer=None):

    workflow = StateGraph(State)

    tools = [get_formatted_context, get_formatted_reviews_context, get_formatted_items_context]
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

    graph = workflow.compile(checkpointer=checkpointer)

    return graph, tool_descriptions

@traceable(
    name="normalize_graph_result",
    run_type="llm",
    tags=["execution"]
)
def _normalize_graph_result(result: dict, query_text: str) -> dict:
        normalized = dict(result or {})

        def _message_signature(message):
            return (
                getattr(message, 'type', None),
                getattr(message, 'content', None),
                getattr(message, 'name', None),
                getattr(message, 'tool_name', None),
                getattr(message, 'tool_call_id', None),
            )

        def _dedupe_consecutive_messages(messages):
            deduped = []
            last_signature = None
            for message in messages or []:
                signature = _message_signature(message)
                if signature == last_signature:
                    continue
                deduped.append(message)
                last_signature = signature
            return deduped

        def _message_to_context(message):
            if getattr(message, 'type', None) != 'tool':
                return None
            content = getattr(message, 'content', '') or ''
            return {
                'tool_name': getattr(message, 'name', None) or getattr(message, 'tool_name', None) or 'get_formatted_context',
                'tool_call_id': getattr(message, 'tool_call_id', None),
                'content': content,
                'status': getattr(message, 'status', None),
            }

        def _message_to_reference(message):
            context_item = _message_to_context(message)
            if not context_item:
                return None
            content = context_item['content'].strip()
            if not content:
                return None
            return {
                'id': context_item['tool_call_id'] or context_item['tool_name'] or 'retrieved_context',
                'review': content,
                'description': content[:300],
            }

        # Deduplicate consecutive identical messages (helps remove repetition)
        normalized['messages'] = _dedupe_consecutive_messages(normalized.get('messages') or [])

        # Prefer retriever-structured results (they include `query_used`) when available.
        retriever_candidates = []
        for item in normalized.get('retrieved_context', []) or []:
            if isinstance(item, dict) and ('retrieved_contexts' in item or 'retrieved_contexts' in item):
                snippets = item.get('retrieved_contexts', []) or []
                ids = item.get('retrieved_context_ids', []) or []
                ratings = item.get('retrieved_context_ratings', []) or []
                parts = []
                for i, s in enumerate(snippets[:3]):
                    pid = ids[i] if i < len(ids) else None
                    rating = ratings[i] if i < len(ratings) else None
                    parts.append(f"Product ID: {pid}\nDescription: {s}\nRating: {rating}\n")
                content = "\n".join(parts).strip()
                retriever_candidates.append({
                    'tool_name': 'get_formatted_context',
                    'tool_call_id': item.get('query_used') or item.get('focus_product') or None,
                    'content': content,
                    'query_used': item.get('query_used') or item.get('focus_product') or None,
                    'status': 'retrieved',
                })

        if retriever_candidates:
            normalized['retrieved_context'] = retriever_candidates

        # Fall back to parsing tool messages only if retriever-structured results are not present
        tool_messages = [
            message for message in (normalized.get('messages') or [])
            if getattr(message, 'type', None) == 'tool'
        ]

        if not normalized.get('retrieved_context'):
            parsed_retrieved_context = [
                context_item for context_item in (_message_to_context(message) for message in tool_messages)
                if context_item and context_item.get('content')
            ]
            if parsed_retrieved_context:
                normalized['retrieved_context'] = parsed_retrieved_context

        # If retrieved_context still empty or only fallback placeholders, attempt to run the tool functions
        try:
            needs_populate = False
            rc_list = normalized.get('retrieved_context') or []
            if not rc_list or all((str(item.get('content','')).startswith('No retrieved context') or not item.get('content')) for item in rc_list):
                needs_populate = True
        except Exception:
            needs_populate = False

        if needs_populate:
            populated = []
            for tc in normalized.get('tool_calls', []) or []:
                q = None
                if isinstance(tc, dict):
                    q = (tc.get('arguments') or {}).get('query')
                else:
                    if hasattr(tc, 'model_dump'):
                        try:
                            tc_dict = tc.model_dump()
                            q = (tc_dict.get('arguments') or {}).get('query')
                        except Exception:
                            q = getattr(tc, 'arguments', {}).get('query') if isinstance(getattr(tc, 'arguments', {}), dict) else None
                    else:
                        args = getattr(tc, 'arguments', getattr(tc, 'args', {})) or {}
                        q = args.get('query')
                if not q:
                    continue
                try:
                    # call notebook helper to retrieve formatted context for this query
                    formatted = get_formatted_context(q)
                except Exception:
                    formatted = ''
                populated.append({
                    'tool_name': 'get_formatted_context',
                    'tool_call_id': q,
                    'content': formatted or 'No retrieved context available yet.',
                    'query_used': q,
                    'status': 'retrieved',
                })
            if populated:
                normalized['retrieved_context'] = populated

        # Build referencesfrom retrieved_context (prefer `query_used` as id when available)
        parsed_references = []
        for item in normalized.get('retrieved_context', []) or []:
            if not item:
                continue
            review = (item.get('content') or '') if isinstance(item, dict) else ''
            if not review:
                continue
            ref_id = item.get('query_used') or item.get('tool_call_id') or item.get('id') or item.get('tool_name') or 'retrieved_context'
            parsed_references.append({
                'id': ref_id,
                'review': review,
                'description': (item.get('description') or review)[:300],
            })

        if parsed_references:
            # Deduplicate references by id preserving order
            seen = set()
            deduped_refs = []
            for r in parsed_references:
                if r['id'] in seen:
                    continue
                seen.add(r['id'])
                deduped_refs.append(r)
            normalized['references'] = deduped_refs

        # Ensure tool_calls exists and includes per-query arguments if possible
        if not normalized.get('tool_calls'):
            normalized['tool_calls'] = [
                {
                    'tool_name': 'get_formatted_context',
                    'arguments': {'query': query_text, 'top_k': 5},
                }
            ]
        else:
            # Normalize any ToolCall model objects into dicts and populate missing `arguments.query`
            tool_calls_list = []
            for idx, tc in enumerate(normalized.get('tool_calls') or []):
                if isinstance(tc, dict):
                    tc_name = tc.get('tool_name') or tc.get('name')
                    args = dict(tc.get('arguments') or tc.get('args') or {})
                else:
                    tc_name = getattr(tc, 'tool_name', getattr(tc, 'name', None))
                    if hasattr(tc, 'model_dump'):
                        try:
                            tc_dict = tc.model_dump()
                            args = dict(tc_dict.get('arguments') or tc_dict.get('args') or {})
                        except Exception:
                            args = dict(getattr(tc, 'arguments', getattr(tc, 'args', {}) ) or {})
                    else:
                        args = dict(getattr(tc, 'arguments', getattr(tc, 'args', {}) ) or {})
                if not args.get('query'):
                    rc = normalized.get('retrieved_context') or []
                    if idx < len(rc):
                        args['query'] = rc[idx].get('query_used') or rc[idx].get('tool_call_id') or args.get('query')
                tool_calls_list.append({'tool_name': tc_name, 'arguments': args})
            normalized['tool_calls'] = tool_calls_list

        # Fallbacks if nothing found
        if not normalized.get('retrieved_context'):
            normalized['retrieved_context'] = [
                {
                    'tool_name': 'get_formatted_context',
                    'tool_call_id': 'fallback_context',
                    'content': normalized.get('answer', '') or 'No retrieved context was returned by the graph.',
                    'status': 'fallback',
                }
            ]

        if not normalized.get('references'):
            fallback_review = normalized.get('answer', '') or 'Fallback reference created because the graph returned no explicit references.'
            normalized['references'] = [
                {
                    'id': 'fallback_context',
                    'review': fallback_review,
                    'description': 'Fallback reference created because the graph returned no explicit references.',
                }
            ]

        last_assistant_finished = False
        for message in reversed(normalized.get('messages') or []):
            if getattr(message, 'type', None) == 'ai' or (isinstance(message, dict) and message.get('role') == 'assistant'):
                tool_calls = getattr(message, 'tool_calls', None) if not isinstance(message, dict) else message.get('tool_calls')
                last_assistant_finished = not bool(tool_calls)
                break
        normalized['final_answer'] = bool(normalized.get('final_answer')) or last_assistant_finished
        return normalized

import threading
from psycopg_pool import ConnectionPool

from typing import Any

_pool_lock = threading.Lock()
_pool_instance: Any = None
_graph_cache = {}

def get_compiled_graph(db_uri: str, qdrant_client):
    global _pool_instance, _graph_cache
    if db_uri not in _graph_cache:
        with _pool_lock:
            if db_uri not in _graph_cache:
                if _pool_instance is None:
                    _pool_instance = ConnectionPool(
                        conninfo=db_uri,
                        max_size=20,
                        kwargs={"autocommit": True}
                    )
                checkpointer = PostgresSaver(_pool_instance)
                checkpointer.setup()
                graph, tool_descriptions = compile_agent_graph(qdrant_client, checkpointer=checkpointer)
                _graph_cache[db_uri] = (graph, tool_descriptions)
    return _graph_cache[db_uri]

@traceable(
    name="run_agent_graph",
    run_type="llm",
    tags=["execution"]
)
def run_agent_graph(role, qdrant_client, query, thread_id: str) -> dict:
    import os
    from typing import Any

    initial_state: dict[str, Any] = {
        "messages": [{
            "role": role,
            "content": query
        }],
        "iteration": 0
    }

    invoke_state: dict[str, Any] = dict(initial_state) if isinstance(initial_state, dict) else {}
    if 'initial_query' not in invoke_state:
        invoke_state['initial_query'] = query
    if 'messages' not in invoke_state or not invoke_state.get('messages'):
        invoke_state['messages'] = [{'role': 'user', 'content': query}]

    db_uri = os.getenv("DATABASE_URL") or "postgresql://langgraph_user:langgraph_password@localhost:5434/langgraph_db"
    if os.path.exists('/.dockerenv') and "localhost:5434" in db_uri:
        db_uri = db_uri.replace("localhost:5434", "postgres:5432")

    graph, tool_descriptions = get_compiled_graph(db_uri, qdrant_client)
    invoke_state["available_tools"] = tool_descriptions

    run_config = {"configurable": {"qdrant_client": qdrant_client, "thread_id": thread_id}}
    result = _normalize_graph_result(graph.invoke(invoke_state, config=run_config), query)
        
    return result

# result = run_agent_graph("user", None, "Can I get a Tablet for my kid, a watch for me, a laptop for my wife and a waterproof speaker for our party next week?")
# print(result)
# Can I get a Tablet for my kid, a watch for me, a laptop for my wife and a waterproof speaker for our party next week?
# Can I you provide best Laptop for my wife, a Tablet for my kid, a Watch for myself, an Water Bottle, and a Waterproof Speaker for our party next week?
# Can I Get Best Laptop?

@traceable(
    name="rag_agent_stream_wrapper",
    run_type="llm",
    tags=["execution"]
)
def rag_agent_stream_wrapper(question: str, thread_id: str, qdrant_client=None):
    """
    Executes the multi-agent RAG pipeline and yields SSE events corresponding
    to intermediate steps (analyzing, planning, tool usage) and the final answer.
    """
    import os
    import json
    
    def _string_for_sse(message: str) -> str:
        return f"data: {message}\n\n"

    def process_graph_event(chunk):
        def _is_node_start(chunk):
            if not isinstance(chunk, (list, tuple)) or len(chunk) < 2:
                return False
            # Check for debug task events
            return chunk[0] == "debug" and isinstance(chunk[1], dict) and chunk[1].get("type") == "task"

        def _tool_to_text(tool_call):
            if isinstance(tool_call, dict):
                name = tool_call.get("name") or tool_call.get("tool_name")
                args = tool_call.get("arguments") or tool_call.get("args") or {}
            else:
                name = getattr(tool_call, "name", None) or getattr(tool_call, "tool_name", None)
                args = getattr(tool_call, "arguments", None) or getattr(tool_call, "args", {}) or {}
                
            if name == "get_formatted_items_context":
                return f"Looking for items: {args.get('query', '')}"
            elif name == "get_formatted_reviews_context":
                return f"Fetching user reviews..."
            elif name == "get_formatted_context":
                return f"Retrieving general context for query: {args.get('query', '')}"
            else:
                return f"Calling tool: {name or 'unknown'}"

        if _is_node_start(chunk):
            payload = chunk[1].get("payload", {})
            node_name = payload.get("name")
            if node_name == "intent_router_node":
                return "Analysing the question..."
            elif node_name == "agent_node":
                return "Planning..."
            elif node_name == "tool_node":
                input_data = payload.get("input", {})
                tool_calls = []
                if isinstance(input_data, dict):
                    tool_calls = input_data.get("tool_calls") or []
                    # Fallback to checking messages if tool_calls not directly present
                    if not tool_calls:
                        messages = input_data.get("messages") or []
                        if messages and hasattr(messages[-1], "tool_calls"):
                            tool_calls = messages[-1].tool_calls
                else:
                    tool_calls = getattr(input_data, "tool_calls", []) or []
                
                # Format each tool call description
                texts = []
                for tc in tool_calls:
                    texts.append(_tool_to_text(tc))
                if texts:
                    return " | ".join(texts)
                return "Executing tools..."
        return None

    # Instantiate Qdrant client if not provided
    if qdrant_client is None:
        active_url = os.getenv('QDRANT_URL', 'http://localhost:6333')
        if not os.path.exists('/.dockerenv') and "qdrant:6333" in active_url:
            active_url = active_url.replace("qdrant:6333", "localhost:6333")
        qdrant_client = QdrantClient(
            url=active_url,
            api_key=os.getenv('QDRANT_API_KEY'),
            check_compatibility=False
        )

    # Compile or retrieve the graph using connection pool setup
    db_uri = os.getenv("DATABASE_URL") or "postgresql://langgraph_user:langgraph_password@localhost:5434/langgraph_db"
    if os.path.exists('/.dockerenv') and "localhost:5434" in db_uri:
        db_uri = db_uri.replace("localhost:5434", "postgres:5432")

    graph, tool_descriptions = get_compiled_graph(db_uri, qdrant_client)

    state = {
        "messages": [{"role": "user", "content": question}],
        "initial_query": question,
        "available_tools": tool_descriptions,
        "iteration": 0
    }
    
    config = {
        "configurable": {
            "thread_id": thread_id,
            "qdrant_client": qdrant_client
        }
    }

    result = {}
    
    # Run the compiled graph stream
    for chunk in graph.stream(
        state,
        config=config,
        stream_mode=["updates", "debug", "values", "checkpoints", "messages"]
    ):
        processed_chunk = process_graph_event(chunk)
        if processed_chunk:
            yield _string_for_sse(processed_chunk)
            
        if isinstance(chunk, (list, tuple)) and len(chunk) >= 2 and chunk[0] == "values":
            result = chunk[1] or {}

    # Extract final normalized graph result
    normalized = _normalize_graph_result(result, question)
    
    # Extract tool messages to build rich contexts
    messages = normalized.get("messages", [])
    tool_messages = [msg for msg in messages if getattr(msg, "type", None) == "tool"]
    
    import re
    product_ids = []
    for msg in tool_messages:
        content = getattr(msg, 'content', '') or ''
        # Find Product ID patterns (e.g. B09QKNYJBL)
        found_ids = re.findall(r'Product ID:\s*([A-Z0-9]+)', content)
        product_ids.extend(found_ids)

    # Deduplicate product IDs preserving order
    product_ids = list(dict.fromkeys(product_ids))
    used_context = []
    collection_name = os.environ.get("collection_name") or "Amazon_Electronics_Products"

    for pid in product_ids:
        try:
            scroll_result = qdrant_client.scroll(
                collection_name=collection_name,
                scroll_filter=Filter(
                    should=[
                        FieldCondition(key="parent_asin", match=MatchValue(value=pid)),
                        FieldCondition(key="product_id", match=MatchValue(value=pid)),
                    ]
                ),
                limit=1,
                with_payload=True
            )
            if scroll_result and scroll_result[0]:
                point = scroll_result[0][0]
                payload = point.payload or {}
                review = (
                    payload.get('processed_description')
                    or payload.get('description')
                    or payload.get('text')
                    or payload.get('title')
                    or ""
                )
                images = payload.get('image_url') or payload.get('images') or []
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
                    "id": payload.get('parent_asin') or payload.get('product_id') or pid,
                    "review": review,
                    "title": payload.get('title') or review[:80] or str(pid),
                    "description": review,
                    "images": image_list,
                    "videos": [],
                    "features": payload.get('features') or [],
                    "categories": payload.get('categories') or [],
                    "main_category": payload.get('main_category') or "",
                    "store": payload.get('brand') or payload.get('store') or "",
                    "price": payload.get('price'),
                    "rating_number": payload.get('rating_number'),
                    "score": 1.0,
                    "average_rating": payload.get('average_rating'),
                    "details": payload.get('details') or {},
                })
        except Exception:
            pass

    if len(used_context) < len(product_ids):
        existing_ids = {ctx["id"] for ctx in used_context}
        for msg in tool_messages:
            content = getattr(msg, 'content', '') or ''
            products = content.split("Product ID:")
            for prod in products:
                if not prod.strip():
                    continue
                lines = prod.strip().split("\n")
                pid = lines[0].strip()
                if pid in existing_ids:
                    continue
                desc = ""
                rating = None
                for line in lines[1:]:
                    if line.startswith("Description:"):
                        desc = line.replace("Description:", "").strip()
                    elif line.startswith("Rating:"):
                        try:
                            rating = float(line.replace("Rating:", "").strip())
                        except ValueError:
                            rating = None
                used_context.append({
                    "id": pid,
                    "review": desc,
                    "title": desc[:80] if desc else pid,
                    "description": desc,
                    "images": [],
                    "videos": [],
                    "features": [],
                    "categories": [],
                    "main_category": "",
                    "store": "",
                    "price": None,
                    "rating_number": None,
                    "score": 1.0,
                    "average_rating": rating,
                    "details": {},
                })
                existing_ids.add(pid)

    current_run = get_current_run_tree()
    trace_id = str(getattr(current_run, "trace_id", current_run.id)) if current_run else ""

    yield _string_for_sse(json.dumps(
        {
            "type": "final_answer",
            "data": {
                "answer": normalized.get("answer", ""),
                "used_context": used_context,
                "trace_id": trace_id
            }
        }
    ))
            