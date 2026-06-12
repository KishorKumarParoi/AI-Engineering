from qdrant_client import QdrantClient
from qdrant_client import models
from qdrant_client.models import Distance, VectorParams, PointStruct, SparseVectorParams, Document
from qdrant_client.http.exceptions import UnexpectedResponse

import pandas as pd
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
    images = review.get('images') or []
    image_url = None
    if isinstance(images, list) and images:
        first_image = images[0]
        if isinstance(first_image, dict):
            image_url = first_image.get('large') or first_image.get('thumb') or first_image.get('hi_res')
        elif isinstance(first_image, str):
            image_url = first_image

    description = review.get('description')
    if isinstance(description, list):
        description = " ".join(str(item) for item in description if item is not None)

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
        'processed_description': description or review.get('title') or "",
        'image_url': image_url,
    }

def get_embedding(text):
    response = openai.embeddings.create(
        input = text,
        model = "text-embedding-3-small"
    )
    return response.data[0].embedding

def get_embeddings_batch(text_list, model="text-embedding-3-small", batch_size=100):
    all_embeddings = []
    for i in range(0, len(text_list), batch_size):
        batch = text_list[i:i+batch_size]
        response = openai.embeddings.create(input=batch, model=model)
        all_embeddings.extend([emb.embedding for emb in response.data])
    return all_embeddings
    
def populate_qdrant(df, qdrant_client, collection_name="Amazon_Electronics_Products"):
    # check the data before processing
    check_data(df)
    data_to_embed = df.apply(preprocess_review, axis=1).tolist()

    # Ensure collection exists (create if missing). Ignore if already created concurrently.
    try:
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config={
                "text-embedding-3-small": VectorParams(size=1536, distance=Distance.COSINE)
            },
            sparse_vectors_config={
                "bm25": SparseVectorParams(modifier=models.Modifier.IDF)
            }
        )
    except Exception:
        # If creation fails due to already-exists or transient issue, continue -- upsert will handle final state
        pass

    # Batch embed the titles
    titles = [review['title'] for review in data_to_embed]
    embeddings = get_embeddings_batch(titles)

    pointstructs = []
    for idx, review in enumerate(data_to_embed):
        embedding = embeddings[idx]
        desc = review.get('processed_description') or review.get('title') or ""
        pointstructs.append(PointStruct(
            id=idx,
            vector={
                "text-embedding-3-small": embedding,
                "bm25": Document(
                    text=desc,
                    model="qdrant/bm25"
                )
            },
            payload={
                'product_id': review.get('product_id'),
                'text': review.get('title'),
                'title': review.get('title'),
                'description': review.get('description'),
                'processed_description': review.get('processed_description'),
                'images': review.get('images'),
                'videos': review.get('videos'),
                'price': review.get('price'),
                'rating_number': review.get('rating_number'),
                'average_rating': review.get('average_rating'),
                'main_category': review.get('main_category'),
                'categories': review.get('categories'),
                'store': review.get('store'),
                'details': review.get('details'),
                'parent_asin': review.get('parent_asin'),
                'image_url': review.get('image_url'),
                'features': review.get('features'),
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


def ensure_collection_exists(qdrant_client, collection_name="Amazon_Electronics_Products", vectors_size=1536, retries=10, delay=2):
    """Ensure the Qdrant collection exists; create it if missing. Retries for transient Qdrant availability."""
    import time
    for attempt in range(1, retries + 1):
        try:
            qdrant_client.get_collection(collection_name=collection_name)
            return True
        except UnexpectedResponse as e:
            status = getattr(e, 'status_code', None)
            if status == 404:
                try:
                    qdrant_client.create_collection(
                        collection_name=collection_name,
                        vectors_config={
                            "text-embedding-3-small": VectorParams(size=vectors_size, distance=Distance.COSINE)
                        },
                        sparse_vectors_config={
                            "bm25": SparseVectorParams(modifier=models.Modifier.IDF)
                        }
                    )
                    return True
                except Exception:
                    # Creation could fail transiently; fall through to retry
                    pass
            else:
                # Non-404 UnexpectedResponse -> re-raise
                raise
        except Exception:
            # Generic error, likely Qdrant not ready; retry
            pass

        time.sleep(delay)

    raise RuntimeError(f"Could not ensure collection '{collection_name}' exists after {retries} retries")

def retrieve_data(qdrant_client, query, collection_name="Amazon_Electronics_Products", k=5):
    query_embedding = get_embedding(query)
    # Ensure collection exists to avoid 404 from Qdrant
    try:
        _ = qdrant_client.get_collection(collection_name=collection_name)
    except UnexpectedResponse as e:
        if getattr(e, 'status_code', None) == 404:
            # create an empty collection with the expected vector shape
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config={
                    "text-embedding-3-small": VectorParams(size=1536, distance=Distance.COSINE)
                },
                sparse_vectors_config={
                    "bm25": SparseVectorParams(modifier=models.Modifier.IDF)
                }
            )
        else:
            raise

    # Execute dense vector search against the collection's named vector.
    results = qdrant_client.query_points(
        collection_name=collection_name,
        query=query_embedding,
        using="text-embedding-3-small",
        limit=k,
    )

    return results
