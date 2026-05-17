
from langsmith import traceable, get_current_run_tree
import openai

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
    prompt = f"""You are a helpful assistant for answering questions about
      Amazon product reviews. Use the following retrieved context 
      to answer the question. If the context does not contain relevant information, 
      say you don't know.
      Instructions:
       - Use the retrieved context to answer the question.
       - If the context does not contain relevant information, say you don't know.

    Context:
      {preprocessed_context}
      Question: {question}
      Answer:"""
    return prompt

@traceable(
        name="gen_answer",
        tags=["answer_generation", "openai"],
        run_type="llm",
        metadata={"model": "gpt-5-nano", "ls-provider": "openai"}
)
def gen_answer(prompt):
    response = openai.chat.completions.create(
        model="gpt-5-nano",
        messages=[{"role": "user", "content": prompt}]
    )

    current_run = get_current_run_tree()
    # Safely extract usage metadata from response or its raw form
    if current_run:
        try:
            usage_obj = getattr(response, "usage", None)
            if usage_obj is None and isinstance(response, dict):
                usage_obj = response.get("usage")

            prompt_tokens = getattr(usage_obj, "prompt_tokens", None) if usage_obj is not None and not isinstance(usage_obj, dict) else (usage_obj.get("prompt_tokens") if isinstance(usage_obj, dict) else None)
            completion_tokens = getattr(usage_obj, "completion_tokens", None) if usage_obj is not None and not isinstance(usage_obj, dict) else (usage_obj.get("completion_tokens") if isinstance(usage_obj, dict) else None)
            total_tokens = getattr(usage_obj, "total_tokens", None) if usage_obj is not None and not isinstance(usage_obj, dict) else (usage_obj.get("total_tokens") if isinstance(usage_obj, dict) else None)

            current_run.add_metadata({
                "usage_metadata": {
                    "input_tokens": prompt_tokens,
                    "output_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "generation_model": "gpt-5-nano",
                }
            })
        except Exception:
            logger = __import__("logging").getLogger(__name__)
            logger.debug("Failed to add generation usage metadata to run")
    return response.choices[0].message.content

@traceable(
        name="rag_pipeline",
        tags=["pipeline", "retrieval_generation"],
)
def rag_pipeline(question, qdrant_client, top_k=5):
    retrieve_context = retrieve_data(question, qdrant_client=qdrant_client, k=top_k)
    preprocessed_context = process_context(retrieve_context)
    prompt = build_prompt(preprocessed_context, question)
    answer = gen_answer(prompt)

    final_result = {
        "question": question,
        "answer": answer,
        "retrieved_context": retrieve_context
    }

    return final_result