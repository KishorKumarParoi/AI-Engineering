# Zomato AI Data Engineering -- End-to-End Enterprise Lakehouse & AI Platform

A production-grade batch data engineering and AI analytics platform processing food delivery datasets at scale:

**Zomato Dataset -> Amazon S3 -> Snowflake (Medallion: Bronze/Silver/Gold/SCD2) -> dbt -> Apache Airflow (Astronomer) -> OpenAI LLM -> Streamlit AI Apps**

---

## 1. System Architecture

```text
+-----------------------------------------------------------------------------------------------+
|                                      ARCHITECTURE OVERVIEW                                    |
+-----------------------------------------------------------------------------------------------+
|                                                                                               |
|  [ S3 Data Lake ]                                                                             |
|      s3://zomato-dataset-kkp/raw-data/ (*.csv: ~2.3 GB, 35M+ rows)                             |
|                           |                                                                   |
|                           v  (Storage Integration + External Stage: keyless IAM handshake)   |
|  [ Snowflake BRONZE / RAW ]                                                                   |
|      FOOD (371K) | MENU (1.17M) | USERS (100K) | RESTAURANTS (148K)                           |
|      ORDERS (10M) | ORDER_ITEMS (23M) | REVIEWS (300K)                                        |
|                           |                                                                   |
|                           v  (dbt Transformations: Type casting, cleanup, conform)           |
|  [ Snowflake SILVER / STAGING ]                                                               |
|      stg_food, stg_menu, stg_users, stg_restaurants, stg_orders, stg_order_items, stg_reviews |
|                           |                                                                   |
|                           +---------------------------------------+                           |
|                           |                                       |                           |
|                           v                                       v                           |
|  [ Snowflake GOLD / MARTS ]                                [ Snowflake SNAPSHOTS ]            |
|      - Dimensions: dim_restaurants, dim_customers,            - snap_restaurants (SCD2)       |
|                    dim_food, dim_date                                                         |
|      - Incremental Facts: fct_orders, fct_order_items                                         |
|      - Analytical Marts: mart_daily_city_revenue,                                             |
|                          mart_restaurant_performance,                                         |
|                          mart_delivery_sla                                                    |
|                           |                                                                   |
|                           v                                                                   |
|  [ OpenAI LLM Enrichment (gpt-4o-mini) ]                                                      |
|      ai/enrich_reviews.py -> Sentiment Label, Sentiment Score, Topic, Key Issue              |
|                           |                                                                   |
|                           v                                                                   |
|  [ Snowflake AI Layer ]                                                                       |
|      - ZOMATO.AI.REVIEW_ENRICHED                                                              |
|      - ZOMATO.MARTS.MART_REVIEW_INSIGHTS (dbt AI mart)                                        |
|                           |                                                                   |
|                           v                                                                   |
|  [ Interactive Applications (Streamlit) ]                                                     |
|      1. Semantic RAG Review Chat (ai/rag_chat.py)                                             |
|      2. Natural Language Text-to-SQL Analytics (ai/text_to_sql.py)                            |
|                                                                                               |
+-----------------------------------------------------------------------------------------------+
```

---

## 2. Medallion Layer Specifications

| Layer | Snowflake Schema | Type | Description | Row Count |
|---|---|---|---|---|
| **Bronze** | `ZOMATO.RAW` | Tables | Raw ingested CSV data via `COPY INTO` from S3 external stage | ~35,100,000 |
| **Silver** | `ZOMATO.STAGING` | Views | Cleansed, trimmed, type-cast, conformed standard views | ~35,100,000 |
| **Gold Dims** | `ZOMATO.MARTS` | Tables | Conformed dimension entities (`dim_restaurants`, `dim_customers`, `dim_food`, `dim_date`) | ~620,000 |
| **Gold Facts**| `ZOMATO.MARTS` | Incremental | High-volume fact tables with MERGE deduplication strategy (`fct_orders`, `fct_order_items`) | ~33,000,000 |
| **Gold Marts**| `ZOMATO.MARTS` | Tables | Pre-aggregated business marts (`mart_daily_city_revenue`, `mart_restaurant_performance`, `mart_delivery_sla`) | ~588,000 |
| **SCD Type 2**| `ZOMATO.SNAPSHOTS` | Snapshot | Track dimension attribute changes over time (`snap_restaurants`) with valid time windows | 148,541 |
| **AI Layer**  | `ZOMATO.AI` | Table | LLM-enriched sentiments, scores, and topics (`REVIEW_ENRICHED`) | Configurable |
| **AI Marts**  | `ZOMATO.MARTS` | Table | Aggregated review and sentiment insights per restaurant and city (`mart_review_insights`) | Active |

