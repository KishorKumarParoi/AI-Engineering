
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
    if current_run and response.usage:
        # `add_metadata` is a method on the run object; call it with a dict
        try:
            current_run.add_metadata({
                "usage_metadata": {
                    "input_tokens": response.usage.prompt_tokens,
                    "total_tokens": response.usage.total_tokens,
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
    if current_run:
        try:
            current_run.add_metadata({
                "usage_metadata": {
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
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