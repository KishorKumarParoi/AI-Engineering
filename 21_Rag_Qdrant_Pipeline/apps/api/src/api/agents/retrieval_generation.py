
import openai
from qdrant_client import QdrantClient
import os

def get_embedding(text, model="text-embedding-3-small"):
    response = openai.embeddings.create(
        input=text,
        model=model
    )
    return response.data[0].embedding

def retrieve_data(query, qdrant_client=None, k=5):
    if qdrant_client is None:
        qdrant_client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))
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

def process_context(context):
    formatted_context = []
    for id, chunk, rating, details, product_name, helpful_votes in zip(context['retrieved_context_ids'], context['retrieve_context'], context['retrieved_context_ratings'], context['retrieve_context_details'], context['retrieve_context_product_names'], context['retrieve_context_helpful_votes']):
        formatted_context.append(f"ID: {id}\nRating: {rating}\nReview: {chunk}\nDetails: {details}\nProduct Name: {product_name}\nHelpful Votes: {helpful_votes}\n---")
    return "\n".join(formatted_context)


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

def gen_answer(prompt):
    response = openai.chat.completions.create(
        model="gpt-5-nano",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def rag_pipeline(question, top_k=5):
    qdrant_client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))
    retrieve_context = retrieve_data(question, qdrant_client=qdrant_client, k=top_k)
    preprocessed_context = process_context(retrieve_context)
    prompt = build_prompt(preprocessed_context, question)
    answer = gen_answer(prompt)
    return answer 