
from pydantic import BaseModel, Field
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from langsmith import traceable, get_current_run_tree, Client

from api.agents.modified_single_agent.tools import AgentResponse, IntentRouterResponse, RAGUsedContext, prompt_template_config, prompt_template_registry, QueryExpandResponse, AggregatorResponse, State, RagGenerationResponseReference, ToolCall, query_expand_conditional_edges, query_expand_node, retriever_node_parallel, aggregator_node, get_formatted_context
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
    initial_state = {
        "initial_query": query
    }

    graph = old_compile_graph()
    result = graph.invoke(initial_state)
    print(result.get("answer", []))
    return result.get("answer", "")

@traceable(
    name="compile_agent_graph",
    run_type="llm",
    tags=["execution"]
)
def compile_agent_graph(qdrant_client=None):

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

@traceable(
    name="run_agent_graph",
    run_type="llm",
    tags=["execution"]
)
def run_agent_graph(role,qdrant_client, query):
    graph, tool_descriptions = compile_agent_graph(qdrant_client)

    initial_state = {
    "messages": [{
        "role": role,
        "content": query
            # "role": "user",
            # "content": "Can I get a Tablet for my kid, a watch for me, a laptop for my wife and a waterproof speaker for our party next week?"
        }],
        "available_tools": tool_descriptions
    }

    invoke_state = dict(initial_state) if isinstance(initial_state, dict) else {}
    if 'initial_query' not in invoke_state:
        invoke_state['initial_query'] = query
    if 'messages' not in invoke_state or not invoke_state.get('messages'):
        invoke_state['messages'] = [{'role': 'user', 'content': query}]

    run_config = {"configurable": {"qdrant_client": qdrant_client}}
    result = _normalize_graph_result(graph.invoke(invoke_state, config=run_config), query)
    # print(result.get('answer', ''))
    return result

# result = run_agent_graph("user", None, "Can I get a Tablet for my kid, a watch for me, a laptop for my wife and a waterproof speaker for our party next week?")
# print(result)
# Can I get a Tablet for my kid, a watch for me, a laptop for my wife and a waterproof speaker for our party next week?
# Can I you provide best Laptop for my wife, a Tablet for my kid, a Watch for myself, an Water Bottle, and a Waterproof Speaker for our party next week?
# Can I Get Best Laptop?