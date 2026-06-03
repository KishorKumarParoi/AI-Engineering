from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

import pandas as pd
from google import genai
import openai

def check_data(df):
    print("Checking for missing values...")
    for col in df.columns:
        if df[col].isnull().sum() > 0:
            print(f"Column '{col}' has {df[col].isnull().sum()} missing values.")
    print("\nChecking data types...")
    print(df.dtypes)
    #  fix missing values and data types if necessary
    # For example, if 'image_url' has missing values, you could fill them with a placeholder or drop those rows:
    df['price'] = df['price'].fillna(df['price'].mean())
    df['store'] = df['store'].fillna(df['store'].mode()[0])
    print("\nAfter handling missing values:")
    print(df.isnull().sum())

def preprocess_review(review):
    return {
        'product_id': review['product_id'], 
        'main_category': review['main_category'],
        'title': review['title'],
        'average_rating': review['average_rating'],
        'rating_number': review['rating_number'],
        'features': review['features'],
        'description': review['description'],
        'price': review['price'],
        'images': review['images'],
        'videos': review['videos'],
        'store': review['store'],
        'categories': review['categories'],
        'details': review['details'],
        'parent_asin': review['parent_asin'],
    }

def get_embedding(text):
    response = openai.embeddings.create(
        input = text,
        model = "text-embedding-3-small"
    )
    return response.data[0].embedding
    
def populate_qdrant(df, qdrant_client, collection_name="Amazon_Electronics_Products"):
    # check the data before processing
    check_data(df)
    data_to_embed = df.apply(preprocess_review, axis=1).tolist()

    qdrant_client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
    )

    pointstructs = []
    for idx, review in enumerate(data_to_embed):
        embedding = get_embedding(review['title'])
    pointstructs.append(PointStruct(
        id=idx,
        vector=embedding,
        payload={
            'product_id': review['product_id'],
            'text': review['title'],
            'description': review['description'],
            'images': review['images'],
            'videos': review['videos'],
            'price': review['price'],
            'rating_number': review['rating_number'],
            'main_category': review['main_category'],
            'categories': review['categories'],
            'store': review['store'],
            'details': review['details'],
            'features': review['features'],
        }
    ))

    batch_size = 128

    for start in range(0, len(pointstructs), batch_size):
        batch = pointstructs[start:start + batch_size]
        qdrant_client.upsert(
            collection_name=collection_name,
            wait=True,
            points=batch,
        )

    print(f"Upserted {len(pointstructs)} points in batches of {batch_size}.")

def retrieve_data(qdrant_client, query, collection_name="Amazon_Electronics_Products", k=5):
    query_embedding = get_embedding(query)
    results = qdrant_client.query_points(
        collection_name=collection_name,
        query=query_embedding,
        limit=k
    )
    return results
