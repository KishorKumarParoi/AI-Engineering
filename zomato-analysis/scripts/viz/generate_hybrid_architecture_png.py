#!/usr/bin/env python3
"""
Script: scripts/generate_hybrid_architecture_png.py
Purpose: Generate a pristine, high-resolution dark-mode architecture diagram PNG
         representing the complete end-to-end Hybrid Architecture:
         Kafka -> Databricks -> Snowflake -> Airflow -> dbt -> Next.js / Power BI.
Outputs:
  - zomato-analysis/docs/hybrid_architecture_blueprint.png
  - Artifact directory copy for markdown embedding
"""

import os
import shutil
from PIL import Image, ImageDraw, ImageFont

def get_font(size, bold=False):
    font_candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/SFPro.ttf"
    ]
    for p in font_candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()

def draw_card(draw, box, fill, outline, radius=14, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

def generate_diagram(output_path="docs/hybrid_architecture_blueprint.png"):
    w = 2600
    h = 1600

    # 1. Base Dark Solid Canvas (#080b11)
    base_bg = (8, 11, 17)
    img = Image.new("RGB", (w, h), base_bg)

    # 2. Ambient Lighting Glow Layer
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)

    # Amber Glow on Left (Kafka)
    for r in range(450, 0, -15):
        alpha = int(14 * (1 - r / 450))
        gdraw.ellipse([-r, 300 - r, r * 2, 300 + r * 2], fill=(245, 158, 11, alpha))

    # Crimson Glow (Databricks)
    for r in range(400, 0, -15):
        alpha = int(12 * (1 - r / 400))
        gdraw.ellipse([700 - r, 300 - r, 700 + r * 2, 300 + r * 2], fill=(239, 68, 68, alpha))

    # Sky Blue Glow (Snowflake)
    for r in range(450, 0, -15):
        alpha = int(14 * (1 - r / 450))
        gdraw.ellipse([1400 - r, 300 - r, 1400 + r * 2, 300 + r * 2], fill=(56, 189, 248, alpha))

    # Emerald Glow (Airflow & dbt)
    for r in range(400, 0, -15):
        alpha = int(12 * (1 - r / 400))
        gdraw.ellipse([2100 - r, 300 - r, 2100 + r * 2, 300 + r * 2], fill=(16, 185, 129, alpha))

    # Composite Glow
    img_rgba = img.convert("RGBA")
    img_rgba = Image.alpha_composite(img_rgba, glow)
    img = img_rgba.convert("RGB")
    draw = ImageDraw.Draw(img)

    # Fonts
    brand_font = get_font(18, bold=True)
    badge_font = get_font(14, bold=True)
    title_font = get_font(40, bold=True)
    sub_font = get_font(18, bold=False)
    col_title_font = get_font(21, bold=True)
    col_tag_font = get_font(12, bold=True)
    card_title_font = get_font(17, bold=True)
    body_font = get_font(15, bold=False)
    bullet_font = get_font(15, bold=True)
    footer_font = get_font(15, bold=False)

    # --- TOP HEADER ---
    draw.text((w // 2, 45), "ZOMATO ENTERPRISE HYBRID DATA & AI PLATFORM", fill=(244, 63, 94), font=brand_font, anchor="mm")

    badge_text = "PRINCIPAL ARCHITECT / SENIOR STAFF SYSTEM DESIGN BLUEPRINT"
    badge_w = 640
    badge_h = 32
    bx = (w - badge_w) // 2
    by = 70
    draw.rounded_rectangle([bx, by, bx + badge_w, by + badge_h], radius=16, fill=(22, 27, 34), outline=(56, 139, 253), width=1)
    draw.text((w // 2, by + 16), badge_text, fill=(88, 166, 255), font=badge_font, anchor="mm")

    draw.text((w // 2, by + 58), "END-TO-END HYBRID DATA FLOW & LAKEHOUSE ARCHITECTURE", fill=(255, 255, 255), font=title_font, anchor="mm")
    sub_title = "Kafka Live Streaming (50k evt/s) --> Databricks PySpark & MLflow --> Snowflake Medallion Lakehouse & OBT --> Next.js 16 + Power BI Telemetry"
    draw.text((w // 2, by + 94), sub_title, fill=(148, 163, 184), font=sub_font, anchor="mm")

    draw.line([80, by + 120, w - 80, by + 120], fill=(48, 54, 61), width=2)

    # --- 4 VERTICAL ARCHITECTURE COLUMNS ---
    start_y = by + 145
    col_w = 580
    gutter = 40
    left_margin = (w - (col_w * 4 + gutter * 3)) // 2

    columns_data = [
        {
            "idx": 0,
            "title": "1. INGESTION & EVENT STREAMING",
            "tag": "REAL-TIME & BATCH SOURCES",
            "accent": (245, 158, 11),  # Amber
            "cards": [
                {
                    "title": "Apache Kafka Event Broker (Port 9092)",
                    "bullets": [
                        "Topic: 'zomato.order_events' (50,000 evt/s)",
                        "Topic: 'zomato.rider_telemetry' (Live GPS lat/lng)",
                        "Confluent cp-kafka:7.5.0 Docker cluster",
                        "High-throughput Python async event producer",
                        "Partitioning: key-hash by order_id & city"
                    ]
                },
                {
                    "title": "AWS S3 Raw Landing Buckets",
                    "bullets": [
                        "s3://zomato-dataset-kkp/raw-data/ (Orders, Users)",
                        "7 Conformed source folders (CSV / JSON dumps)",
                        "Event-driven S3 -> SQS metadata notification",
                        "Immutable raw landing with checksum validation",
                        "Partition layout: year=YYYY/month=MM/day=DD"
                    ]
                },
                {
                    "title": "Go Microservices & Postgres CDC",
                    "bullets": [
                        "Order Service (Port 8081) & Catalog Service",
                        "Debezium CDC streaming Postgres WAL to Kafka",
                        "Transactional Outbox Pattern for zero data loss",
                        "Redis 7 Cache-Aside layer with TTL safeguards"
                    ]
                }
            ]
        },
        {
            "idx": 1,
            "title": "2. HEAVY COMPUTE & AI ENGINE",
            "tag": "DATABRICKS DELTA LAKEHOUSE",
            "accent": (239, 68, 68),  # Crimson Red
            "cards": [
                {
                    "title": "Databricks Auto Loader (cloudFiles)",
                    "bullets": [
                        "01_s3_autoloader_ingestion.py",
                        "Zero-list SQS directory notification",
                        "Auto schema evolution ('addNewColumns')",
                        "Rescued data column (_rescued_data safety net)",
                        "Writes directly to Delta Bronze tables"
                    ]
                },
                {
                    "title": "Spark Structured Streaming",
                    "bullets": [
                        "02_kafka_streaming_ingestion.py",
                        "Binary JSON payload deserialization to StructType",
                        "15-minute watermark for out-of-order phone syncs",
                        "Deduplication by [order_id, status, timestamp]",
                        "Trigger.AvailableNow for 80% cost reduction"
                    ]
                },
                {
                    "title": "PySpark Silver ETL & MLflow ETA Model",
                    "bullets": [
                        "03_silver_pyspark_etl.py: Haversine distance km",
                        "04_ml_delivery_eta_model.py: GBTRegressor",
                        "Scores predicted ETA with +/- 3.5 min error bands",
                        "05_export_to_snowflake_iceberg.py: UniForm Bridge",
                        "Partitioned Snappy Parquet export for Snowflake"
                    ]
                }
            ]
        },
        {
            "idx": 2,
            "title": "3. SERVING, WAREHOUSE & MARTS",
            "tag": "SNOWFLAKE ENTERPRISE SUITE",
            "accent": (56, 189, 248),  # Sky Blue
            "cards": [
                {
                    "title": "Bronze RAW & External Stages",
                    "bullets": [
                        "03_stage_and_formats.sql: ZOMATO_RAW_STAGE",
                        "05_copy_into.sql: Idempotent RAW table reloads",
                        "@ZOMATO.RAW.DATABRICKS_ML_STAGE for ML features",
                        "Role-Based Access Control (DBT_ROLE, ANALYST)",
                        "Zero-copy cloning for dev/staging environments"
                    ]
                },
                {
                    "title": "dbt Silver Staging & SCD Type 2",
                    "bullets": [
                        "snap_restaurants.sql & snap_users.sql (SCD Type 2)",
                        "Tracks restaurant & address mutations over time",
                        "valid_from, valid_to, is_current temporal audit",
                        "stg_orders, stg_food, stg_menu, stg_reviews",
                        "Automated schema tests (unique, not_null, fks)"
                    ]
                },
                {
                    "title": "Gold Marts, OBT & Hybrid Telemetry",
                    "bullets": [
                        "fct_orders (incremental fact) & dimensional stars",
                        "obt_orders.sql: 35M+ One Big Table denormalized",
                        "Zero-join serving for Text-to-SQL AI & BI tools",
                        "v_hybrid_order_telemetry: Snowflake + Databricks",
                        "Sub-50ms query serving via DirectQuery cache"
                    ]
                }
            ]
        },
        {
            "idx": 3,
            "title": "4. ORCHESTRATION & AGENTIC APPS",
            "tag": "AIRFLOW, AI & POWER BI UI",
            "accent": (16, 185, 129),  # Emerald Green
            "cards": [
                {
                    "title": "Astronomer Airflow Pipelines",
                    "bullets": [
                        "zomato_batch.py: Daily Medallion batch DAG",
                        "zomato_hybrid_pipeline.py: Multi-cloud DAG",
                        "TaskGroups: Ingest -> ML -> Snowflake -> Quality",
                        "Automated data contracts & reconciliation gates",
                        "Dynamic dbt virtualenv execution paths"
                    ]
                },
                {
                    "title": "Dual-Engine AI & Voice Assistants",
                    "bullets": [
                        "enrich_reviews.py: OpenAI sentiment & topics",
                        "rag_chat.py: Qdrant semantic vector search",
                        "text_to_sql.py: Natural language over obt_orders",
                        "AST SQL Guardrails (Read-Only SELECT enforcement)",
                        "Silero VAD + Faster-Whisper + Edge-TTS pipeline"
                    ]
                },
                {
                    "title": "Next.js 16 + Power BI Telemetry Suite",
                    "bullets": [
                        "React 19 Server Components & Glassmorphic UI",
                        "PowerBiDashboard.tsx: Executive telemetry",
                        "Live 50k Kafka Burst Simulator in browser",
                        "Multi-Market Slicers (Bangalore, Mumbai, Delhi)",
                        "Azure ADLS Gen2 Multi-Cloud Disaster Recovery"
                    ]
                }
            ]
        }
    ]

    # Render 4 Columns
    for col in columns_data:
        cx = left_margin + col["idx"] * (col_w + gutter)
        cy = start_y
        accent = col["accent"]
        r, g, b = accent

        # Column Header Container
        header_h = 70
        draw_card(draw, [cx, cy, cx + col_w, cy + header_h], (18, 24, 38), (r, g, b), radius=12, width=2)

        # Tag Pill
        draw.rounded_rectangle([cx + 16, cy + 12, cx + 220, cy + 32], radius=10, fill=(r // 6 + 12, g // 6 + 12, b // 6 + 12), outline=(r, g, b), width=1)
        draw.text((cx + 118, cy + 22), col["tag"], fill=(r, g, b), font=col_tag_font, anchor="mm")

        # Column Title
        draw.text((cx + 16, cy + 40), col["title"], fill=(255, 255, 255), font=col_title_font)

        # Render 3 Cards per Column
        card_start_y = cy + header_h + 18
        card_h = 240
        card_gutter = 18

        for card_idx, c_info in enumerate(col["cards"]):
            card_y = card_start_y + card_idx * (card_h + card_gutter)
            draw_card(draw, [cx, card_y, cx + col_w, card_y + card_h], (14, 18, 28), (48, 54, 61), radius=12, width=1)

            # Left accent highlight bar
            draw.rounded_rectangle([cx, card_y, cx + 4, card_y + card_h], radius=2, fill=(r, g, b))

            # Card Title
            draw.text((cx + 20, card_y + 18), c_info["title"], fill=(255, 255, 255), font=card_title_font)
            draw.line([cx + 20, card_y + 44, cx + col_w - 20, card_y + 44], fill=(30, 36, 46), width=1)

            # Bullets
            bullet_y = card_y + 58
            for b_idx, bullet in enumerate(c_info["bullets"]):
                by_pos = bullet_y + b_idx * 33
                draw.text((cx + 22, by_pos), "[+]", fill=(r, g, b), font=bullet_font)
                draw.text((cx + 52, by_pos), bullet, fill=(203, 213, 225), font=body_font)

    # --- BOTTOM SUMMARY FLOW RIBBON ---
    ribbon_y = start_y + 70 + 18 + 3 * (240 + 18) + 16
    ribbon_h = 100
    draw_card(draw, [left_margin, ribbon_y, left_margin + col_w * 4 + gutter * 3, ribbon_y + ribbon_h], (15, 23, 42), (99, 102, 241), radius=14, width=2)

    # Ribbon Pill
    draw.rounded_rectangle([left_margin + 20, ribbon_y + 14, left_margin + 240, ribbon_y + 36], radius=11, fill=(25, 30, 60), outline=(129, 140, 248), width=1)
    draw.text((left_margin + 130, ribbon_y + 25), "UNIFIED DATA PIPELINE FLOW", fill=(165, 180, 252), font=col_tag_font, anchor="mm")

    flow_text = "Kafka (50k evt/s) + S3 Landing  -->  Databricks Auto Loader & Structured Streaming  -->  Delta Lake Silver & MLflow ETA Regressor  -->  Snowflake Iceberg & OBT Marts  -->  Power BI (< 45ms DirectQuery)"
    draw.text((left_margin + 20, ribbon_y + 54), flow_text, fill=(255, 255, 255), font=get_font(18, bold=True))

    sla_text = "Guarantees: Zero Data Loss (Transactional Outbox)  |  SCD Type 2 History Audit  |  Sub-50ms Dashboard Latency  |  Multi-Cloud DR to Azure ADLS Gen2 ($0.99/TB)"
    draw.text((left_margin + 20, ribbon_y + 78), sla_text, fill=(148, 163, 184), font=body_font)

    # --- FOOTER ---
    footer_text = "Zomato Enterprise Hybrid Lakehouse Architecture Blueprint | Principal / Senior Staff Engineer Standard | Production Verified"
    draw.text((w // 2, h - 25), footer_text, fill=(100, 116, 139), font=footer_font, anchor="mm")

    # Save to project docs
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG")
    print(f"[✓] Pristine architecture diagram generated at: {output_path}")

    # Also copy directly to the Antigravity conversation artifact directory for embedding!
    artifact_dir = "/Users/kishorkumarparoi/.gemini/antigravity-ide/brain/b5ed5655-a13a-4222-bf0a-489a61ae0d39"
    artifact_path = os.path.join(artifact_dir, "hybrid_enterprise_architecture.png")
    shutil.copyfile(output_path, artifact_path)
    print(f"[✓] Copied to artifact directory: {artifact_path}")

if __name__ == "__main__":
    generate_diagram()
