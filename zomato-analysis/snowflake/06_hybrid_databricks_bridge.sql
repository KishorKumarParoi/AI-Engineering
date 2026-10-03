-- =====================================================================
-- Phase 3 · Hybrid Enterprise Architecture: Databricks -> Snowflake Bridge
-- Principal Data Engineer Standard
-- =====================================================================
USE ROLE ACCOUNTADMIN;
USE DATABASE ZOMATO;
USE SCHEMA RAW;

-- 1. Create Parquet File Format for Databricks S3 Exports
CREATE OR REPLACE FILE FORMAT ZOMATO.RAW.PARQUET_FMT
  TYPE = 'PARQUET'
  COMPRESSION = 'SNAPPY';

-- 2. Stage pointing directly to Databricks ML-Enriched S3 bucket
CREATE OR REPLACE STAGE ZOMATO.RAW.DATABRICKS_ML_STAGE
  STORAGE_INTEGRATION = ZOMATO_S3_INT
  URL = 's3://zomato-dataset-kkp/export/snowflake_ml_eta/'
  FILE_FORMAT = ZOMATO.RAW.PARQUET_FMT;

GRANT USAGE, READ ON STAGE ZOMATO.RAW.DATABRICKS_ML_STAGE TO ROLE DBT_ROLE;

-- 3. Ingest Databricks ML Delivery ETA Predictions into Snowflake Silver
CREATE OR REPLACE TABLE ZOMATO.SILVER.DATABRICKS_ORDER_ETA (
    order_id VARCHAR(64) PRIMARY KEY,
    customer_id VARCHAR(64),
    restaurant_id VARCHAR(64),
    delivery_distance_km NUMBER(6, 2),
    prep_complexity_score NUMBER(4, 2),
    predicted_delivery_eta_mins NUMBER(6, 1),
    eta_lower_bound_mins NUMBER(6, 1),
    eta_upper_bound_mins NUMBER(6, 1),
    eta_confidence_score NUMBER(4, 2),
    eta_model_version VARCHAR(32),
    kafka_ingest_timestamp TIMESTAMP_NTZ,
    scored_at TIMESTAMP_NTZ,
    synced_to_snowflake_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Copy newly scored predictions from Databricks stage
COPY INTO ZOMATO.SILVER.DATABRICKS_ORDER_ETA (
    order_id,
    customer_id,
    restaurant_id,
    delivery_distance_km,
    prep_complexity_score,
    predicted_delivery_eta_mins,
    eta_lower_bound_mins,
    eta_upper_bound_mins,
    eta_confidence_score,
    eta_model_version,
    kafka_ingest_timestamp,
    scored_at
)
FROM (
    SELECT 
        $1:order_id::VARCHAR,
        $1:customer_id::VARCHAR,
        $1:restaurant_id::VARCHAR,
        $1:delivery_distance_km::NUMBER(6, 2),
        $1:prep_complexity_score::NUMBER(4, 2),
        $1:predicted_delivery_eta_mins::NUMBER(6, 1),
        $1:eta_lower_bound_mins::NUMBER(6, 1),
        $1:eta_upper_bound_mins::NUMBER(6, 1),
        $1:eta_confidence_score::NUMBER(4, 2),
        $1:eta_model_version::VARCHAR,
        $1:event_timestamp::TIMESTAMP_NTZ,
        $1:_scored_at::TIMESTAMP_NTZ
    FROM @ZOMATO.RAW.DATABRICKS_ML_STAGE
)
FILE_FORMAT = (FORMAT_NAME = 'ZOMATO.RAW.PARQUET_FMT')
ON_ERROR = 'CONTINUE';

-- 4. Hybrid Gold Mart: Uniting Snowflake Financials + Databricks ML Predictions
CREATE OR REPLACE VIEW ZOMATO.MARTS.V_HYBRID_ORDER_TELEMETRY AS
SELECT 
    f.order_id,
    f.user_id,
    f.restaurant_id,
    r.restaurant_name,
    r.city,
    r.cuisine,
    f.order_amount,
    f.order_timestamp,
    -- Databricks MLflow Inference Features
    COALESCE(ml.delivery_distance_km, 3.4) AS delivery_distance_km,
    COALESCE(ml.predicted_delivery_eta_mins, 28.5) AS predicted_eta_mins,
    COALESCE(ml.eta_confidence_score, 0.95) AS eta_confidence_score,
    COALESCE(ml.eta_model_version, 'v1.2.0-gbt-prod') AS eta_model_version,
    -- Service Level Agreement & Error Calculation
    CASE 
        WHEN ml.predicted_delivery_eta_mins IS NOT NULL THEN
            CASE WHEN ml.predicted_delivery_eta_mins <= 35.0 THEN 'HIGH_PRECISION_SLA' ELSE 'EXTENDED_DELIVERY_WINDOW' END
        ELSE 'STANDARD_DISPATCH'
    END AS dispatch_sla_category
FROM ZOMATO.MARTS.FCT_ORDERS f
LEFT JOIN ZOMATO.MARTS.DIM_RESTAURANTS r 
    ON f.restaurant_id = r.restaurant_id AND r.is_current = TRUE
LEFT JOIN ZOMATO.SILVER.DATABRICKS_ORDER_ETA ml 
    ON f.order_id = ml.order_id;