---

## 3. Repository Structure

```text
zomato-analysis/
|-- Dockerfile                  # Astronomer Airflow container with isolated dbt venv
|-- airflow_settings.yaml       # Automated Airflow connections (snowflake_default) and variables
|-- requirements.txt            # Python dependencies for Airflow runtime
|-- packages.txt                # System packages for container (git, build tools)
|-- pyproject.toml              # Local uv package specification
|-- test_con.py                 # Automated Snowflake health check and population verifier
|-- dags/
|   `-- zomato_batch.py         # Master Airflow orchestration DAG
|-- zomato/                     # dbt Project
|   |-- dbt_project.yml         # dbt project configuration with Medallion schema mappings
|   |-- profiles.yml            # Snowflake connection profile reading environment variables
|   |-- macros/
|   |   `-- generate_schema_name.sql # Custom schema generator for exact Medallion schemas
|   |-- models/
|   |   |-- staging/            # Silver layer views + schema documentation + tests
|   |   |   |-- _sources.yml    # Bronze layer source contracts
|   |   |   |-- _staging.yml    # Staging tests and column descriptions
|   |   |   |-- stg_restaurants.sql
|   |   |   |-- stg_users.sql
|   |   |   |-- stg_food.sql
|   |   |   |-- stg_menu.sql
|   |   |   |-- stg_orders.sql
|   |   |   |-- stg_order_items.sql
|   |   |   `-- stg_reviews.sql
|   |   `-- marts/              # Gold layer dimensions, facts, and business marts
|   |       |-- _marts.yml      # Marts documentation and referential integrity tests
|   |       |-- dim_restaurants.sql
|   |       |-- dim_customers.sql
|   |       |-- dim_food.sql
|   |       |-- dim_date.sql
|   |       |-- fct_orders.sql
|   |       |-- fct_order_items.sql
|   |       |-- mart_daily_city_revenue.sql
|   |       |-- mart_restaurant_performance.sql
|   |       |-- mart_delivery_sla.sql
|   |       `-- mart_review_insights.sql
|   `-- snapshots/
|       `-- snap_restaurants.sql# SCD Type 2 dimension snapshot
|-- ai/
|   |-- enrich_reviews.py       # OpenAI batch LLM review classification
|   |-- rag_chat.py             # Streamlit RAG interface for semantic review search
|   |-- text_to_sql.py          # Streamlit natural language query interface for Snowflake
|   `-- example.env             # Template for AI credentials
|-- snowflake/                  # DDL scripts for manual or bootstrap setup
|   |-- 01_setup.sql            # Database, schemas, warehouse, roles, and privileges
|   |-- 02_storage_integration.sql # S3 Storage Integration setup
|   |-- 03_stage_and_formats.sql   # External Stage and CSV File Format definitions
|   |-- 04_raw_tables.sql       # Bronze RAW table definitions
|   `-- 05_copy_into.sql        # COPY INTO commands for manual hydration
|-- aws/iam/                    # IAM policies and trust policies for keyless integration
`-- docs/
    `-- architecture.png        # Architecture diagram asset
```

---

## 4. Orchestration Pipeline (Apache Airflow)

The master pipeline DAG `zomato_batch` runs on Astronomer Airflow and orchestrates all layers in exact dependency sequence:

```text
+----------------+      +-------------------+      +--------------------+      +------------------+
|   reload_raw   | ---> |   dbt_build_core  | ---> |   enrich_reviews   | ---> |   dbt_build_ai   |
+----------------+      +-------------------+      +--------------------+      +------------------+
  Snowflake COPY          Transform Silver/Gold      OpenAI gpt-4o-mini          Build AI Mart
  from S3 Stage           & Run Data Tests           Sentiment Enrichment        (mart_review_insights)
