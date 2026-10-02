"""
Zomato Batch Data Engineering & AI Pipeline
Architecture:
  Lakehouse (S3) --> Snowflake RAW (Bronze) --> dbt Core (Silver & Gold) --> OpenAI LLM (AI) --> dbt AI Marts
"""

import os
from datetime import datetime, timedelta
from airflow import DAG

# Airflow 2.x and 3.x compatibility
try:
    from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
except ImportError:
    from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator as SQLExecuteQueryOperator

try:
    from airflow.providers.standard.operators.bash import BashOperator
except ImportError:
    from airflow.operators.bash import BashOperator

# Detect environment paths dynamically for Astro CLI and Docker
AIRFLOW_HOME = os.getenv("AIRFLOW_HOME", "/usr/local/airflow")
DBT_PROJECT = os.getenv("DBT_PROJECT_DIR", f"{AIRFLOW_HOME}/zomato")

# Locate dbt binary (isolated venv or PATH)
if os.path.exists("/opt/airflow/dbt_venv/bin/dbt"):
    DBT = "/opt/airflow/dbt_venv/bin/dbt"
elif os.path.exists(f"{AIRFLOW_HOME}/dbt_venv/bin/dbt"):
    DBT = f"{AIRFLOW_HOME}/dbt_venv/bin/dbt"
else:
    DBT = "dbt"

AI_SCRIPT = os.path.join(AIRFLOW_HOME, "ai", "enrich_reviews.py")

COPY_RAW = [
    "USE WAREHOUSE ZOMATO_WH;",
    "USE DATABASE ZOMATO;",
    "USE SCHEMA RAW;",
    "COPY INTO ZOMATO.RAW.restaurants FROM @ZOMATO.RAW.ZOMATO_RAW_STAGE/restaurant.csv FILE_FORMAT = (FORMAT_NAME = 'ZOMATO.RAW.CSV_FMT') ON_ERROR = 'CONTINUE';",
    "COPY INTO ZOMATO.RAW.users       FROM @ZOMATO.RAW.ZOMATO_RAW_STAGE/users.csv       FILE_FORMAT = (FORMAT_NAME = 'ZOMATO.RAW.CSV_FMT') ON_ERROR = 'CONTINUE';",
    "COPY INTO ZOMATO.RAW.food        FROM @ZOMATO.RAW.ZOMATO_RAW_STAGE/food.csv        FILE_FORMAT = (FORMAT_NAME = 'ZOMATO.RAW.CSV_FMT') ON_ERROR = 'CONTINUE';",
    "COPY INTO ZOMATO.RAW.menu        FROM @ZOMATO.RAW.ZOMATO_RAW_STAGE/menu.csv        FILE_FORMAT = (FORMAT_NAME = 'ZOMATO.RAW.CSV_FMT') ON_ERROR = 'CONTINUE';",
    "COPY INTO ZOMATO.RAW.orders      FROM @ZOMATO.RAW.ZOMATO_RAW_STAGE/orders.csv      FILE_FORMAT = (FORMAT_NAME = 'ZOMATO.RAW.CSV_FMT') ON_ERROR = 'CONTINUE';",
    "COPY INTO ZOMATO.RAW.order_items FROM @ZOMATO.RAW.ZOMATO_RAW_STAGE/order_items.csv FILE_FORMAT = (FORMAT_NAME = 'ZOMATO.RAW.CSV_FMT') ON_ERROR = 'CONTINUE';",
    "COPY INTO ZOMATO.RAW.reviews     FROM @ZOMATO.RAW.ZOMATO_RAW_STAGE/reviews.csv     FILE_FORMAT = (FORMAT_NAME = 'ZOMATO.RAW.CSV_FMT') ON_ERROR = 'CONTINUE';",
]

default_args = {
    "owner": "data_engineering",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="zomato_batch",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["zomato", "dbt", "snowflake", "medallion", "ai"],
    doc_md=__doc__,
) as dag:

    # 1. Ingest Bronze layer from S3 external stage into Snowflake RAW
    reload_raw = SQLExecuteQueryOperator(
        task_id="reload_raw",
        conn_id="snowflake_default",
        sql=COPY_RAW,
        split_statements=True,
        autocommit=True,
    )

    # 2. Transform Bronze -> Silver (STAGING) and Gold (MARTS Core)
    dbt_build_core = BashOperator(
        task_id="dbt_build_core",
        bash_command=f"{DBT} build --exclude tag:ai --project-dir {DBT_PROJECT} --profiles-dir {DBT_PROJECT}",
    )

    # 3. LLM Enrichment task calling OpenAI gpt-4o-mini
    enrich_reviews = BashOperator(
        task_id="enrich_reviews",
        bash_command=f"python {AI_SCRIPT}",
    )

    # 4. Build AI Marts combining warehouse metrics with LLM sentiment & topics
    dbt_build_ai = BashOperator(
        task_id="dbt_build_ai",
        bash_command=f"{DBT} build --select tag:ai --project-dir {DBT_PROJECT} --profiles-dir {DBT_PROJECT}",
    )

    # Pipeline dependency graph: Ingest -> Transform Core -> Enrich AI -> Build AI Marts
    reload_raw >> dbt_build_core >> enrich_reviews >> dbt_build_ai
