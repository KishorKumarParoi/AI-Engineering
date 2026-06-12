from api.agents.modified_single_agent.graph import run_agent_graph
from langsmith import traceable, get_current_run_tree
from pydantic import BaseModel, Field, Field
import openai
import instructor

from api.agents.modified_single_agent.tools import retrieve_data, process_context, get_formatted_context, AgentResponse, IntentRouterResponse, RAGUsedContext, prompt_template_config, prompt_template_registry, QueryExpandResponse, AggregatorResponse, State, RagGenerationResponseReference, ToolCall, query_expand_conditional_edges, query_expand_node, retriever_node_parallel, aggregator_node, get_formatted_context
from api.agents.modified_single_agent.utils import format_ai_message, parse_function_definition, get_type_from_annotation, parse_docstring_params, get_tool_descriptions
from api.agents.modified_single_agent.agent import agent_node, intent_router_node, intent_router_conditional_edges, tool_router, intent_router_route
    
class RagGenerationResponse(BaseModel):
    answer: str = Field(description="The answer to the question")
    reasoning: str = Field(description="The reasoning behind the answer")

def process_context(retrieve_context):
    preprocessed_context = ""
    for idx, context in enumerate(retrieve_context["retrieved_contexts"]):
        preprocessed_context += f"Product {idx+1}:\n{context}\n\n"
    return preprocessed_context

client = instructor.from_openai(openai.OpenAI())  # Instructor wrapper for structured responses

@traceable(
        name="build_prompt",
        tags=["prompt_construction"],
        run_type="prompt"
)
def build_prompt(preprocessed_context, question):
    template = prompt_template_config("api/prompts/retrieval_generation.yaml", "retrieval_generation_prompt")
    return template.render(preprocessed_context=preprocessed_context, question=question)

@traceable(
        name="gen_answer",
        tags=["answer_generation", "openai"],
        run_type="llm",
        metadata={"model": "gpt-4.1-mini", "ls-provider": "openai"}
)
def gen_answer(prompt):
    # Call may return different shapes depending on client used (OpenAI SDK or a helper
    # that returns a Pydantic model). Handle both cases and normalize to a dict.
    response = client.chat.completions.create_with_completion(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_model=RagGenerationResponse,
    )

    # Some clients return a tuple (model_obj, raw_response) or list; handle that.
    raw_resp = None
    if isinstance(response, (tuple, list)):
        if len(response) == 2:
            response, raw_resp = response
        else:
            response = response[0]

    # Normalize into a consistent gen_response dict
    gen_response = {
        "text": None,
        "usage": None,
        "model": None,
        "raw_response": raw_resp or response,
    }

    # If the client returned a Pydantic model (e.g., RagGenerationResponse), extract fields
    if isinstance(response, BaseModel):
        # pydantic v1/v2 compatibility: try attribute access first
        text_val = getattr(response, "answer", None) or getattr(response, "text", None)
        if text_val is None:
            # fall back to model_dump if available
            try:
                dumped = response.model_dump() if hasattr(response, "model_dump") else response.dict()
                text_val = dumped.get("answer") or dumped.get("text")
            except Exception:
                text_val = str(response)
        gen_response.update({
            "text": text_val,
            "usage": None,
            "model": getattr(response, "model", None) or None,
        })
    else:
        # Assume OpenAI-style response (has choices and usage)
        try:
            gen_text = response.choices[0].message.content
        except Exception:
            # Last-resort stringification
            try:
                # If raw_resp contains the OpenAI-style object, try there
                gen_text = raw_resp.choices[0].message.content if raw_resp is not None else str(response)
            except Exception:
                gen_text = str(response)

        # Safely extract usage from either the primary response or the raw response
        usage_source = getattr(response, "usage", None) or (getattr(raw_resp, "usage", None) if raw_resp is not None else None)
        if usage_source is None and isinstance(raw_resp, dict):
            usage_source = raw_resp.get("usage")

        def _get_token(u, name):
            if u is None:
                return None
            if hasattr(u, name):
                return getattr(u, name)
            if isinstance(u, dict):
                return u.get(name)
            return None

        gen_response.update({
            "text": gen_text,
            "usage": {
                "prompt_tokens": _get_token(usage_source, "prompt_tokens"),
                "completion_tokens": _get_token(usage_source, "completion_tokens"),
                "total_tokens": _get_token(usage_source, "total_tokens"),
            },
            "model": getattr(response, "model", None) or (getattr(raw_resp, "model", None) if raw_resp is not None else "gpt-4.1-mini"),
        })

    current_run = get_current_run_tree()
    if current_run and gen_response.get("usage"):
        try:
            current_run.add_metadata({
                "usage_metadata": gen_response["usage"]
            })
        except Exception:
            logger = __import__("logging").getLogger(__name__)
            logger.debug("Failed to add generation usage metadata to run")

    return gen_response, gen_response.get("raw_response")


