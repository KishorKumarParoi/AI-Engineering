from langsmith import traceable, get_current_run_tree, Client
from jinja2 import Template
from langchain_core.messages import convert_to_openai_messages, convert_to_messages
import instructor
from jinja2 import Template
from openai import OpenAI

import instructor
import json


from api.agents.modified_single_agent.tools import AgentResponse, IntentRouterResponse, RAGUsedContext, prompt_template_config, prompt_template_registry, QueryExpandResponse, AggregatorResponse, State, RagGenerationResponseReference, ToolCall, query_expand_conditional_edges, query_expand_node, retriever_node_parallel, aggregator_node, get_formatted_context
from api.agents.modified_single_agent.utils import format_ai_message, parse_function_definition, get_type_from_annotation, parse_docstring_params, get_tool_descriptions

@traceable(
    name="agent_node",
    run_type="llm",
    tags=["agent", "openai"],
    metadata={"model": "gpt-4.1-mini", "ls-provider": "openai"},
)
def agent_node(state: State) -> dict:
    prompt = prompt_template_config("api/agents/modified_single_agent/prompts/qna_agent.yaml", "qna_agent_prompt").render(
        available_tools=json.dumps(getattr(state, 'available_tools', []) or [], ensure_ascii=True, indent=2)
    )

    conversation = []
    for message in (getattr(state, 'messages', None) or []):
        conversation.append(convert_to_openai_messages(message))

    client = instructor.from_openai(OpenAI())
    response = client.chat.completions.create_with_completion(
        model="gpt-4.1-mini",
        response_model=AgentResponse,
        messages=[{"role": "system", "content": prompt}, *conversation],
        temperature=0.5,
        timeout=20,
    )
    if isinstance(response, (tuple, list)):
        response = response[0]

    tool_calls_raw = getattr(response, 'tool_calls', []) or []
    normalized_tool_calls = [
        {
            'tool_name': getattr(tc, 'tool_name', getattr(tc, 'name', None)),
            'arguments': dict(getattr(tc, 'arguments', getattr(tc, 'args', {})) or {}),
        }
        for tc in tool_calls_raw
    ]

    ai_message = format_ai_message(response)

    print("ai_message:", ai_message)

    def _tool_messages(messages: list) -> list[dict]:
        items = []
        for message in messages:
            if getattr(message, 'type', None) != 'tool':
                continue
            items.append({
                'tool_name': getattr(message, 'name', None) or getattr(message, 'tool_name', None) or 'tool',
                'tool_call_id': getattr(message, 'tool_call_id', None),
                'content': getattr(message, 'content', '') or '',
                'status': getattr(message, 'status', None),
            })
        return items

    def _normalize_references(context_items: list[dict]) -> list[dict]:
        refs = []
        for item in context_items:
            content = str(item.get('content', '')).strip()
            if not content:
                continue
            refs.append({
                'id': item.get('tool_call_id') or item.get('tool_name') or 'retrieved_context',
                'review': content,
                'description': content[:300],
            })
        seen = set()
        deduped = []
        for ref in refs:
            ref_id = ref.get('id')
            if ref_id in seen:
                continue
            seen.add(ref_id)
            deduped.append(ref)
        return deduped

    def _ensure_reference_dicts(items):
        normalized_items = []
        for item in items or []:
            if isinstance(item, dict):
                normalized_items.append(item)
            elif hasattr(item, 'model_dump'):
                normalized_items.append(item.model_dump())
            elif hasattr(item, 'dict'):
                normalized_items.append(item.dict())
            else:
                normalized_items.append({
                    'id': getattr(item, 'id', 'retrieved_context'),
                    'review': getattr(item, 'review', '') or '',
                    'description': getattr(item, 'description', '') or '',
                })
        return normalized_items

    existing_messages = list(getattr(state, 'messages', None) or [])
    retrieved_context_field = getattr(state, 'retrieved_context', None) or _tool_messages(existing_messages)
    if not retrieved_context_field:
        retrieved_context_field = [{
            'tool_name': 'get_formatted_context',
            'tool_call_id': None,
            'content': 'No retrieved context available yet.',
            'status': 'fallback',
        }]

    references_field = (
        getattr(response, 'references', None)
        or getattr(response, 'used_context', None)
        or getattr(state, 'references', None)
        or _normalize_references(retrieved_context_field)
    )
    references_field = _ensure_reference_dicts(references_field)
    if not references_field:
        references_field = [{
            'id': 'retrieved_context',
            'review': 'Retrieved context is available in the state.',
            'description': 'Retrieved context is available in the state.',
        }]

    tool_calls_field = normalized_tool_calls or []
    if not tool_calls_field:
        query_seed = getattr(state, 'expanded_query', []) or [getattr(state, 'initial_query', '') or '']
        query_seed = [item for item in query_seed if item]
        tool_calls_field = [
            {
                'tool_name': 'get_formatted_context',
                'arguments': {'query': query_item, 'top_k': 5},
            }
            for query_item in query_seed
        ] or [{'tool_name': 'get_formatted_context', 'arguments': {'query': getattr(state, 'initial_query', '') or '', 'top_k': 5}}]

    available_tools_field = getattr(state, 'available_tools', None) or []
    if not available_tools_field:
        available_tools_field = [{
            'name': 'get_formatted_context',
            'description': 'Retrieve and format top-k context chunks for a query',
            'arguments': {'query': 'str', 'top_k': 'int'},
        }]

    messages_field = [ai_message]

    return {
        'messages': messages_field,
        'tool_calls': tool_calls_field,
        'retrieved_context': retrieved_context_field,
        'expanded_query': getattr(state, 'expanded_query', []) or [],
        'initial_query': getattr(state, 'initial_query', '') or '',
        'answer': getattr(response, 'answer', None) or getattr(state, 'answer', '') or '',
        'question_relevant': bool(getattr(state, 'question_relevant', False)),
        'available_tools': available_tools_field,
        'final_answer': len(tool_calls_field) == 0,
        'iteration': (getattr(state, 'iteration', 0) or 0) + 1,
        'references': references_field,
    }

