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

DIM_CUSTOMERS(customer_id, customer_name, email, age, generation_cohort, age_segment, gender, marital_status, occupation, income_band, education, family_size)
DIM_DATE(date_day, year, quarter, month, month_name, day_of_month, day_name, is_weekend)
DIM_FOOD(food_id, food_name, veg_or_non_veg)
DIM_RESTAURANTS(restaurant_id, restaurant_name, city, rating, rating_count, cost_for_two, cuisine, license_number, address, restaurant_url)

FCT_ORDERS(order_id, order_timestamp, order_date, customer_id, restaurant_id, city, cuisine,
           items_count, sales_qty, subtotal, discount, delivery_fee, gst, sales_amount,
           currency, payment_method, order_status, is_delivered, customer_rating, delivery_time_min)

FCT_ORDER_ITEMS(order_item_id, order_id, restaurant_id, f_id, food_id, order_ts, order_date, city, price, quantity, line_amount)

MART_DAILY_CITY_REVENUE(order_date, city, total_orders, delivered_orders, cancelled_orders, cancel_rate, gmv, aov, total_discounts_given, total_delivery_fees, avg_delivery_time_mins)

MART_RESTAURANT_PERFORMANCE(restaurant_id, restaurant_name, city, cuisine, catalog_rating, cost_for_two, total_orders, delivered_orders, total_revenue, avg_delivery_time_mins, avg_customer_rating)

MART_DELIVERY_SLA(city, order_hour, total_delivered_orders, p50_delivery_time_mins, p90_delivery_time_mins, avg_delivery_time_mins, min_delivery_time_mins, max_delivery_time_mins, under_30_mins_count, delayed_over_45_mins_count, on_time_sla_percentage)

MART_REVIEW_INSIGHTS(city, topic, sentiment_label, reviews, avg_sentiment_score, avg_star_rating, flagged_issues)

Note:
- Use exact column names from the schemas above (e.g. use TOTAL_ORDERS instead of orders, TOTAL_REVENUE instead of revenue).
- GMV means delivered revenue (or sales_amount when is_delivered = true).
- If querying for order volume by cuisine, you can use FCT_ORDERS (e.g. COUNT(*) by cuisine) or MART_RESTAURANT_PERFORMANCE (e.g. SUM(total_orders) by cuisine).
"""

SYSTEM_PROMPT = f"""
You are a Snowflake SQL expert. Write ONE SELECT query that answers the question.

Rules:
- SELECT queries only, never modify data.
- Use bare table names (e.g. FCT_ORDERS, MART_DAILY_CITY_REVENUE).
- Use exact column names from the schema provided below.
- In Snowflake SQL, for conditional aggregation use COUNT_IF(condition) or SUM(IFF(condition, 1, 0)). NEVER use PostgreSQL 'FILTER (WHERE ...)' syntax.
- Add a LIMIT of 100 or less, unless the question asks for a single aggregated scalar.
- Reply as JSON in this exact format: {{"sql": "your query here"}}

{SCHEMA}
"""

def get_openai_client(api_key: str | None = None) -> OpenAI:
    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError("OPENAI_API_KEY not found in environment or arguments.")
    return OpenAI(api_key=key)

def get_connection():
    user = os.getenv("SNOWFLAKE_USER") or os.getenv("SNOWFLAKE_USERNAME")
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=user,
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "ZOMATO_WH"),
        database=os.getenv("SNOWFLAKE_DATABASE", "ZOMATO"),
        schema="MARTS",
        role=os.getenv("SNOWFLAKE_ROLE", "DBT_ROLE"),
        client_session_keep_alive=True,
    )

def generate_sql(question: str, client: OpenAI | None = None) -> str:
    if client is None:
        client = get_openai_client()
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

def is_safe(sql: str) -> bool:
    lowered = sql.lower()
    if not (lowered.startswith("select") or lowered.startswith("with")):
        return False
    for word in FORBIDDEN_WORDS:
        if f" {word} " in f" {lowered} ":
            return False
    return True

def run_query(sql: str, conn=None, max_retries: int = 2):
    last_err = None
    for attempt in range(max_retries):
        close_conn = False
        active_conn = conn
        if active_conn is None or getattr(active_conn, "is_closed", lambda: False)():
            active_conn = get_connection()
            close_conn = True
        try:
            cursor = active_conn.cursor()
            cursor.execute("USE SCHEMA ZOMATO.MARTS")
            return cursor.execute(sql).fetch_pandas_all()
        except Exception as e:
            last_err = e
            err_str = str(e).lower()
            if any(term in err_str for term in ["390114", "token has expired", "08001", "session does not exist", "closed", "connection"]):
                conn = None
                continue
            raise e
        finally:
            if close_conn and active_conn:
                try:
                    active_conn.close()
                except Exception:
                    pass
    raise last_err

def render_ui():
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
                sql = generate_sql(question, client=client)
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

if __name__ == "__main__":
    render_ui()
