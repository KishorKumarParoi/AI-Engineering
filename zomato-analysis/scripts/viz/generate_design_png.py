#!/usr/bin/env python3
"""
Script: scripts/generate_design_png.py
Purpose: Generate a comprehensive, high-resolution working flow architecture diagram PNG
         saved as design.png and docs/design.png.
"""

import os
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

def draw_card(draw, xy, fill, outline, radius=14, border_width=2):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=border_width)

def draw_step_badge(draw, cx, cy, text, bg_color, text_color=(255, 255, 255), r=15, font=None):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=bg_color, outline=(255, 255, 255), width=1)
    if font:
        draw.text((cx, cy), text, fill=text_color, font=font, anchor="mm")

def draw_arrow_label(draw, cx, cy, text1, text2, text_color, bg_color=(22, 27, 34), font1=None, font2=None):
    w1 = len(text1) * 9 + 20
    w2 = len(text2) * 8 + 20 if text2 else 0
    w = max(w1, w2)
    h = 36 if text2 else 24
    draw.rounded_rectangle([cx - w//2, cy - h//2, cx + w//2, cy + h//2], radius=8, fill=bg_color, outline=(48, 54, 61), width=1)
    if text2:
        draw.text((cx, cy - 8), text1, fill=text_color, font=font1, anchor="mm")
        draw.text((cx, cy + 9), text2, fill=(201, 209, 217), font=font2, anchor="mm")
    else:
        draw.text((cx, cy), text1, fill=text_color, font=font1, anchor="mm")

def generate_flow_diagram(output_paths=["design.png", "docs/design.png"]):
    width = 2600
    height = 1750

    base_bg = (11, 15, 23)
    img = Image.new("RGB", (width, height), base_bg)

    # Ambient Lighting
    glow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)

    for r in range(450, 0, -20):
        alpha = int(14 * (1 - r / 450))
        glow_draw.ellipse([width//4 - r, 300 - r, width//4 + r, 300 + r], fill=(56, 189, 248, alpha))
        glow_draw.ellipse([3*width//4 - r, 350 - r, 3*width//4 + r, 350 + r], fill=(244, 63, 94, alpha))
        glow_draw.ellipse([width//3 - r, 900 - r, width//3 + r, 900 + r], fill=(2, 132, 199, alpha))
        glow_draw.ellipse([2*width//3 - r, 900 - r, 2*width//3 + r, 900 + r], fill=(16, 185, 129, alpha))
        glow_draw.ellipse([width//2 - r, 1400 - r, width//2 + r, 1400 + r], fill=(168, 85, 247, alpha))

    img_rgba = img.convert("RGBA")
    img_rgba = Image.alpha_composite(img_rgba, glow_layer)
    img = img_rgba.convert("RGB")
    draw = ImageDraw.Draw(img)

    # Fonts
    brand_font = get_font(18, bold=True)
    badge_font = get_font(14, bold=True)
    step_font = get_font(13, bold=True)
    title_font = get_font(40, bold=True)
    block_title_font = get_font(21, bold=True)
    block_sub_font = get_font(13, bold=True)
    body_font = get_font(16, bold=False)
    bullet_font = get_font(16, bold=True)
    arrow_label_font = get_font(13, bold=True)
    arrow_sub_font = get_font(11, bold=False)
    footer_font = get_font(15, bold=False)

    # --- HEADER ---
    header_y = 48
    draw.text((width // 2, header_y), "ZOMATO HYPER-SCALE DISTRIBUTED PLATFORM", fill=(244, 63, 94), font=brand_font, anchor="mm")
    
    badge_text = "PRINCIPAL ARCHITECT: END-TO-END WORKING FLOW & EXECUTION LIFECYCLE"
    badge_w = 760
    badge_h = 34
    bx1 = (width - badge_w) // 2
    by1 = header_y + 22
    draw.rounded_rectangle([bx1, by1, bx1 + badge_w, by1 + badge_h], radius=17, fill=(22, 27, 34), outline=(56, 139, 253), width=1)
    draw.text((width // 2, by1 + 17), badge_text, fill=(88, 166, 255), font=badge_font, anchor="mm")

    main_title = "SYSTEM WORKING FLOW: EDGE TO LAKEHOUSE, MLOPS, AGENTS & MULTI-CLOUD"
    draw.text((width // 2, by1 + 72), main_title, fill=(255, 255, 255), font=title_font, anchor="mm")
    draw.line([120, by1 + 106, width - 120, by1 + 106], fill=(48, 54, 61), width=2)

    content_top = by1 + 130

    # =========================================================================
    # ROW 1 (TOP): 
    # [DOMAIN 1: CLIENTS & CLOUDFLARE EDGE] ---> [DOMAIN 2: GO TRANSACTIONAL CORE & SAGA OUTBOX]
    # =========================================================================
    r1_y = content_top
    r1_h = 430

    # Domain 1 (Left)
    d1_x1 = 80
    d1_w = 760
    d1_x2 = d1_x1 + d1_w
    d1_accent = (56, 189, 248) # Sky blue
    draw_card(draw, [d1_x1, r1_y, d1_x2, r1_y + r1_h], (20, 26, 36), d1_accent, radius=18)

    draw.rounded_rectangle([d1_x1 + 20, r1_y + 16, d1_x1 + 220, r1_y + 42], radius=13, fill=(18, 38, 54), outline=d1_accent, width=1)
    draw.text((d1_x1 + 120, r1_y + 29), "DOMAIN 1: CLIENT & EDGE", fill=d1_accent, font=block_sub_font, anchor="mm")
    draw_step_badge(draw, d1_x1 + d1_w - 30, r1_y + 29, "1", d1_accent, text_color=(0, 0, 0), font=step_font)

    draw.text((d1_x1 + 20, r1_y + 54), "Consumer Client Layer & Global Edge", fill=(255, 255, 255), font=block_title_font)

    # Box 1A: Next.js 16+ App Router
    draw_card(draw, [d1_x1 + 20, r1_y + 96, d1_x2 - 20, r1_y + 240], (26, 34, 48), (56, 189, 248, 120), radius=10, border_width=1)
    draw.text((d1_x1 + 36, r1_y + 112), "Next.js 16+ Consumer App (React 19 RSC)", fill=d1_accent, font=get_font(17, bold=True))
    d1_bullets_a = [
        "Server Actions with Instant Optimistic UI Mutation",
        "Idempotency Key Injection (UUID v4) on Checkout",
        "Live Order Timeline consuming Server-Sent Events (SSE)",
        "Embedded Dual-Engine AI Assistant Drawer (SQL + RAG)"
    ]
    for idx, b in enumerate(d1_bullets_a):
        draw.text((d1_x1 + 36, r1_y + 138 + idx*24), "[*]", fill=d1_accent, font=bullet_font)
        draw.text((d1_x1 + 60, r1_y + 138 + idx*24), b, fill=(201, 209, 217), font=body_font)

    # Box 1B: Cloudflare Global Anycast Edge
    draw_card(draw, [d1_x1 + 20, r1_y + 256, d1_x2 - 20, r1_y + 406], (26, 34, 48), (56, 189, 248, 120), radius=10, border_width=1)
    draw.text((d1_x1 + 36, r1_y + 272), "Cloudflare Anycast Global Edge Network", fill=d1_accent, font=get_font(17, bold=True))
    d1_bullets_b = [
        "Edge WAF: DDoS Mitigation, Rate Limiting & Bot Shield",
        "Dynamic Geo-DNS Routing: 90% Primary AWS, 10% GCP",
        "Sub-15ms Edge SSL Termination & Token Verification",
        "Anycast Latency Routing for Voice WebRTC Gateways"
    ]
    for idx, b in enumerate(d1_bullets_b):
        draw.text((d1_x1 + 36, r1_y + 298 + idx*24), "[*]", fill=d1_accent, font=bullet_font)
        draw.text((d1_x1 + 60, r1_y + 298 + idx*24), b, fill=(201, 209, 217), font=body_font)

    # Domain 2 (Right)
    d2_x1 = 1040
    d2_w = width - d2_x1 - 80
    d2_x2 = d2_x1 + d2_w
    d2_accent = (244, 63, 94) # Rose Red
    draw_card(draw, [d2_x1, r1_y, d2_x2, r1_y + r1_h], (28, 22, 28), d2_accent, radius=18)

    draw.rounded_rectangle([d2_x1 + 20, r1_y + 16, d2_x1 + 270, r1_y + 42], radius=13, fill=(50, 20, 30), outline=d2_accent, width=1)
    draw.text((d2_x1 + 145, r1_y + 29), "DOMAIN 2: DISTRIBUTED CORE (GO)", fill=d2_accent, font=block_sub_font, anchor="mm")
    draw_step_badge(draw, d2_x2 - 30, r1_y + 29, "2", d2_accent, text_color=(255, 255, 255), font=step_font)

    draw.text((d2_x1 + 20, r1_y + 54), "Go Order Service, Transactional Outbox & Saga Orchestrator", fill=(255, 255, 255), font=block_title_font)

    # CONNECTOR ARROW 1 -> 2
    c12_y = r1_y + 160
    draw.line([d1_x2, c12_y, d2_x1, c12_y], fill=(244, 63, 94), width=4)
    draw.polygon([(d2_x1, c12_y), (d2_x1 - 14, c12_y - 8), (d2_x1 - 14, c12_y + 8)], fill=(244, 63, 94))
    draw_arrow_label(draw, (d1_x2 + d2_x1) // 2, c12_y, "1. POST /orders", "(Idempotency-Key)", (244, 63, 94), font1=arrow_label_font, font2=arrow_sub_font)

    # Return SSE Arrow (2 -> 1)
    c21_y = r1_y + 240
    draw.line([d2_x1, c21_y, d1_x2, c21_y], fill=(56, 189, 248), width=3)
    draw.polygon([(d1_x2, c21_y), (d1_x2 + 14, c21_y - 7), (d1_x2 + 14, c21_y + 7)], fill=(56, 189, 248))
    draw_arrow_label(draw, (d1_x2 + d2_x1) // 2, c21_y, "5. Live SSE Stream", "Status: CONFIRMED", (56, 189, 248), font1=arrow_label_font, font2=arrow_sub_font)

    sub2_w = (d2_w - 60) // 3
    
    # 2A: Go Order Service + Outbox DB
    b2a_x1 = d2_x1 + 18
    draw_card(draw, [b2a_x1, r1_y + 96, b2a_x1 + sub2_w, r1_y + 406], (38, 26, 34), (244, 63, 94, 120), radius=10, border_width=1)
    draw.text((b2a_x1 + 16, r1_y + 112), "Order Service & ACID DB", fill=d2_accent, font=get_font(17, bold=True))
    d2a_bullets = [
        "Go 1.24+ Hexagonal Architecture",
        "Goroutine Worker Pool (:8081)",
        "2. BEGIN TX: Insert Order",
        "   + Insert Outbox Event Payload",
        "COMMIT TX (Zero Dual-Writes)",
        "202 Accepted returned in <10ms",
        "SSE Push Channel (:8081/stream)"
    ]
    for idx, b in enumerate(d2a_bullets):
        draw.text((b2a_x1 + 16, r1_y + 142 + idx*26), "[*]", fill=d2_accent, font=bullet_font)
        draw.text((b2a_x1 + 40, r1_y + 142 + idx*26), b, fill=(201, 209, 217), font=body_font)

    # 2B: Debezium CDC Connector
    b2b_x1 = b2a_x1 + sub2_w + 12
    draw_card(draw, [b2b_x1, r1_y + 96, b2b_x1 + sub2_w, r1_y + 406], (38, 26, 34), (244, 63, 94, 120), radius=10, border_width=1)
    draw.text((b2b_x1 + 16, r1_y + 112), "Debezium CDC Engine", fill=d2_accent, font=get_font(17, bold=True))
    d2b_bullets = [
        "3. Streams Postgres WAL Log",
        "Extracts Outbox Mutations",
        "Guarantees In-Order Delivery",
        "Zero Overhead on Order API",
        "Publishes: order.created",
        "Kafka Topic Partitioning by",
        "Order ID (Deterministic Key)"
    ]
    for idx, b in enumerate(d2b_bullets):
        draw.text((b2b_x1 + 16, r1_y + 142 + idx*26), "[*]", fill=d2_accent, font=bullet_font)
        draw.text((b2b_x1 + 40, r1_y + 142 + idx*26), b, fill=(201, 209, 217), font=body_font)

    # 2C: Kafka Event Mesh & Distributed Saga
    b2c_x1 = b2b_x1 + sub2_w + 12
    draw_card(draw, [b2c_x1, r1_y + 96, b2c_x1 + sub2_w, r1_y + 406], (38, 26, 34), (244, 63, 94, 120), radius=10, border_width=1)
    draw.text((b2c_x1 + 16, r1_y + 112), "Kafka Mesh & Saga Svc", fill=d2_accent, font=get_font(17, bold=True))
    d2c_bullets = [
        "4. Parallel Saga Verification:",
        "   - Payment Svc (Card / UPI)",
        "   - Delivery Svc (Rider Hold)",
        "Kafka MSK Multi-AZ Cluster",
        "Auto-Compensating Rollback:",
        "   CancelOrder on payment fail",
        "Status: CONFIRMED Event"
    ]
    for idx, b in enumerate(d2c_bullets):
        draw.text((b2c_x1 + 16, r1_y + 142 + idx*26), "[*]", fill=d2_accent, font=bullet_font)
        draw.text((b2c_x1 + 40, r1_y + 142 + idx*26), b, fill=(201, 209, 217), font=body_font)


    # =========================================================================
    # ROW 2 (MIDDLE):
    # [DOMAIN 3: MEDALLION LAKEHOUSE & AIRFLOW] <---> [DOMAIN 4: MLOPS & ETA SERVING]
    # =========================================================================
    r2_y = r1_y + r1_h + 54
    r2_h = 440

    # Vertical Connector down from Kafka (Domain 2) to S3 Lakehouse (Domain 3)
    c23_x = 1140
    c23_y1 = r1_y + r1_h
    c23_y2 = r2_y
    draw.line([c23_x, c23_y1, c23_x, c23_y2], fill=(2, 132, 199), width=4)
    draw.polygon([(c23_x, c23_y2), (c23_x - 8, c23_y2 - 14), (c23_x + 8, c23_y2 - 14)], fill=(2, 132, 199))
    draw_arrow_label(draw, c23_x + 140, (c23_y1 + c23_y2) // 2, "6. S3 Ingestion Sink", "2.3 GB Raw Streaming", (2, 132, 199), font1=arrow_label_font, font2=arrow_sub_font)

    # Domain 3 (Left)
    d3_x1 = 80
    d3_w = 1260
    d3_x2 = d3_x1 + d3_w
    d3_accent = (2, 132, 199) # Snowflake Cyan/Blue
    draw_card(draw, [d3_x1, r2_y, d3_x2, r2_y + r2_h], (18, 28, 38), d3_accent, radius=18)

    draw.rounded_rectangle([d3_x1 + 20, r2_y + 16, d3_x1 + 270, r2_y + 42], radius=13, fill=(14, 38, 56), outline=d3_accent, width=1)
    draw.text((d3_x1 + 145, r2_y + 29), "DOMAIN 3: LAKEHOUSE ANALYTICS", fill=d3_accent, font=block_sub_font, anchor="mm")
    draw_step_badge(draw, d3_x2 - 30, r2_y + 29, "3", d3_accent, text_color=(255, 255, 255), font=step_font)

    draw.text((d3_x1 + 20, r2_y + 54), "Snowflake Medallion Architecture & Astronomer Airflow DAGs", fill=(255, 255, 255), font=block_title_font)

    sub3_w = (d3_w - 60) // 3
    
    # 3A: Bronze Layer
    b3a_x1 = d3_x1 + 18
    draw_card(draw, [b3a_x1, r2_y + 96, b3a_x1 + sub3_w, r2_y + 416], (24, 36, 48), (2, 132, 199, 120), radius=10, border_width=1)
    draw.text((b3a_x1 + 16, r2_y + 112), "Bronze Layer (RAW)", fill=d3_accent, font=get_font(17, bold=True))
    d3a_bullets = [
        "35,098,217 Total Raw Records",
        "S3 IAM Role Delegation Stage",
        "RAW_ORDERS (2.1M rows)",
        "RAW_ORDER_ITEMS (4.2M)",
        "RAW_USERS & RESTAURANTS",
        "RAW_REVIEWS & FOOD/MENU",
        "Append-Only Immutability"
    ]
    for idx, b in enumerate(d3a_bullets):
        draw.text((b3a_x1 + 16, r2_y + 146 + idx*26), "[*]", fill=d3_accent, font=bullet_font)
        draw.text((b3a_x1 + 40, r2_y + 146 + idx*26), b, fill=(201, 209, 217), font=body_font)

    # 3B: Silver Layer
    b3b_x1 = b3a_x1 + sub3_w + 12
    draw_card(draw, [b3b_x1, r2_y + 96, b3b_x1 + sub3_w, r2_y + 416], (24, 36, 48), (2, 132, 199, 120), radius=10, border_width=1)
    draw.text((b3b_x1 + 16, r2_y + 112), "Silver Layer (STAGING)", fill=d3_accent, font=get_font(17, bold=True))
    d3b_bullets = [
        "7 Conformed Clean Views",
        "7. dbt Core Transformation",
        "Data Quality Contract Checks",
        "Null Coalesce & Canonical Casing",
        "UTC Timestamp Normalization",
        "Type Casting & Schema Locks",
        "STG_ORDERS & STG_REVIEWS"
    ]
    for idx, b in enumerate(d3b_bullets):
        draw.text((b3b_x1 + 16, r2_y + 146 + idx*26), "[*]", fill=d3_accent, font=bullet_font)
        draw.text((b3b_x1 + 40, r2_y + 146 + idx*26), b, fill=(201, 209, 217), font=body_font)

    # 3C: Gold & SCD2 Layer
    b3c_x1 = b3b_x1 + sub3_w + 12
    draw_card(draw, [b3c_x1, r2_y + 96, b3c_x1 + sub3_w, r2_y + 416], (24, 36, 48), (2, 132, 199, 120), radius=10, border_width=1)
    draw.text((b3c_x1 + 16, r2_y + 112), "Gold Marts & Snapshots", fill=d3_accent, font=get_font(17, bold=True))
    d3c_bullets = [
        "Dimensions: CUSTOMER, FOOD",
        "FCT_ORDERS (Incremental MERGE)",
        "MART_DELIVERY_SLA Metrics",
        "MART_DAILY_CITY_REVENUE",
        "SNAP_RESTAURANTS (SCD2)",
        "Historical Time-Travel Tracking",
        "ZOMATO.AI 1536-dim Vectors"
    ]
    for idx, b in enumerate(d3c_bullets):
        draw.text((b3c_x1 + 16, r2_y + 146 + idx*26), "[*]", fill=d3_accent, font=bullet_font)
        draw.text((b3c_x1 + 40, r2_y + 146 + idx*26), b, fill=(201, 209, 217), font=body_font)

    # Domain 4 (Right)
    d4_x1 = 1460
    d4_w = width - d4_x1 - 80
    d4_x2 = d4_x1 + d4_w
    d4_accent = (16, 185, 129) # Emerald Green
    draw_card(draw, [d4_x1, r2_y, d4_x2, r2_y + r2_h], (18, 30, 24), d4_accent, radius=18)

    draw.rounded_rectangle([d4_x1 + 20, r2_y + 16, d4_x1 + 280, r2_y + 42], radius=13, fill=(14, 46, 30), outline=d4_accent, width=1)
    draw.text((d4_x1 + 150, r2_y + 29), "DOMAIN 4: MLOPS & GPU INFRA", fill=d4_accent, font=block_sub_font, anchor="mm")
    draw_step_badge(draw, d4_x2 - 30, r2_y + 29, "4", d4_accent, text_color=(0, 0, 0), font=step_font)

    draw.text((d4_x1 + 20, r2_y + 54), "Kubeflow ETA SLA Pipeline & LLMOps Gateway", fill=(255, 255, 255), font=block_title_font)

    # CONNECTOR 3 -> 4
    c34_y = r2_y + 200
    draw.line([d3_x2, c34_y, d4_x1, c34_y], fill=(16, 185, 129), width=4)
    draw.polygon([(d4_x1, c34_y), (d4_x1 - 14, c34_y - 8), (d4_x1 - 14, c34_y + 8)], fill=(16, 185, 129))
    draw_arrow_label(draw, (d3_x2 + d4_x1) // 2, c34_y, "8. Feature Store Sync", "Facts -> ML Pipeline", (16, 185, 129), font1=arrow_label_font, font2=arrow_sub_font)

    sub4_w = (d4_w - 40) // 2
    
    # 4A: Kubeflow Delivery ETA Pipeline
    b4a_x1 = d4_x1 + 16
    draw_card(draw, [b4a_x1, r2_y + 96, b4a_x1 + sub4_w, r2_y + 416], (24, 40, 32), (16, 185, 129, 120), radius=10, border_width=1)
    draw.text((b4a_x1 + 16, r2_y + 112), "Kubeflow Delivery ETA Pipeline", fill=d4_accent, font=get_font(17, bold=True))
    d4a_bullets = [
        "Feature Store: Prep time + Distance",
        "Weather score + Rider density",
        "XGBoost / LightGBM Regressor",
        "MLflow Registry & Experiment Runs",
        "Automated Model Validation Gate",
        "p95 SLA Breach Probability < 2%",
        "Low-Latency gRPC Serving Endpoint"
    ]
    for idx, b in enumerate(d4a_bullets):
        draw.text((b4a_x1 + 16, r2_y + 146 + idx*26), "[*]", fill=d4_accent, font=bullet_font)
        draw.text((b4a_x1 + 40, r2_y + 146 + idx*26), b, fill=(201, 209, 217), font=body_font)

    # 4B: LLMOps Gateway & GPU Serving
    b4b_x1 = b4a_x1 + sub4_w + 10
    draw_card(draw, [b4b_x1, r2_y + 96, b4b_x1 + sub4_w, r2_y + 416], (24, 40, 32), (16, 185, 129, 120), radius=10, border_width=1)
    draw.text((b4b_x1 + 16, r2_y + 112), "TensorZero & GPU Gateway", fill=d4_accent, font=get_font(17, bold=True))
    d4b_bullets = [
        "TensorZero / LiteLLM Proxy",
        "Dynamic Multi-Cloud Fallback:",
        "  OpenAI -> Azure AI -> vLLM",
        "Redis Semantic Prompt Cache",
        "Kubernetes GPU Serving Cluster",
        "vLLM Tensor Parallelism (A10G/T4)",
        "OpenTelemetry Latency & Cost Span"
    ]
    for idx, b in enumerate(d4b_bullets):
        draw.text((b4b_x1 + 16, r2_y + 146 + idx*26), "[*]", fill=d4_accent, font=bullet_font)
        draw.text((b4b_x1 + 40, r2_y + 146 + idx*26), b, fill=(201, 209, 217), font=body_font)


    # =========================================================================
    # ROW 3 (BOTTOM):
    # [DOMAIN 5: AGENTIC AI & REAL-TIME VOICE] <---> [DOMAIN 6: MULTI-CLOUD DEVOPS & GITOPS]
    # =========================================================================
    r3_y = r2_y + r2_h + 54
    r3_h = 440

    # Vertical Connector down from Lakehouse to Agentic AI (Domain 5)
    c35_x = 360
    c35_y1 = r2_y + r2_h
    c35_y2 = r3_y
    draw.line([c35_x, c35_y1, c35_x, c35_y2], fill=(168, 85, 247), width=4)
    draw.polygon([(c35_x, c35_y2), (c35_x - 8, c35_y2 - 14), (c35_x + 8, c35_y2 - 14)], fill=(168, 85, 247))
    draw_arrow_label(draw, c35_x + 130, (c35_y1 + c35_y2) // 2, "9. Query Gold Marts", "AST Read-Only Guardrails", (168, 85, 247), font1=arrow_label_font, font2=arrow_sub_font)

    # Domain 5 (Left)
    d5_x1 = 80
    d5_w = 1420
    d5_x2 = d5_x1 + d5_w
    d5_accent = (168, 85, 247) # Purple / Violet
    draw_card(draw, [d5_x1, r3_y, d5_x2, r3_y + r3_h], (26, 20, 36), d5_accent, radius=18)

    draw.rounded_rectangle([d5_x1 + 20, r3_y + 16, d5_x1 + 280, r3_y + 42], radius=13, fill=(46, 24, 66), outline=d5_accent, width=1)
    draw.text((d5_x1 + 150, r3_y + 29), "DOMAIN 5: AGENTIC AI & VOICE", fill=d5_accent, font=block_sub_font, anchor="mm")
    draw_step_badge(draw, d5_x2 - 30, r3_y + 29, "5", d5_accent, text_color=(255, 255, 255), font=step_font)

    draw.text((d5_x1 + 20, r3_y + 54), "LangGraph Cyclic State Machine, Voice Pipeline & MCP", fill=(255, 255, 255), font=block_title_font)

    sub5_w = (d5_w - 60) // 3

    # 5A: LangGraph Cyclic State Machine
    b5a_x1 = d5_x1 + 18
    draw_card(draw, [b5a_x1, r3_y + 96, b5a_x1 + sub5_w, r3_y + 416], (36, 26, 48), (168, 85, 247, 120), radius=10, border_width=1)
    draw.text((b5a_x1 + 16, r3_y + 112), "LangGraph Cyclic Graph", fill=d5_accent, font=get_font(17, bold=True))
    d5a_bullets = [
        "10. Intent Classifier Router",
        "AST Guardrail: SELECT/WITH only",
        "Snowflake Execution Engine",
        "Result Evaluator & Quality Check",
        "Self-Reflection Node (< 3 loops)",
        "Auto-Correction Query Repair",
        "Human-In-The-Loop Escalation"
    ]
    for idx, b in enumerate(d5a_bullets):
        draw.text((b5a_x1 + 16, r3_y + 146 + idx*26), "[*]", fill=d5_accent, font=bullet_font)
        draw.text((b5a_x1 + 40, r3_y + 146 + idx*26), b, fill=(201, 209, 217), font=body_font)

    # 5B: Full-Duplex Real-Time Voice Engine
    b5b_x1 = b5a_x1 + sub5_w + 12
    draw_card(draw, [b5b_x1, r3_y + 96, b5b_x1 + sub5_w, r3_y + 416], (36, 26, 48), (168, 85, 247, 120), radius=10, border_width=1)
    draw.text((b5b_x1 + 16, r3_y + 112), "Full-Duplex Voice Engine", fill=d5_accent, font=get_font(17, bold=True))
    d5b_bullets = [
        "WebRTC Audio Stream Gateway",
        "Local Silero VAD (< 15ms latency)",
        "Faster-Whisper Streaming STT",
        "Streaming LLM Reasoning Engine",
        "Edge-TTS Chunk Synthesis",
        "Instant Interruption Barge-in",
        "Total Round-Trip Latency < 300ms"
    ]
    for idx, b in enumerate(d5b_bullets):
        draw.text((b5b_x1 + 16, r3_y + 146 + idx*26), "[*]", fill=d5_accent, font=bullet_font)
        draw.text((b5b_x1 + 40, r3_y + 146 + idx*26), b, fill=(201, 209, 217), font=body_font)

    # 5C: Model Context Protocol (MCP) & n8n
    b5c_x1 = b5b_x1 + sub5_w + 12
    draw_card(draw, [b5c_x1, r3_y + 96, b5c_x1 + sub5_w, r3_y + 416], (36, 26, 48), (168, 85, 247, 120), radius=10, border_width=1)
    draw.text((b5c_x1 + 16, r3_y + 112), "MCP Server & n8n Ops", fill=d5_accent, font=get_font(17, bold=True))
    d5c_bullets = [
        "Custom MCP Server (JSON-RPC/SSE)",
        "Exposes Snowflake Marts as Tools",
        "Order SLA Re-dispatch Actions",
        "n8n Workflow Automation:",
        "  - Negative Review Escalation",
        "  - Auto Wallet Compensation",
        "  - Delivery Delay Protocol"
    ]
    for idx, b in enumerate(d5c_bullets):
        draw.text((b5c_x1 + 16, r3_y + 146 + idx*26), "[*]", fill=d5_accent, font=bullet_font)
        draw.text((b5c_x1 + 40, r3_y + 146 + idx*26), b, fill=(201, 209, 217), font=body_font)

    # Domain 6 (Right)
    d6_x1 = 1600
    d6_w = width - d6_x1 - 80
    d6_x2 = d6_x1 + d6_w
    d6_accent = (245, 158, 11) # Amber / Gold
    draw_card(draw, [d6_x1, r3_y, d6_x2, r3_y + r3_h], (32, 26, 18), d6_accent, radius=18)

    draw.rounded_rectangle([d6_x1 + 20, r3_y + 16, d6_x1 + 290, r3_y + 42], radius=13, fill=(54, 38, 16), outline=d6_accent, width=1)
    draw.text((d6_x1 + 155, r3_y + 29), "DOMAIN 6: MULTI-CLOUD & GITOPS", fill=d6_accent, font=block_sub_font, anchor="mm")
    draw_step_badge(draw, d6_x2 - 30, r3_y + 29, "6", d6_accent, text_color=(0, 0, 0), font=step_font)

    draw.text((d6_x1 + 20, r3_y + 54), "Terraform, ArgoCD, SonarQube & PyRIT Red Teaming", fill=(255, 255, 255), font=block_title_font)

    # CONNECTOR 5 -> 6
    c56_y = r3_y + 200
    draw.line([d5_x2, c56_y, d6_x1, c56_y], fill=(245, 158, 11), width=4)
    draw.polygon([(d6_x1, c56_y), (d6_x1 - 14, c56_y - 8), (d6_x1 - 14, c56_y + 8)], fill=(245, 158, 11))
    draw_arrow_label(draw, (d5_x2 + d6_x1) // 2, c56_y, "11. Security Gate", "PyRIT + SonarQube", (245, 158, 11), font1=arrow_label_font, font2=arrow_sub_font)

    sub6_w = (d6_w - 40) // 2

    # 6A: Multi-Cloud Terraform & ArgoCD
    b6a_x1 = d6_x1 + 16
    draw_card(draw, [b6a_x1, r3_y + 96, b6a_x1 + sub6_w, r3_y + 416], (44, 34, 22), (245, 158, 11, 120), radius=10, border_width=1)
    draw.text((b6a_x1 + 16, r3_y + 112), "Multi-Cloud & GitOps", fill=d6_accent, font=get_font(17, bold=True))
    d6a_bullets = [
        "12. Declarative Terraform:",
        "  - AWS EKS + MSK + Aurora",
        "  - GCP GKE + Cloud SQL (DR)",
        "  - Azure AKS + Azure OpenAI",
        "ArgoCD Continuous GitOps Sync",
        "Automated Cluster Drift Defense",
        "RTO < 30s & RPO < 1s Multi-Cloud"
    ]
    for idx, b in enumerate(d6a_bullets):
        draw.text((b6a_x1 + 16, r3_y + 146 + idx*26), "[*]", fill=d6_accent, font=bullet_font)
        draw.text((b6a_x1 + 40, r3_y + 146 + idx*26), b, fill=(201, 209, 217), font=body_font)

    # 6B: DevSecOps & PyRIT Adversarial Gate
    b6b_x1 = b6a_x1 + sub6_w + 10
    draw_card(draw, [b6b_x1, r3_y + 96, b6b_x1 + sub6_w, r3_y + 416], (44, 34, 22), (245, 158, 11, 120), radius=10, border_width=1)
    draw.text((b6b_x1 + 16, r3_y + 112), "DevSecOps & PyRIT Gate", fill=d6_accent, font=get_font(17, bold=True))
    d6b_bullets = [
        "Jenkins + GitHub Actions Pipeline",
        "SonarQube Quality Gate (>80% cov)",
        "Nexus Repository Artifact Registry",
        "Trivy Container Vulnerability Scan",
        "Microsoft PyRIT Adversarial Attacks:",
        "  - Polymorphic Jailbreak Check",
        "  - Build Fails if Evasion > 0.0%"
    ]
    for idx, b in enumerate(d6b_bullets):
        draw.text((b6b_x1 + 16, r3_y + 146 + idx*26), "[*]", fill=d6_accent, font=bullet_font)
        draw.text((b6b_x1 + 40, r3_y + 146 + idx*26), b, fill=(201, 209, 217), font=body_font)

    # --- FOOTER ---
    footer_text = "Zomato Grand Unified Architecture Working Flow | End-to-End Enterprise Standard | Principal / Senior Staff Engineer Blueprint"
    draw.text((width // 2, height - 32), footer_text, fill=(139, 148, 158), font=footer_font, anchor="mm")

    for p in output_paths:
        os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
        img.save(p, "PNG")
        print(f"Successfully generated detailed working flow diagram at: {p}")

if __name__ == "__main__":
    generate_flow_diagram()