@traceable(
        name="rag_pipeline",
        tags=["pipeline", "retrieval_generation"],
)
def rag_pipeline(question, qdrant_client, top_k=5):
    retrieve_context = retrieve_data(question, qdrant_client=qdrant_client, top_k=top_k)
    preprocessed_context = process_context(retrieve_context)
    prompt = build_prompt(preprocessed_context, question)
    gen, raw_gen = gen_answer(prompt)
    result = run_agent_graph(role="user", query=question, qdrant_client=qdrant_client)

    # Normalize final answer whether gen is dict-like or an object
    if isinstance(gen, dict):
        answer_text = gen.get("text") or gen.get("answer") or str(gen)
        rag_generation_response = gen
    else:
        answer_text = getattr(gen, "answer", getattr(gen, "text", str(gen)))
        # try to convert to dict if pydantic object provides model_dump
        try:
            rag_generation_response = gen.model_dump() if hasattr(gen, "model_dump") else gen.dict()
        except Exception:
            rag_generation_response = str(gen)

    final_result = {
        "question": question,
        "original_output": answer_text,
        "raw_gen": raw_gen,
        "answer": answer_text.answer if isinstance(answer_text, RagGenerationResponse) else answer_text,
        "references": answer_text.references if isinstance(answer_text, RagGenerationResponseReference) else [],
        "retrieved_context_ids": retrieve_context['retrieved_context_ids'],
        "retrieved_context": retrieve_context,
        "similarity_scores": retrieve_context['similarity_scores'],
        "rag_generation_response": rag_generation_response,
        "result": result,
    }

    return final_result

@traceable(
    name="rag_pipeline_wrapper",
    run_type="llm",
    tags=["execution"]
)
def rag_pipeline_wrapper(question, qdrant_client, top_k=5):
    pipeline_result = rag_pipeline(question, qdrant_client, top_k)
    used_context = []

    retrieved_context = pipeline_result.get("retrieved_context", {})

    if isinstance(retrieved_context, dict):
        retrieved_context_ids = retrieved_context.get("retrieved_context_ids", [])
        retrieved_contexts = retrieved_context.get("retrieved_contexts", [])
        similarity_scores = retrieved_context.get("similarity_scores", [])
        retrieved_context_ratings = retrieved_context.get("retrieved_context_ratings", [])
        retrieved_context_prices = retrieved_context.get("retrieved_context_prices", [])
        retrieved_context_images = retrieved_context.get("retrieved_context_images", [])
        retrieved_context_rating_numbers = retrieved_context.get("retrieved_context_rating_numbers", [])

        item_count = len(retrieved_context_ids)
        for index in range(item_count):
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
                "id": retrieved_context_ids[index],
                "review": review,
                "title": review[:80] if review else str(retrieved_context_ids[index]),
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

    return {
        "answer": pipeline_result.get("answer"),
        "used_context": used_context,
        "retrieved_context_ids": pipeline_result.get("retrieved_context_ids"),
        "similarity_scores": pipeline_result.get("similarity_scores"),
    }
       

