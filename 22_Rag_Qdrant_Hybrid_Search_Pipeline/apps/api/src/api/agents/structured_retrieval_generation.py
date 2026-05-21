
from unittest import result

from qdrant_client.models import FieldCondition, Filter, MatchValue

import instructor
from langsmith import traceable, get_current_run_tree
import openai
from pydantic import BaseModel, Field
import numpy as np
import os
from dotenv import load_dotenv

# Load environment variables from .env file
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


client = instructor.from_openai(openai.OpenAI())

class RagGenerationResponse(BaseModel):
    answer: str = Field(description="The answer to the question")
    reasoning: str = Field(description="The reasoning behind the answer")

class RAGUsedContext(BaseModel):
    id: str = Field(description="The ID of the retrieved review")
    review: str = Field(description="The text of the retrieved review")

class RagGenerationResponseReference(BaseModel):
    answer: str = Field(description="The answer to the question")
    reasoning: str = Field(description="The reasoning behind the answer")
    used_context: list[RAGUsedContext] = Field(description="The list of retrieved reviews used to generate the answer")
    references: list[RAGUsedContext] = Field(description="The list of references used to generate the answer")

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
        name="retrieve_data",
        tags=["retrieval", "qdrant"],
        run_type="retriever"
)
def retrieve_data(query, qdrant_client, k=5):   
    query_embedding = get_embedding(query)
    results = qdrant_client.query_points(
        collection_name="amazon_reviews_collection",
        query=query_embedding,
        limit=k
    )

    retrieved_context_ids = []
    retrieve_context = []
    similarity_scores = []
    retrieved_context_ratings = []
    retrieve_context_details = []
    retrieve_context_product_names = []
    retrieve_context_helpful_votes = []

    for result in results.points:
        payload = result.payload or {}
        retrieved_context_ids.append(payload.get('product_id'))
        retrieve_context.append(payload.get('review_text', ''))
        similarity_scores.append(result.score)
        retrieved_context_ratings.append(payload.get('rating', 0))
        retrieve_context_helpful_votes.append(payload.get('helpful_votes', 0))
        retrieve_context_product_names.append(payload.get('product_name', ''))
        retrieve_context_details.append(payload.get('details', ''))

    return {
        'retrieved_context_ids': retrieved_context_ids,
        'retrieve_context': retrieve_context,
        'similarity_scores': similarity_scores,
        'retrieved_context_ratings': retrieved_context_ratings,
        'retrieve_context_details': retrieve_context_details,
        'retrieve_context_product_names': retrieve_context_product_names,
        'retrieve_context_helpful_votes': retrieve_context_helpful_votes
    }

@traceable(
        name="process_context",
        tags=["context_processing"],
        run_type="prompt"
)
def process_context(context):
    formatted_context = []
    for id, chunk, rating, details, product_name, helpful_votes in zip(context['retrieved_context_ids'], context['retrieve_context'], context['retrieved_context_ratings'], context['retrieve_context_details'], context['retrieve_context_product_names'], context['retrieve_context_helpful_votes']):
        formatted_context.append(f"ID: {id}\nRating: {rating}\nReview: {chunk}\nDetails: {details}\nProduct Name: {product_name}\nHelpful Votes: {helpful_votes}\n---")
    return "\n".join(formatted_context)

@traceable(
        name="build_prompt",
        tags=["prompt_construction"],
        run_type="prompt"
)
def build_prompt(preprocessed_context, question):
    prompt = f"""You are a helpful shopping assistant for answering questions about
      products in stock.
      You will be given a question and a lits of context

      Instructions:
      - You need to answer the question based on the provided context only
      - Never use word context and refer to it as the available products
      - As an output you need to provide:

      * The answer to the question based on the provided context
      * The list of the IDs of the chuns that were used to answer the question.
      only return the ones that are used in the answer.
      * Short description (1-2 sentences) of the item based on the description provided in the context

      - The short description should have the name of the item.
      - The answer to the question should contain detailed information about the product and returned with
      detailed specification in bullet points.

      Context:
        {preprocessed_context}
    Question: {question}
    """ 
    return prompt

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
    retrieve_context = retrieve_data(question, qdrant_client=qdrant_client, k=top_k)
    preprocessed_context = process_context(retrieve_context)
    prompt = build_prompt(preprocessed_context, question)
    gen, raw_gen = gen_answer(prompt)

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
        "answer": answer_text.answer if isinstance(answer_text, RagGenerationResponse) else answer_text,
        "retrieved_context": retrieve_context,
        "rag_generation_response": rag_generation_response,
    }

    return final_result


def rag_pipeline_wrapper(question, qdrant_client, top_k=5):
    result = rag_pipeline(question, qdrant_client, top_k)

    used_context = []
    dummy_vector = np.zeros(1536).tolist()  # Replace with actual embedding vector if available

    for item in result.get('references', []):
        payload = qdrant_client.query_points(
            collection_name="amazon_reviews_collection",
            query=dummy_vector,
            limit=1,
            with_payload=True,
            query_filter = Filter(
                         must=[
                            FieldCondition(
                                key="product_id",
                                match=MatchValue(value=item.id)
                            )]
            )
        ).points[0].payload or {}
        helpful_votes = payload.get('helpful_votes', 'N/A')
        used_context.append({
            "id": item.id,
            "review": payload.get('review_text', ''),
            "helpful_votes": helpful_votes
        })

    return {   
            "answer": result["answer"] if "answer" in result else str(result),
            "used_context": used_context
        }