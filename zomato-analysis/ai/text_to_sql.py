import os
import json
import pandas as pd
import streamlit as st
import snowflake.connector
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

MODEL = "gpt-4o-mini"

FORBIDDEN_WORDS = [
    "drop", "delete", "truncate", "alter", "update", "insert",
    "create", "replace", "grant", "revoke"
]

EXAMPLE_QUESTIONS = [
    "Top 10 cities by GMV",
    "Which cuisine has the most orders?",
    "Average delivery time by city, worst first",
    "Cancel rate by payment method",
    "Top 5 restaurants by total revenue in Bangalore"
]

SCHEMA = """
Tables available (Snowflake). Use bare table names, no database or schema prefix.

DIM_RESTAURANTS(restaurant_id, restaurant_name, city, cuisine, rating, rating_count, cost_for_two)
DIM_CUSTOMERS(customer_id, customer_name, email, age, age_segment, gender, marital_status, occupation, income_band, family_size)
DIM_FOOD(food_id, food_name, category)
DIM_DATE(date_day, year, month, month_name, day, day_of_week, day_name, quarter, is_weekend)

FCT_ORDERS(order_id, order_timestamp, order_date, customer_id, restaurant_id, city, cuisine,
           items_count, sales_qty, subtotal, discount, delivery_fee, gst, sales_amount,
           currency, payment_method, order_status, is_delivered, customer_rating, delivery_time_min)

FCT_ORDER_ITEMS(order_item_id, order_id, restaurant_id, food_id, price, quantity, line_amount)

MART_DAILY_CITY_REVENUE(order_date, city, orders, delivered_orders, cancel_rate, gmv, aov)
MART_RESTAURANT_PERFORMANCE(restaurant_id, restaurant_name, city, cuisine, orders, delivered_orders, revenue, avg_customer_rating, cancel_rate)
MART_DELIVERY_SLA(city, order_hour, delivered_orders, p50_delivery_min, p90_delivery_min, late_rate)
MART_REVIEW_INSIGHTS(restaurant_id, restaurant_name, city, total_reviews, avg_rating, sentiment_ratio, top_topics)

Note: GMV means delivered revenue (or sales_amount when is_delivered = true). Prefer the MART_ tables when they fit the question.
"""

SYSTEM_PROMPT = f"""
You are a Snowflake SQL expert. Write ONE SELECT query that answers the question.

Rules:
- SELECT queries only, never modify data.
- Use bare table names (e.g., FCT_ORDERS, MART_DAILY_CITY_REVENUE).
- Add a LIMIT of 100 or less, unless the question asks for a single aggregated scalar.
- Reply as JSON in this exact format: {{"sql": "your query here"}}

{SCHEMA}
"""

st.set_page_config(page_title="Zomato Text-to-SQL Analytics", page_icon="📊", layout="wide")
st.title("Chat with your Zomato Warehouse")
st.caption(f"Ask business questions in plain English; {MODEL} writes the Snowflake SQL")

openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    openai_key = st.sidebar.text_input("OpenAI API Key", type="password", help="Enter your OpenAI API key or set OPENAI_API_KEY in .env")

if not openai_key:
    st.info("Please provide an OpenAI API Key in the sidebar or via the `.env` file to generate SQL.")
    st.stop()

client = OpenAI(api_key=openai_key)

@st.cache_resource
def get_connection():
    user = os.getenv("SNOWFLAKE_USER") or os.getenv("SNOWFLAKE_USERNAME")
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=user,
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "ZOMATO_WH"),
        database=os.getenv("SNOWFLAKE_DATABASE", "ZOMATO"),
        schema=os.getenv("SNOWFLAKE_SCHEMA", "MARTS"),
        role=os.getenv("SNOWFLAKE_ROLE", "DBT_ROLE"),
    )

def generate_sql(question):
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question}
        ]
    )
    answer = response.choices[0].message.content
    sql = json.loads(answer)["sql"]
    sql = sql.replace("ZOMATO.MARTS.", "").replace("ZOMATO.", "")
    return sql.strip().rstrip(";")

def is_safe(sql):
    lowered = sql.lower()
    if not (lowered.startswith("select") or lowered.startswith("with")):
        return False
    for word in FORBIDDEN_WORDS:
        # Check whole word or enclosed in spaces/punctuation
        if f" {word} " in f" {lowered} ":
            return False
    return True

def run_query(sql):
    conn = get_connection()
    cursor = conn.cursor()
    return cursor.execute(sql).fetch_pandas_all()

with st.sidebar:
    st.header("Example Questions")
    for q in EXAMPLE_QUESTIONS:
        st.markdown(f"- {q}")

question = st.text_input(
    "Enter your business question:",
    placeholder="e.g. Top 10 cities by GMV in 2024"
)

if question:
    with st.spinner("Generating SQL query..."):
        try:
            sql = generate_sql(question)
        except Exception as e:
            st.error(f"Error communicating with OpenAI: {e}")
            st.stop()

    st.subheader("Generated SQL")
    st.code(sql, language="sql")

    if not is_safe(sql):
        st.error("The generated SQL contains forbidden keywords or is not a read-only query. Execution blocked for security.")
    else:
        try:
            with st.spinner("Running query against Snowflake..."):
                df = run_query(sql)
            st.success(f"Returned {len(df)} rows")
            st.dataframe(df, use_container_width=True, hide_index=True)

            if len(df.columns) >= 2 and pd.api.types.is_numeric_dtype(df.iloc[:, 1]):
                col_x, col_y = df.columns[0], df.columns[1]
                st.subheader("Visualization")
                st.bar_chart(df.set_index(col_x)[col_y])
        except Exception as e:
            st.error(f"Error running Snowflake query: {e}")
