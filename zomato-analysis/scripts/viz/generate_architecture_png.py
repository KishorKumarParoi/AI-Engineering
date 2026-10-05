#!/usr/bin/env python3
"""
Script: scripts/generate_architecture_png.py
Purpose: Generate a high-resolution, pixel-perfect, dark-mode architecture diagram PNG
         representing the "Principal Engineer Grand Unified Architecture Combo".
Target: docs/architecture.png
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

def draw_rounded_card(draw, xy, fill, outline, radius=16, border_width=2):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill, outline=outline, width=border_width)

def generate_diagram(output_path="docs/architecture.png"):
    width = 2400
    height = 1420
    
    # 1. Base Dark Solid Canvas (Pure RGB, #0d1117)
    base_bg = (13, 17, 23)
    img = Image.new("RGB", (width, height), base_bg)
    draw = ImageDraw.Draw(img)

    # 2. Subtle Radial Ambient Lighting via Composite
    glow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)

    # Top Center Crimson Glow
    for r in range(350, 0, -10):
        alpha = int(12 * (1 - r / 350))
        glow_draw.ellipse([width//2 - r*2, -r, width//2 + r*2, r*2], fill=(226, 55, 68, alpha))
    
    # Bottom Left Sky Blue Glow
    for r in range(400, 0, -15):
        alpha = int(10 * (1 - r / 400))
        glow_draw.ellipse([-r, height - r, r*2, height + r*2], fill=(56, 189, 248, alpha))
    
    # Bottom Right Violet Glow
    for r in range(400, 0, -15):
        alpha = int(10 * (1 - r / 400))
        glow_draw.ellipse([width - r*2, height - r*2, width + r, height + r], fill=(168, 85, 247, alpha))

    # Composite Glow onto Base
    img_rgba = img.convert("RGBA")
    img_rgba = Image.alpha_composite(img_rgba, glow_layer)
    img = img_rgba.convert("RGB")
    draw = ImageDraw.Draw(img)

    # Fonts
    brand_font = get_font(18, bold=True)
    badge_font = get_font(14, bold=True)
    title_font = get_font(42, bold=True)
    card_title_font = get_font(23, bold=True)
    card_tag_font = get_font(13, bold=True)
    body_font = get_font(18, bold=False)
    bullet_font = get_font(18, bold=True)
    footer_font = get_font(15, bold=False)

    # --- TOP HEADER ---
    header_y = 50
    draw.text((width // 2, header_y), "ZOMATO ENTERPRISE AI DATA & LOGISTICS PLATFORM", fill=(244, 63, 94), font=brand_font, anchor="mm")
    
    # Pill Badge
    badge_text = "PRINCIPAL ARCHITECT / SENIOR STAFF SYSTEM DESIGN BLUEPRINT"
    badge_w = 680
    badge_h = 34
    bx1 = (width - badge_w) // 2
    by1 = header_y + 22
    draw.rounded_rectangle([bx1, by1, bx1 + badge_w, by1 + badge_h], radius=17, fill=(22, 27, 34), outline=(56, 139, 253), width=1)
    draw.text((width // 2, by1 + 17), badge_text, fill=(88, 166, 255), font=badge_font, anchor="mm")

    main_title = "THE PRINCIPAL ENGINEER GRAND UNIFIED ARCHITECTURE COMBO"
    draw.text((width // 2, by1 + 72), main_title, fill=(255, 255, 255), font=title_font, anchor="mm")

    # Separator Line
    draw.line([140, by1 + 108, width - 140, by1 + 108], fill=(48, 54, 61), width=2)

    # --- 7 PILLARS GRID LAYOUT ---
    start_y = by1 + 132
    col_w = 680
    gutter_x = 40
    row_h = 320
    gutter_y = 28
    col1_x = (width - (col_w * 3 + gutter_x * 2)) // 2
    col2_x = col1_x + col_w + gutter_x
    col3_x = col2_x + col_w + gutter_x

    cards = [
        # (col_idx, row_idx, title, tag, accent_color, bullets)
        {
            "col": 0, "row": 0,
            "title": "1. LATEST NEXT.JS 16+ (REACT 19)",
            "tag": "EDGE & UI LAYER",
            "accent": (56, 189, 248), # Sky Blue
            "bullets": [
                "Next.js 16 App Router & Server Components (RSC)",
                "React 19 Server Actions & Streaming SSR (sub-50ms TTFB)",
                "Real-Time SSE & WebSocket Order Tracking Pipeline",
                "Glassmorphic Consumer Flow & Faceted Catalog Search",
                "Embedded Dual-Engine AI Exploration Drawer"
            ]
        },
        {
            "col": 1, "row": 0,
            "title": "4. AGENTIC AI & VOICE AGENT",
            "tag": "AUTONOMOUS REASONING",
            "accent": (168, 85, 247), # Purple
            "bullets": [
                "LangGraph Cyclic StateGraph with Self-Critique Loops",
                "AST SQL Guardrails (Read-Only SELECT/WITH Enforcement)",
                "Real-Time Voice Engine: Silero VAD (<15ms) + Faster-Whisper",
                "Streaming Edge-TTS with Instant Interruption Detection",
                "Model Context Protocol (MCP) & n8n Operational Workflows"
            ]
        },
        {
            "col": 2, "row": 0,
            "title": "6. HIGH-THROUGHPUT MICROSERVICES",
            "tag": "DISTRIBUTED CORE (GO)",
            "accent": (244, 63, 94), # Rose Red
            "bullets": [
                "Go 1.24+ Hexagonal Architecture (Sub-10ms Latency)",
                "Transactional Outbox Pattern (Zero Event Loss Guarantee)",
                "Distributed Saga Orchestrator with Compensating Actions",
                "Kafka Event Mesh with Debezium CDC Postgres WAL",
                "Redis Cache-Aside Pattern with Bloom Filter Protection"
            ]
        },
        {
            "col": 0, "row": 1,
            "title": "2. DATA ENGINEERING LAKEHOUSE",
            "tag": "PETABYTE LAKEHOUSE",
            "accent": (2, 132, 199), # Cyan
            "bullets": [
                "35M+ Rows Snowflake Medallion Lakehouse Storage",
                "Bronze (RAW) -> Silver (7 Conformed) -> Gold (10 Marts)",
                "SCD Type 2 Snapshots (SNAP_RESTAURANTS Time-Travel)",
                "Astronomer Airflow Isolated Batch DAG Orchestration",
                "dbt Core Idempotent Models with Data Quality Contracts"
            ]
        },
        {
            "col": 1, "row": 1,
            "title": "5. MLOPS & LLMOPS INFRASTRUCTURE",
            "tag": "AI LIFECYCLE & GPU",
            "accent": (16, 185, 129), # Emerald Green
            "bullets": [
                "Kubeflow Automated Delivery ETA SLA Prediction Pipeline",
                "MLflow Feature Store, Model Registry & Metric Tracking",
                "TensorZero / LiteLLM Proxy with Dynamic Multi-Cloud Fallback",
                "Semantic Cache in Redis (65% Query Cost Reduction)",
                "Kubernetes GPU Serving Cluster running vLLM (Tensor Parallel)"
            ]
        },
        {
            "col": 2, "row": 1,
            "title": "3. DEVOPS, GITOPS & MULTI-CLOUD",
            "tag": "INFRASTRUCTURE AS CODE",
            "accent": (245, 158, 11), # Amber
            "bullets": [
                "Multi-Cloud Terraform: AWS EKS, GCP GKE, Azure AKS",
                "ArgoCD Declarative GitOps Continuous Drift Sync",
                "SonarQube Quality Gate (>80% Cov) & Nexus Artifacts",
                "Microsoft PyRIT Adversarial AI Red-Teaming in CI/CD",
                "Trivy Container CVE Security & Ruff/GolangCI Linter Gates"
            ]
        }
    ]

    # Render Cards 1 to 6
    for c in cards:
        cx = col1_x if c["col"] == 0 else (col2_x if c["col"] == 1 else col3_x)
        cy = start_y + c["row"] * (row_h + gutter_y)
        cw = col_w
        ch = row_h

        r, g, b = c["accent"]
        bg_fill = (22, 27, 34)
        border_outline = (r, g, b)
        draw_rounded_card(draw, [cx, cy, cx + cw, cy + ch], bg_fill, border_outline, radius=16, border_width=2)

        # Card Pill Tag
        pill_w = 200
        pill_h = 24
        draw.rounded_rectangle([cx + 20, cy + 18, cx + 20 + pill_w, cy + 18 + pill_h], radius=12, fill=(r//7 + 10, g//7 + 10, b//7 + 10), outline=(r, g, b), width=1)
        draw.text((cx + 20 + pill_w // 2, cy + 18 + pill_h // 2), c["tag"], fill=(r, g, b), font=card_tag_font, anchor="mm")

        # Card Title
        draw.text((cx + 20, cy + 54), c["title"], fill=(255, 255, 255), font=card_title_font)

        # Bullets
        bullet_start_y = cy + 96
        line_spacing = 38
        for i, bullet in enumerate(c["bullets"]):
            by = bullet_start_y + i * line_spacing
            draw.text((cx + 24, by), "[+]", fill=(r, g, b), font=bullet_font)
            draw.text((cx + 58, by), bullet, fill=(201, 209, 217), font=body_font)

    # --- ROW 3: CARD 7 (WIDE FULL SPAN FOR SYSTEM DESIGN & RESILIENCE) ---
    c7_x = col1_x
    c7_y = start_y + 2 * (row_h + gutter_y)
    c7_w = col_w * 3 + gutter_x * 2
    c7_h = 260
    accent7 = (99, 102, 241) # Indigo
    r7, g7, b7 = accent7

    draw_rounded_card(draw, [c7_x, c7_y, c7_x + c7_w, c7_y + c7_h], (22, 27, 34), (r7, g7, b7), radius=16, border_width=2)

    # Pill
    draw.rounded_rectangle([c7_x + 24, c7_y + 18, c7_x + 24 + 250, c7_y + 18 + 26], radius=13, fill=(r7//7 + 10, g7//7 + 10, b7//7 + 10), outline=(r7, g7, b7), width=1)
    draw.text((c7_x + 24 + 125, c7_y + 31), "SYSTEM ARCHITECTURE & DEFENSE", fill=(r7, g7, b7), font=card_tag_font, anchor="mm")

    draw.text((c7_x + 24, c7_y + 56), "7. SYSTEM DESIGN, RESILIENCE & PRINCIPAL INTERVIEW DEFENSE", fill=(255, 255, 255), font=card_title_font)

    # 3 Columns inside Card 7
    col7_w = (c7_w - 80) // 3
    bullets_c7 = [
        [
            "C4 Architecture & Zero-Loss Mesh Design",
            "Multi-Region Active-Active Topologies",
            "Cloudflare Anycast Global Edge WAF & DNS",
            "RTO < 30s & RPO < 1s Replication Guarantees"
        ],
        [
            "Strict Low-Level Data Contracts (LLD)",
            "Client Idempotency Keys across Redis & DB",
            "Compensating Transactions for Failed Sagas",
            "AST SQL Parser Blocking Data Mutations"
        ],
        [
            "10-Question Principal Masterclass Defense",
            "Decoupled Latency & Consistency Boundaries",
            "Effective-Once Distributed Event Processing",
            "Continuous Production Resilience Testing"
        ]
    ]

    for c_idx, sub_bullets in enumerate(bullets_c7):
        sub_x = c7_x + 28 + c_idx * (col7_w + 24)
        for b_idx, bullet in enumerate(sub_bullets):
            by = c7_y + 104 + b_idx * 35
            draw.text((sub_x, by), "->", fill=(r7, g7, b7), font=bullet_font)
            draw.text((sub_x + 28, by), bullet, fill=(201, 209, 217), font=body_font)

    # --- FOOTER ---
    footer_text = "Single Source of Truth Architecture Blueprint | Standard: Production-Grade Zero-Loss Multi-Cloud Mesh | Level: Principal / Senior Staff Engineer"
    draw.text((width // 2, height - 32), footer_text, fill=(139, 148, 158), font=footer_font, anchor="mm")

    # Save PNG
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG")
    print(f"Pristine high-resolution architecture diagram generated at: {output_path}")

if __name__ == "__main__":
    generate_diagram()