@traceable(
    name="old_intent_router_node",
    run_type="llm",
    tags=["routing", "openai"],
    metadata={"model": "gpt-4.1-mini", "ls-provider": "openai"}
)
def old_intent_router_node(state: State) -> dict:
    prompt_template = """You are an intent router for a shopping search assistant.
Determine if the user's question is relevant to shopping search and can be answered based on product information.
If the question is relevant, provide a concise answer. If not, politely decline to answer.
Question:
{{query}}
"""

    template = Template(prompt_template)
    prompt = template.render(query=state.initial_query)

    client = instructor.from_openai(OpenAI())

    response = client.chat.completions.create_with_completion(
        model="gpt-4.1-mini",
        response_model=IntentRouterResponse,
        messages=[{"role": "system", "content": prompt}],
        temperature=0.1,
    )

    if isinstance(response, (tuple, list)):
        response = response[0]

    return {
        "question_relevant": response.question_relevant,
        "answer": response.answer
    }

@traceable(
    name="intent_router_node",
    run_type="llm",
    tags=["routing", "openai"],
    metadata={"model": "gpt-4.1-mini", "ls-provider": "openai"}
)
def intent_router_node(state: State) -> dict:
    prompt_template = prompt_template_config("api/agents/modified_single_agent/prompts/intent_router_agent.yaml", "intent_router_agent_prompt").render()

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

@traceable(
    name="intent_router_route",
    run_type="llm",
    tags=["routing", "openai"],
    metadata={"model": "gpt-4.1-mini", "ls-provider": "openai"}
)
def intent_router_route(state):
   state_data = state.model_dump() if hasattr(state, "model_dump") else state
   question_relevant = False

   if isinstance(state_data, dict):
      question_relevant = bool(state_data.get("question_relevant", False))
   else:
      question_relevant = bool(getattr(state, "question_relevant", False))

   if question_relevant:
      return "query_expand_node"
   return END

@traceable(
    name="tool_router",
    run_type="llm",
    tags=["routing", "openai"],
    metadata={"model": "gpt-4.1-mini", "ls-provider": "openai"}
)
def tool_router(state: State) -> str:
    """Decide whether to continue or end"""
    if state.final_answer:
        return "end"
    elif state.iteration > 2:
        return "end"
    elif len(state.tool_calls) > 0:
        return "tools"
    else:
        return "end"



