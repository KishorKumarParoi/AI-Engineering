import os
import json
import snowflake.connector
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

MODEL = "gpt-4o-mini"
TOPICS = ["food quality", "delivery", "pricing", "service", "packaging", "other"]

SYSTEM_PROMPT = f"""
You classify customer reviews for a food delivery app.

For the review you are given, return:
- sentiment_label: positive, negative, or neutral
- sentiment_score: a number between -1.0 and 1.0
- topic: one of {TOPICS}
- key_issue: a short phrase of 6 words or less that describes the main issue in the review, if any. If there is no issue, return null

Reply as JSON in this exact format:
{{
    "sentiment_label": "<sentiment_label>",
    "sentiment_score": <sentiment_score>,
    "topic": "<topic>",
    "key_issue": "<key_issue>"
}}
"""

def get_connection():
    user = os.getenv("SNOWFLAKE_USER") or os.getenv("SNOWFLAKE_USERNAME")
    return snowflake.connector.connect(
        user=user,
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "ZOMATO_WH"),
        database=os.getenv("SNOWFLAKE_DATABASE", "ZOMATO"),
        schema=os.getenv("SNOWFLAKE_SCHEMA", "RAW"),
        role=os.getenv("SNOWFLAKE_ROLE", "DBT_ROLE"),
    )

def create_output_table(cursor):
    cursor.execute("CREATE SCHEMA IF NOT EXISTS ZOMATO.AI")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ZOMATO.AI.REVIEW_ENRICHED (
            REVIEW_ID STRING,
            SENTIMENT_LABEL STRING,
            SENTIMENT_SCORE FLOAT,
            TOPIC STRING,
            KEY_ISSUE STRING,
            MODEL STRING,
            ENRICHED_AT TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
        )
    """)

def get_reviews_to_enrich(cursor, sample_n=5):
    cursor.execute(f"""
        SELECT REVIEW_ID, COMMENT
        FROM ZOMATO.RAW.REVIEWS
        WHERE REVIEW_ID NOT IN (SELECT REVIEW_ID FROM ZOMATO.AI.REVIEW_ENRICHED)
          AND COMMENT IS NOT NULL
        LIMIT {sample_n}
    """)
    return cursor.fetchall()

def classify_review(client, comment):
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": comment}
        ]
    )
    answer = response.choices[0].message.content
    return json.loads(answer)

def save_results(cursor, results):
    """Insert all the enriched rows into Snowflake in one go."""
    print(f"Saving {len(results)} enriched reviews to Snowflake...")
    cursor.executemany(
        """
        INSERT INTO ZOMATO.AI.REVIEW_ENRICHED
            (review_id, sentiment_label, sentiment_score, topic, key_issue, model)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        results,
    )

def main():
    conn = get_connection()
    cursor = conn.cursor()
    create_output_table(cursor)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[WARNING] OPENAI_API_KEY is not set. Table ZOMATO.AI.REVIEW_ENRICHED ensured, but skipping LLM classification.")
        cursor.close()
        conn.close()
        return

    client = OpenAI(api_key=api_key)
    sample_n = int(os.getenv("SAMPLE_N", "5"))

    reviews = get_reviews_to_enrich(cursor, sample_n=sample_n)
    if len(reviews) == 0:
        print("No new reviews to enrich.")
        cursor.close()
        conn.close()
        return

    print(f"Enriching {len(reviews)} reviews with {MODEL}...")

    results = []
    for review_id, comment in reviews:
        print(f"Classifying review {review_id}...")
        try:
            labels = classify_review(client, comment)
            results.append((
                review_id,
                labels.get("sentiment_label"),
                float(labels.get("sentiment_score", 0.0)),
                labels.get("topic"),
                labels.get("key_issue"),
                MODEL
            ))
        except Exception as e:
            print(f"Error occurred while classifying review {review_id}: {e}")

    if results:
        save_results(cursor, results)
        conn.commit()
        print(f"Saved {len(results)} enriched reviews to ZOMATO.AI.REVIEW_ENRICHED.")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()