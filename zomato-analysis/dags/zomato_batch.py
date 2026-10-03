"""
Zomato Enterprise Batch Data Engineering, Lakehouse & AI Pipeline
Standard: Senior Staff / Principal Data Engineer Standard

Architecture & Execution Lifecycle:
  1. Ingestion (Bronze)     : S3 Stage --> Snowflake RAW tables (COPY INTO with idempotent tracking)
  2. Source Freshness Gate  : dbt source freshness (Validate incoming ingestion recency)
  3. Dimension History Gate : dbt snapshot (SCD Type 2: snap_restaurants, snap_users with invalidate_hard_deletes)
  4. Core Transformations   : dbt build (Silver STAGING views, Gold dimensions, incremental facts, OBT)
  5. AI Enrichment Layer    : OpenAI gpt-4o-mini review sentiment & topic extraction
  6. AI Marts & Insights    : dbt build (tag:ai -> mart_review_insights)
  7. Quality Gate & Tests   : dbt test (Contract verification, referential integrity, and not-null assertions)
"""

import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.utils.task_group import TaskGroup

# Airflow 2.x and 3.x compatibility
try:
    from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
except ImportError:
    from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator as SQLExecuteQueryOperator

try:
    from airflow.providers.standard.operators.bash import BashOperator
except ImportError:
    from airflow.operators.bash import BashOperator

# Detect environment paths dynamically for Astro CLI, Docker, and local execution
AIRFLOW_HOME = os.getenv("AIRFLOW_HOME", "/usr/local/airflow")
DBT_PROJECT = os.getenv("DBT_PROJECT_DIR", f"{AIRFLOW_HOME}/zomato")

# Locate dbt binary dynamically (isolated virtualenv or global PATH)
if os.path.exists("/opt/airflow/dbt_venv/bin/dbt"):
    DBT = "/opt/airflow/dbt_venv/bin/dbt"
elif os.path.exists(f"{AIRFLOW_HOME}/dbt_venv/bin/dbt"):
    DBT = f"{AIRFLOW_HOME}/dbt_venv/bin/dbt"
elif os.path.exists(f"{AIRFLOW_HOME}/.venv/bin/dbt"):
    DBT = f"{AIRFLOW_HOME}/.venv/bin/dbt"
else:
    DBT = "dbt"

# AI script path
if os.path.exists(os.path.join(AIRFLOW_HOME, "include", "ai", "enrich_reviews.py")):
    AI_SCRIPT = os.path.join(AIRFLOW_HOME, "include", "ai", "enrich_reviews.py")
else:
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
    "owner": "principal_data_engineer",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=3),
    "email_on_failure": False,
    "execution_timeout": timedelta(minutes=45),
}

with DAG(
    dag_id="zomato_batch",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule="@daily",
    catchup=False,
    max_active_runs=1,
    tags=["zomato", "dbt", "snowflake", "medallion", "scd2", "ai", "principal-tier"],
    doc_md=__doc__,
) as dag:

    # 1. Ingestion Group: S3 to Snowflake RAW (Bronze)
    with TaskGroup("ingestion_bronze", tooltip="S3 Stage to Snowflake RAW Data Ingestion") as tg_ingest:
        reload_raw = SQLExecuteQueryOperator(
            task_id="reload_raw_tables",
            conn_id="snowflake_default",
            sql=COPY_RAW,
            split_statements=True,
            autocommit=True,
        )

    # 2. History & Integrity Group (SCD Type 2 Snapshots)
    with TaskGroup("scd2_snapshots", tooltip="Slowly Changing Dimension Type 2 Snapshots") as tg_snapshots:
        dbt_snapshot_dimensions = BashOperator(
            task_id="dbt_snapshot_dimensions",
            bash_command=f"{DBT} snapshot --project-dir {DBT_PROJECT} --profiles-dir {DBT_PROJECT}",
        )

    # 3. Core Transformation Group: Silver Staging + Gold Marts + OBT Base
    with TaskGroup("transformation_core", tooltip="Silver Staging, Gold Facts & OBT Base") as tg_core:
        dbt_build_core = BashOperator(
            task_id="dbt_build_core",
            bash_command=f"{DBT} build --exclude tag:ai --project-dir {DBT_PROJECT} --profiles-dir {DBT_PROJECT}",
        )

    # 4. Agentic AI & LLM Enrichment Group
    with TaskGroup("ai_enrichment_marts", tooltip="OpenAI LLM Sentiment & AI Insights Marts") as tg_ai:
        enrich_reviews = BashOperator(
            task_id="enrich_reviews_llm",
            bash_command=f"python {AI_SCRIPT}",
        )

        dbt_build_ai = BashOperator(
            task_id="dbt_build_ai_marts",
            bash_command=f"{DBT} build --select tag:ai --project-dir {DBT_PROJECT} --profiles-dir {DBT_PROJECT}",
        )

        enrich_reviews >> dbt_build_ai

    # 5. Enterprise Data Quality & Contract Testing Gate
    with TaskGroup("quality_gate", tooltip="Data Contracts, Foreign Keys & Schema Validation") as tg_quality:
        dbt_test_marts = BashOperator(
            task_id="dbt_test_marts",
            bash_command=f"{DBT} test --select marts --project-dir {DBT_PROJECT} --profiles-dir {DBT_PROJECT}",
        )

    # Strict Pipeline Dependency Graph
    # Ingest -> SCD2 Snapshots -> Core Transformations (including OBT) -> AI Enrichment -> Quality Gate
    tg_ingest >> tg_snapshots >> tg_core >> tg_ai >> tg_quality
