
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


def get_embedding(text, model="text-embedding-3-small"):
    response = openai.embeddings.create(
        input=text,
        model=model
    )
    return response.data[0].embedding

def retrieve_data(query, qdrant_client=qdrant_client, k=5):
    query_embedding = get_embedding(query)
    results = qdrant_client.query_points(
        collection_name="Amazon_Electronics_Products",
        query=query_embedding,
        limit=k,
        with_payload=True,
    )

    print("results.points: ", results.points)

    retrieved_context_ids = []
    retrieve_context = []
    similarity_scores = []
    retrieved_context_rating_numbers = []
    retrieve_context_main_categories = []
    retrieve_context_prices = []
    retrieve_context_images = []
    retrieve_context_videos = []
    retrieve_context_stores = []
    retrieve_context_categories = []
    retrieve_context_details = []
    retrieve_context_descriptions = []
    retrieve_context_features = []

    for result in results.points:
        payload = result.payload or {}
        retrieved_context_ids.append(result.id)
        similarity_scores.append(result.score)
        retrieve_context.append(payload.get('text', ''))
        retrieved_context_rating_numbers.append(payload.get('rating_number', None))
        retrieve_context_main_categories.append(payload.get('main_category', None))
        retrieve_context_prices.append(payload.get('price', None))
        retrieve_context_images.append(payload.get('images', None))
        retrieve_context_videos.append(payload.get('videos', None))
        retrieve_context_stores.append(payload.get('store', None))
        retrieve_context_categories.append(payload.get('categories', None))
        retrieve_context_details.append(payload.get('details', None))
        retrieve_context_descriptions.append(payload.get('description', None))
        retrieve_context_features.append(payload.get('features', None))

    return {
        'retrieved_context_ids': retrieved_context_ids,
        'retrieve_context': retrieve_context,
        'similarity_scores': similarity_scores,
        'retrieved_context_rating_numbers': retrieved_context_rating_numbers,
        'retrieve_context_main_categories': retrieve_context_main_categories,
        'retrieve_context_prices': retrieve_context_prices,
        'retrieve_context_images': retrieve_context_images,
        'retrieve_context_videos': retrieve_context_videos,
        'retrieve_context_stores': retrieve_context_stores,
        'retrieve_context_categories': retrieve_context_categories,
        'retrieve_context_details': retrieve_context_details,
        'retrieve_context_descriptions': retrieve_context_descriptions,
        'retrieve_context_features': retrieve_context_features,
    }

def process_context(context):
    formatted_context = []
    count = len(context.get('retrieved_context_ids', []))

    for index in range(count):
        point_id = context['retrieved_context_ids'][index]
        text = context['retrieve_context'][index] if index < len(context.get('retrieve_context', [])) else ''
        score = context['similarity_scores'][index] if index < len(context.get('similarity_scores', [])) else None
        rating_number = context['retrieved_context_rating_numbers'][index] if index < len(context.get('retrieved_context_rating_numbers', [])) else None
        main_category = context['retrieve_context_main_categories'][index] if index < len(context.get('retrieve_context_main_categories', [])) else ''
        price = context['retrieve_context_prices'][index] if index < len(context.get('retrieve_context_prices', [])) else None
        images = context['retrieve_context_images'][index] if index < len(context.get('retrieve_context_images', [])) else []
        videos = context['retrieve_context_videos'][index] if index < len(context.get('retrieve_context_videos', [])) else []
        store = context['retrieve_context_stores'][index] if index < len(context.get('retrieve_context_stores', [])) else ''
        categories = context['retrieve_context_categories'][index] if index < len(context.get('retrieve_context_categories', [])) else []
        details = context['retrieve_context_details'][index] if index < len(context.get('retrieve_context_details', [])) else ''
        description = context['retrieve_context_descriptions'][index] if index < len(context.get('retrieve_context_descriptions', [])) else ''
        features = context['retrieve_context_features'][index] if index < len(context.get('retrieve_context_features', [])) else []

        formatted_context.append(
            f"ID: {point_id}\n"
            f"Score: {score}\n"
            f"Rating Number: {rating_number}\n"
            f"Main Category: {main_category}\n"
            f"Price: {price}\n"
            f"Store: {store}\n"
            f"Categories: {categories}\n"
            f"Details: {details}\n"
            f"Description: {description}\n"
            f"Features: {features}\n"
            f"Images: {images}\n"
            f"Videos: {videos}\n"
            f"Text: {text}\n---"
        )

    return "\n".join(formatted_context)

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


def gen_answer(prompt):
    # Call may return different shapes depending on client used (OpenAI SDK or a helper
    # that returns a Pydantic model). Handle both cases and normalize to a dict.
    response, raw_response = client.chat.completions.create_with_completion(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_model=RagGenerationResponse,
    )

    return response, raw_response
   


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
        "original_output": answer_text,
        "raw_gen": raw_gen,
        "answer": answer_text.answer if isinstance(answer_text, RagGenerationResponse) else answer_text,
        "references": answer_text.references if isinstance(answer_text, RagGenerationResponseReference) else [],
        "retrieved_context_ids": retrieve_context['retrieved_context_ids'],
        "retrieved_context": retrieve_context,
        "similarity_scores": retrieve_context['similarity_scores'],
        "rag_generation_response": rag_generation_response,
    }

    return final_result