```

- **Isolated Execution**: `dbt-snowflake` runs in its own dedicated virtualenv at `/opt/airflow/dbt_venv` inside the container, eliminating dependency conflicts with Airflow packages.
- **Resilient Configuration**: `default_args` configured with `retries: 2` and multi-version compatibility across Airflow 2.x and Airflow 3.x runtime environments.
- **Zero-Secret Hardcoding**: Snowflake and OpenAI credentials are read dynamically from container environment variables and `airflow_settings.yaml`.

---

## 5. AI Applications

### A. Batch Review Enrichment (`ai/enrich_reviews.py`)
- Pulls unenriched customer reviews from `ZOMATO.RAW.REVIEWS`.
- Classifies sentiment (label and continuous score -1.0 to 1.0), assigns one of 6 core topics (`food quality`, `delivery`, `pricing`, `service`, `packaging`, `other`), and extracts key issues.
- Persists structured classifications to `ZOMATO.AI.REVIEW_ENRICHED`.

### B. Semantic RAG Chat (`ai/rag_chat.py`)
- Vector embeddings generated using `text-embedding-3-small` and cached in Parquet for low-latency retrieval.
- Computes cosine similarity across customer reviews and provides grounded, factual answers with citations.
- Run via:
  ```bash
  uv run streamlit run ai/rag_chat.py
  ```

### C. Text-to-SQL Analytics (`ai/text_to_sql.py`)
- Translates natural language questions (e.g. "Top 10 cities by GMV in 2024") into validated Snowflake SQL queries.
- Protected by a read-only safety guard enforcing `SELECT` / `WITH` statements and blocking mutating operations (`DROP`, `DELETE`, `UPDATE`, `ALTER`, etc.).
- Visualizes results automatically using Streamlit dataframes and charts.
- Run via:
  ```bash
  uv run streamlit run ai/text_to_sql.py
  ```

---

## 6. How to Run Locally

### Prerequisites
- Python 3.12+ (or `uv`)
- Docker Desktop
- Astro CLI (`brew install astro`)
- Snowflake account with warehouse `ZOMATO_WH` and database `ZOMATO`

### Step 1: Configure Environment
Copy `.env.example` to `.env` (or verify existing `.env`):
```bash
SNOWFLAKE_ACCOUNT="VVXMVZH-FL05366"
SNOWFLAKE_USERNAME="kkp007"
SNOWFLAKE_PASSWORD="your_password"
SNOWFLAKE_WAREHOUSE="ZOMATO_WH"
SNOWFLAKE_DATABASE="ZOMATO"
SNOWFLAKE_SCHEMA="RAW"
OPENAI_API_KEY="sk-..."
```

### Step 2: Verify Connection and Data Population
Run the health check tool:
```bash
uv run test_con.py
```

### Step 3: Run dbt Transformations
```bash
cd zomato
uv run dbt debug
uv run dbt snapshot
uv run dbt build
cd ..
```

### Step 4: Start Airflow Dev Environment
```bash
astro dev start
```
- Open Airflow UI: `http://localhost:8080` (or `http://zomato-analysis.localhost:6563`)
- Trigger the `zomato_batch` DAG to run the full end-to-end pipeline.

### Step 5: Launch AI Applications
```bash
# Chat with your reviews (RAG)
uv run streamlit run ai/rag_chat.py

# Chat with your warehouse (Text-to-SQL)
uv run streamlit run ai/text_to_sql.py
```

---

## 7. Test Results & Validation Status

- **dbt Suite**: 47 models, snapshots, and tests passing (100% pass rate).
- **DAG Integrity**: Astronomer test suite passed (`pytest tests/dags/test_dag_example.py`).
- **Data Volume**: 35,098,217 rows in Bronze, 35M+ in Silver, and Gold analytical marts fully populated.
- **SCD Type 2**: `ZOMATO.SNAPSHOTS.SNAP_RESTAURANTS` active with 148,541 versioned dimension records.
