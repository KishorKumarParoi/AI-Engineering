import os
import numpy as np
import pandas as pd
import streamlit as st
import snowflake.connector
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"
DEFAULT_SAMPLE_REVIEWS = 500
TOP_K = 5
CACHE_FILE = "review_embeddings.parquet"

def get_openai_client(api_key: str | None = None) -> OpenAI:
    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError("OPENAI_API_KEY not found in environment or arguments.")
    return OpenAI(api_key=key)

def get_snowflake_connection():
    user = os.getenv("SNOWFLAKE_USER") or os.getenv("SNOWFLAKE_USERNAME")
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=user,
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "ZOMATO_WH"),
        database=os.getenv("SNOWFLAKE_DATABASE", "ZOMATO"),
        schema=os.getenv("SNOWFLAKE_SCHEMA", "STAGING"),
        role=os.getenv("SNOWFLAKE_ROLE", "DBT_ROLE"),
    )

def read_reviews_from_snowflake(limit=DEFAULT_SAMPLE_REVIEWS):
    conn = get_snowflake_connection()
    try:
        query = f"""
            SELECT REVIEW_ID, CITY, RATING, COMMENT
            FROM ZOMATO.STAGING.STG_REVIEWS SAMPLE ({limit} ROWS)
            WHERE COMMENT IS NOT NULL
        """
        df = conn.cursor().execute(query).fetch_pandas_all()
    except Exception:
        query = f"""
            SELECT REVIEW_ID, CITY, RATING, COMMENT
            FROM ZOMATO.STAGING.STG_REVIEWS
            WHERE COMMENT IS NOT NULL
            LIMIT {limit}
        """
        df = conn.cursor().execute(query).fetch_pandas_all()
    finally:
        conn.close()

    df.columns = [col.lower() for col in df.columns]
    return df

def embed(texts, client: OpenAI | None = None):
    if client is None:
        client = get_openai_client()
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts
    )
    return [item.embedding for item in response.data]

def cosine_similarity(vec_a, vec_b):
    return np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))

def find_similar_reviews(question, df, client: OpenAI | None = None, top_k=TOP_K):
    question_vector = embed([question], client=client)[0]
    scores = [cosine_similarity(question_vector, review_vec) for review_vec in df["embedding"]]
    df = df.copy()
    df["score"] = scores
    return df.nlargest(top_k, "score")

def ask_llm(question, top_reviews, client: OpenAI | None = None):
    if client is None:
        client = get_openai_client()
    context = ""
    for _, row in top_reviews.iterrows():
        context += f"({row['city']}, {row['rating']} stars): {row['comment']}\n"

    system_prompt = (
        "You are an AI assistant analyzing customer feedback for a food delivery platform. "
        "Answer ONLY using the customer reviews provided. "
        "Be concise and factual. If the reviews don't cover the question, state that clearly."
    )
    user_prompt = f"Question: {question}\n\nReviews:\n{context}"

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )
    return response.choices[0].message.content

def render_ui():
    st.set_page_config(page_title="Zomato Reviews RAG Chat", page_icon="🍔", layout="wide")
    st.title("Chat with your Zomato Reviews")
    st.caption(f"Semantic RAG retrieval with {EMBEDDING_MODEL} and reasoning by {CHAT_MODEL}")

    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        openai_key = st.sidebar.text_input("OpenAI API Key", type="password", help="Enter your OpenAI API key or set OPENAI_API_KEY in .env")

    if not openai_key:
        st.info("Please provide an OpenAI API Key in the sidebar or via the `.env` file to chat with reviews.")
        st.stop()

    client = OpenAI(api_key=openai_key)

    @st.cache_data(show_spinner="Loading and embedding reviews...")
    def load_reviews():
        if os.path.exists(CACHE_FILE):
            return pd.read_parquet(CACHE_FILE)
        try:
            df = read_reviews_from_snowflake()
            df["embedding"] = embed(df["comment"].tolist(), client=client)
            df.to_parquet(CACHE_FILE)
            return df
        except Exception as e:
            st.error(f"Failed to load reviews from Snowflake: {e}")
            return pd.DataFrame()

    review_df = load_reviews()

    if review_df.empty:
        st.warning("No reviews loaded. Ensure Snowflake has data in ZOMATO.STAGING.STG_REVIEWS.")
    else:
        st.sidebar.metric("Loaded Reviews in Index", len(review_df))
        if st.sidebar.button("Re-embed / Refresh Cache"):
            if os.path.exists(CACHE_FILE):
                os.remove(CACHE_FILE)
            st.cache_data.clear()
            st.rerun()

        question = st.text_input(
            "Ask a question about your reviews:",
            placeholder="e.g. What are the most common complaints about delivery in Bangalore?"
        )

        if question:
            with st.spinner("Finding relevant reviews and answering..."):
                top_reviews = find_similar_reviews(question, review_df, client=client)
                answer = ask_llm(question, top_reviews, client=client)

            st.subheader("Answer")
            st.write(answer)

            with st.expander("Reviews retrieved for this context"):
                st.dataframe(top_reviews[["city", "rating", "comment", "score"]], hide_index=True)

if __name__ == "__main__":
    render_ui()