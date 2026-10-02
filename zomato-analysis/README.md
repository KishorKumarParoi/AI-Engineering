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
|-- Makefile                    # Developer ergonomics CLI (make test, make de, make check, etc.)
|-- run.sh                      # Master scripts checker and unified command dispatcher
|-- test_conn.py                # Master test runner (aggregates testing/ suites into executive scorecard)
|-- test_con.py                 # Compatibility wrapper delegating to test_conn.py
|-- main.py                     # Executive CLI entrypoint (python main.py info, test, pipeline)
|-- Dockerfile                  # Astronomer Airflow container with isolated dbt venv
|-- airflow_settings.yaml       # Automated Airflow connections (snowflake_default) and variables
|-- requirements.txt            # Python dependencies for Airflow runtime
|-- packages.txt                # System packages for container (git, build tools)
|-- pyproject.toml              # Local uv package specification
|-- scripts/                    # Production automation scripts
|   |-- data_engineering.sh     # dbt Medallion orchestrator (debug, snapshot, core, ai marts)
|   |-- ai_pipeline.sh          # LLM enrichment, embeddings generation & vector caching
|   |-- orchestration.sh        # Astronomer Airflow lifecycle controller (start, stop, trigger)
|   |-- serve_apps.sh           # Streamlit application server launcher
|   `-- setup_env.sh            # Environment doctor and dependency bootstrapper
|-- testing/                    # Modular verification test suites
|   |-- __init__.py             # Test package definition
|   |-- test_data_engineering_part.py # Comprehensive Snowflake Medallion, S3, and SCD2 checks
|   |-- test_ai_layer.py        # OpenAI embeddings, RAG semantic search, and SQL guardrail tests
|   `-- test_orchestration.py   # Airflow DAG AST syntax, task graph, and container health tests
|-- dags/
|   `-- zomato_batch.py         # Master Airflow orchestration DAG
|-- zomato/                     # dbt Medallion Transformations Project
|   |-- dbt_project.yml         # dbt project configuration with Medallion schema mappings
|   |-- profiles.yml            # Snowflake connection profile reading environment variables
|   |-- macros/
|   |   `-- generate_schema_name.sql # Custom schema generator for exact Medallion schemas
|   |-- models/
|   |   |-- staging/            # Silver layer views + schema documentation + tests
|   |   `-- marts/              # Gold layer dimensions, facts, and business marts
|   `-- snapshots/
|       `-- snap_restaurants.sql# SCD Type 2 dimension snapshot
|-- ai/
|   |-- enrich_reviews.py       # OpenAI batch LLM review classification
|   |-- rag_chat.py             # Streamlit RAG interface for semantic review search
|   |-- text_to_sql.py          # Streamlit natural language query interface for Snowflake
|   `-- example.env             # Template for AI credentials
|-- snowflake/                  # DDL scripts for manual or bootstrap setup
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

## 5. Developer Workflow & CLI Commands

### A. One-Click Scripts Checking (`./run.sh check` or `make check`)
Validates that all automation scripts in `scripts/` exist, have executable permissions (`chmod +x`), and pass bash syntax validation:
```bash
./run.sh check
# or
make check
```

### B. Master Test Runner (`./test_conn.py` or `make test`)
Discovers, executes, and displays an aggregated Senior Staff / Lead Engineer verification scorecard across all modules:
```bash
./test_conn.py
# or
make test
```
*Run individual suites:*
```bash
./test_conn.py --suite de     # Snowflake Medallion, S3 stage, 35M+ rows, SCD2
./test_conn.py --suite ai     # OpenAI embeddings, RAG search, Text-to-SQL
./test_conn.py --suite orch   # Airflow DAG AST, task graphs, container status
```

### C. Data Engineering Pipeline (`./scripts/data_engineering.sh` or `make de`)
Executes the Medallion transformation pipeline:
```bash
make de
# Subcommands:
make de-debug       # Test Snowflake connectivity
make de-snapshot    # Run SCD Type 2 dimension snapshots
make de-core        # Build Silver views & Gold dimensions/facts
make de-ai          # Build Gold AI marts
```

### D. AI & LLM Services (`./scripts/ai_pipeline.sh` or `make ai`)
Enriches customer reviews using `gpt-4o-mini` and builds 1536-dimensional vector search embeddings:
```bash
make ai
# or individual steps:
make ai-enrich
make ai-embed
```

### E. Interactive Streamlit Applications (`make sql` & `make rag`)
Launch the interactive web user interfaces:
```bash
make sql    # Text-to-SQL Assistant on http://localhost:8501
make rag    # Semantic Reviews RAG Chat on http://localhost:8502
```

---

## 6. How to Run End-to-End

### Step 1: Environment Verification
```bash
./run.sh check
make doctor
```

### Step 2: Run Full Test Verification Matrix
```bash
./test_conn.py
```

### Step 3: Run Full Data Engineering Medallion Build
```bash
make de
```

### Step 4: Run Airflow Orchestration
```bash
make astro-start
make astro-trigger
```

---

## 7. Test Results & Validation Status

- **Test Matrix**: 100% PASS across Data Engineering, AI Layer, and Airflow Orchestration.
- **dbt Suite**: 47 models, snapshots, and tests passing.
- **Data Volume**: 35,098,217 rows in Bronze, 35M+ in Silver, and Gold analytical marts fully populated.
- **SCD Type 2**: `ZOMATO.SNAPSHOTS.SNAP_RESTAURANTS` active with 148,541 versioned dimension records.
- **Vector Search**: 1536-dimensional embeddings cached and validated for sub-second semantic retrieval.

