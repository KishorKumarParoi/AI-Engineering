"""
Precision renderer for design.png matching architecture.png
Now includes:
  - Top 6 Medallion & Platform Lifecycle Cards
  - AI Lane (4 Capabilities: LLM Enrichment, Agentic RAG, Text-to-SQL & MCP, Real-Time Voice)
  - MLOps & GPU Serving Lane (Kubeflow XGBoost, MLflow Registry, vLLM A10G/T4, TensorZero, Redis Semantic Cache)
  - DevOps, GitOps & AI Security Lane (Terraform Multi-Cloud, ArgoCD GitOps, SonarQube Gate, PyRIT Red Team)
  - Airflow Orchestration Lane (6 DAG tasks)
  - Foundation, Tools & Security Bar
All rendered with 100% SVG vector brand icons and dynamic dashed connector lines.
"""
import os
import subprocess
import shutil

HTML_TEMPLATE = r'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Zomato Enterprise Grand Unified Architecture</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600;700&display=swap" rel="stylesheet">
  <style>
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }
    body {
      background-color: #ffffff;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      color: #0f172a;
      width: 2200px;
      height: 1440px;
      padding: 24px 40px;
      position: relative;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }

    /* =========================================================================
       1. TOP ROW: 6 MEDALLION & LIFECYCLE CARDS
       ========================================================================= */
    .top-cards-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      width: 100%;
      height: 180px;
      z-index: 2;
    }

    .top-card {
      width: 320px;
      height: 180px;
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      position: relative;
    }

    .top-card-header {
      height: 35px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 13.5px;
      font-weight: 800;
      letter-spacing: 1.2px;
      text-transform: uppercase;
      color: #ffffff;
    }

    .top-card-header.source { background: #64748b; }
    .top-card-header.lake   { background: #0284c7; }
    .top-card-header.bronze { background: #9a5323; }
    .top-card-header.silver { background: #8c939e; }
    .top-card-header.gold   { background: #d97706; }
    .top-card-header.serve  { background: #dc2626; }

    .top-card-body {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 8px 14px;
      text-align: center;
    }

    .top-card-icons {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 12px;
      margin-bottom: 6px;
      height: 38px;
    }

    .top-card-title {
      font-size: 15px;
      font-weight: 700;
      color: #0f172a;
      margin-bottom: 3px;
      letter-spacing: -0.2px;
    }

    .top-card-desc {
      font-size: 11px;
      line-height: 1.45;
      color: #64748b;
      font-weight: 500;
    }

    /* TOP ARROWS */
    .top-arrow {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      width: 28px;
      height: 100%;
      color: #334155;
    }
    .top-arrow-icon {
      width: 22px;
      height: 22px;
    }
    .top-arrow-dbt {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 2px;
    }
    .top-arrow-dbt span {
      font-size: 11px;
      font-weight: 700;
      color: #ff694b;
    }

    /* =========================================================================
       SECTION CONTAINERS: LANES WITH DASHED BORDERS
       ========================================================================= */
    .section-lane {
      width: 100%;
      border-radius: 14px;
      background: #ffffff;
      padding: 14px 22px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      position: relative;
      z-index: 2;
    }

    .ai-lane-box {
      height: 430px;
      border: 1.5px dashed #2563eb;
    }

    .mlops-lane-box {
      height: 225px;
      border: 1.5px dashed #059669;
    }

    .devops-lane-box {
      height: 225px;
      border: 1.5px dashed #7c3aed;
    }

    .lane-header {
      display: flex;
      align-items: center;
      gap: 16px;
      margin-bottom: 4px;
    }
    .lane-title-badge {
      font-size: 13.5px;
      font-weight: 800;
      letter-spacing: 0.8px;
      text-transform: uppercase;
    }
    .lane-title-badge.blue   { color: #1d4ed8; }
    .lane-title-badge.green  { color: #047857; }
    .lane-title-badge.purple { color: #6d28d9; }

    .lane-tech-stack {
      font-size: 11.5px;
      color: #64748b;
      font-weight: 500;
    }

    /* ROW & STEP CHAINS */
    .lane-row {
      display: flex;
      align-items: center;
      height: 84px;
      gap: 16px;
      width: 100%;
    }

    .lane-label-col {
      display: flex;
      align-items: center;
      gap: 12px;
      width: 230px;
      flex-shrink: 0;
    }
    .lane-num-badge {
      width: 26px;
      height: 26px;
      border-radius: 50%;
      color: #ffffff;
      font-size: 12px;
      font-weight: 800;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    .lane-num-badge.blue   { background: #1e3a8a; }
    .lane-num-badge.green  { background: #065f46; }
    .lane-num-badge.purple { background: #581c87; }

    .lane-label-info {
      display: flex;
      flex-direction: column;
    }
    .lane-row-title {
      font-size: 13.5px;
      font-weight: 700;
      color: #0f172a;
      letter-spacing: -0.2px;
    }
    .lane-row-sub {
      font-size: 11px;
      color: #64748b;
      font-weight: 500;
      margin-top: 1px;
    }

    .step-chain {
      display: flex;
      align-items: center;
      gap: 10px;
      flex: 1;
      height: 100%;
    }

    .step-box {
      height: 60px;
      background: #ffffff;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      padding: 0 14px;
      display: flex;
      align-items: center;
      gap: 10px;
      box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03);
    }

    /* Box width distribution */
    .ai-lane-box .lane-row:nth-child(2) .step-box,
    .ai-lane-box .lane-row:nth-child(3) .step-box {
      width: 300px;
      flex: none;
    }
    .ai-lane-box .lane-row:nth-child(4) .step-box {
      width: 260px;
      flex: none;
    }
    .ai-lane-box .lane-row:nth-child(5) .step-box {
      width: 235px;
      flex: none;
    }

    .mlops-lane-box .step-box {
      flex: 1;
    }
    .devops-lane-box .step-box {
      flex: 1;
    }

    .step-box.highlight-blue {
      border: 1.5px solid #2563eb;
      background: #f0f7ff;
    }
    .step-box.highlight-green {
      border: 1.5px solid #059669;
      background: #ecfdf5;
    }
    .step-box.highlight-purple {
      border: 1.5px solid #7c3aed;
      background: #faf5ff;
    }
    .step-box.alert {
      border: 1.5px solid #ef4444;
      background: #fef2f2;
    }

    .step-box-icon {
      width: 24px;
      height: 24px;
      flex-shrink: 0;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .step-box-content {
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .step-box-title {
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      font-weight: 600;
      color: #1e293b;
      white-space: nowrap;
    }
    .step-box.highlight-blue .step-box-title { color: #1d4ed8; font-weight: 700; }
    .step-box.highlight-green .step-box-title { color: #047857; font-weight: 700; }
    .step-box.highlight-purple .step-box-title { color: #6d28d9; font-weight: 700; }
    .step-box.alert .step-box-title { color: #b91c1c; font-weight: 700; }

    .step-box-sub {
      font-size: 10px;
      color: #64748b;
      font-weight: 500;
      margin-top: 1px;
      white-space: nowrap;
    }

    .step-arrow {
      color: #334155;
      font-size: 18px;
      font-weight: 600;
      flex-shrink: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      width: 12px;
    }

    /* =========================================================================
       4. ORCHESTRATION LANE
       ========================================================================= */
    .orchestration-container {
      width: 100%;
      height: 84px;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      background: #ffffff;
      box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
      padding: 0 24px;
      display: flex;
      align-items: center;
      gap: 16px;
      z-index: 2;
    }

    .orchestration-brand-card {
      display: flex;
      align-items: center;
      gap: 12px;
      width: 230px;
      flex-shrink: 0;
    }
    .orchestration-brand-icon {
      width: 40px;
      height: 40px;
      flex-shrink: 0;
    }
    .orchestration-brand-info {
      display: flex;
      flex-direction: column;
    }
    .orchestration-brand-tag {
      font-size: 10.5px;
      font-weight: 800;
      letter-spacing: 0.6px;
      text-transform: uppercase;
      color: #0284c7;
    }
    .orchestration-brand-name {
      font-size: 14px;
      font-weight: 700;
      color: #0f172a;
    }
    .orchestration-brand-dag {
      font-size: 10.5px;
      color: #64748b;
      font-weight: 500;
    }

    .orchestration-chain {
      display: flex;
      align-items: center;
      gap: 12px;
      flex: 1;
    }

    .orch-task-box {
      flex: 1;
      height: 56px;
      background: #ffffff;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      padding: 0 12px;
      display: flex;
      align-items: center;
      gap: 10px;
      box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03);
    }
    .orch-task-box.purple { border: 1.5px solid #a855f7; background: #faf5ff; }
    .orch-task-box.blue   { border: 1.5px solid #3b82f6; background: #eff6ff; }
    .orch-task-box.orange { border: 1.5px solid #f97316; background: #fff7ed; }

    .orch-task-icon {
      width: 20px;
      height: 20px;
      flex-shrink: 0;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .orch-task-text {
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .orch-task-title {
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      font-weight: 700;
      color: #1e293b;
      white-space: nowrap;
    }
    .orch-task-sub {
      font-size: 9.5px;
      color: #64748b;
      font-weight: 500;
      margin-top: 1px;
      white-space: nowrap;
    }

    /* =========================================================================
       5. FOUNDATION & TOOLS & SECURITY BAR
       ========================================================================= */
    .footer-bar {
      width: 100%;
      height: 68px;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      background: #ffffff;
      box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03);
      padding: 0 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      z-index: 2;
    }

    .foundation-col {
      display: flex;
      align-items: center;
      gap: 20px;
    }

    .foundation-label {
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 0.8px;
      text-transform: uppercase;
      color: #64748b;
    }

    .tech-badges-list {
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .tech-item {
      display: flex;
      align-items: center;
      gap: 5px;
      font-size: 12px;
      font-weight: 600;
      color: #1e293b;
    }

    .tech-item svg {
      width: 18px;
      height: 18px;
    }

    .security-box {
      display: flex;
      align-items: center;
      gap: 10px;
      padding-left: 18px;
      border-left: 1px solid #e2e8f0;
    }
    .security-icon {
      width: 24px;
      height: 24px;
    }
    .security-info {
      display: flex;
      flex-direction: column;
    }
    .security-title {
      font-size: 12px;
      font-weight: 700;
      color: #0f172a;
    }
    .security-sub {
      font-size: 10px;
      color: #64748b;
      font-weight: 500;
    }

    /* =========================================================================
       6. SVG CONNECTOR ARROWS OVERLAY
       ========================================================================= */
    .connector-overlay {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
      z-index: 10;
    }
  </style>
</head>
<body>

  <!-- =======================================================================
       1. TOP ROW CARDS (6 Pipeline Cards)
       ======================================================================= -->
  <div class="top-cards-row">
    <!-- CARD 1: SOURCE -->
    <div class="top-card" id="card-source">
      <div class="top-card-header source">SOURCE</div>
      <div class="top-card-body">
        <div class="top-card-icons">
          <!-- Zomato Script Logo -->
          <svg viewBox="0 0 106 28" height="22">
            <text x="0" y="22" font-family="'Inter', sans-serif" font-weight="900" font-style="italic" font-size="26" fill="#E23744">zomato</text>
          </svg>
          <!-- Next.js Logo -->
          <svg viewBox="0 0 180 180" height="22">
            <circle cx="90" cy="90" r="85" fill="#000000"/>
            <path d="M149.5 163.5L67.5 56H52V124H63.5V72.5L138 168.5Z" fill="#ffffff"/>
            <path d="M117 56H128.5V106.5L117 92V56Z" fill="#ffffff"/>
          </svg>
        </div>
        <div class="top-card-title">Zomato Dataset</div>
        <div class="top-card-desc">
          7 CSV folders &middot; 35M+ rows<br>
          country, users, restaurants, orders,<br>
          order_items, menu, reviews
        </div>
      </div>
    </div>

    <!-- ARROW 1 -->
    <div class="top-arrow">
      <svg class="top-arrow-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <line x1="4" y1="12" x2="20" y2="12"></line>
        <polyline points="14 6 20 12 14 18"></polyline>
      </svg>
    </div>

    <!-- CARD 2: LAKE -->
    <div class="top-card" id="card-lake">
      <div class="top-card-header lake">LAKE</div>
      <div class="top-card-body">
        <div class="top-card-icons">
          <!-- S3 Green Bucket Logo with Handle -->
          <svg viewBox="0 0 100 100" height="38">
            <path d="M22 36 L32 82 C33 87 36 90 41 90 L59 90 C64 90 67 87 68 82 L78 36" fill="#dcfce7" stroke="#16a34a" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
            <ellipse cx="50" cy="36" rx="28" ry="10" fill="#22c55e" stroke="#16a34a" stroke-width="5"/>
            <path d="M22 36 C22 18 78 18 78 36" fill="none" stroke="#15803d" stroke-width="4.5" stroke-linecap="round"/>
            <line x1="50" y1="18" x2="50" y2="24" stroke="#15803d" stroke-width="4.5" stroke-linecap="round"/>
          </svg>
        </div>
        <div class="top-card-title">Amazon S3</div>
        <div class="top-card-desc">
          raw / &lt;table&gt; /<br>
          7 CSV folders &middot; 2.3 GB<br>
          (automated / manual upload)
        </div>
      </div>
    </div>

    <!-- ARROW 2 -->
    <div class="top-arrow">
      <svg class="top-arrow-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <line x1="4" y1="12" x2="20" y2="12"></line>
        <polyline points="14 6 20 12 14 18"></polyline>
      </svg>
    </div>

    <!-- CARD 3: BRONZE -->
    <div class="top-card" id="card-bronze">
      <div class="top-card-header bronze">BRONZE</div>
      <div class="top-card-body">
        <div class="top-card-icons">
          <!-- Snowflake Logo -->
          <svg viewBox="0 0 100 100" height="38">
            <g stroke="#29B5E8" stroke-width="6" stroke-linecap="round" stroke-linejoin="round">
              <line x1="50" y1="12" x2="50" y2="88"/>
              <line x1="12" y1="50" x2="88" y2="50"/>
              <line x1="23" y1="23" x2="77" y2="77"/>
              <line x1="23" y1="77" x2="77" y2="23"/>
              <path d="M42 20 L50 12 L58 20" fill="none"/>
              <path d="M42 80 L50 88 L58 80" fill="none"/>
              <path d="M20 42 L12 50 L20 58" fill="none"/>
              <path d="M80 42 L88 50 L80 58" fill="none"/>
              <circle cx="50" cy="50" r="5" fill="#29B5E8"/>
            </g>
          </svg>
        </div>
        <div class="top-card-title">Snowflake RAW</div>
        <div class="top-card-desc">
          COPY via<br>
          storage integration<br>
          7 raw tables &middot; 35M+ rows
        </div>
      </div>
    </div>

    <!-- ARROW 3 -->
    <div class="top-arrow">
      <svg class="top-arrow-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <line x1="4" y1="12" x2="20" y2="12"></line>
        <polyline points="14 6 20 12 14 18"></polyline>
      </svg>
    </div>

    <!-- CARD 4: SILVER -->
    <div class="top-card" id="card-silver">
      <div class="top-card-header silver">SILVER</div>
      <div class="top-card-body">
        <div class="top-card-icons">
          <!-- Snowflake Logo -->
          <svg viewBox="0 0 100 100" height="38">
            <g stroke="#29B5E8" stroke-width="6" stroke-linecap="round" stroke-linejoin="round">
              <line x1="50" y1="12" x2="50" y2="88"/>
              <line x1="12" y1="50" x2="88" y2="50"/>
              <line x1="23" y1="23" x2="77" y2="77"/>
              <line x1="23" y1="77" x2="77" y2="23"/>
              <path d="M42 20 L50 12 L58 20" fill="none"/>
              <path d="M42 80 L50 88 L58 80" fill="none"/>
              <path d="M20 42 L12 50 L20 58" fill="none"/>
              <path d="M80 42 L88 50 L80 58" fill="none"/>
              <circle cx="50" cy="50" r="5" fill="#29B5E8"/>
            </g>
          </svg>
        </div>
        <div class="top-card-title">STAGING (dbt)</div>
        <div class="top-card-desc">
          clean &bull; type &bull; join<br>
          7 conformed views<br>
          schema contracts locked
        </div>
      </div>
    </div>

    <!-- ARROW 4 WITH DBT LOGO -->
    <div class="top-arrow top-arrow-dbt">
      <div style="display:flex; align-items:center; gap: 4px;">
        <svg viewBox="0 0 24 24" width="20" height="20">
          <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="#FF694B"/>
          <path d="M2 17L12 22L22 17V12L12 17L2 12V17Z" fill="#E04E31"/>
        </svg>
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="#334155" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <line x1="4" y1="12" x2="20" y2="12"></line>
          <polyline points="14 6 20 12 14 18"></polyline>
        </svg>
      </div>
      <span>dbt</span>
    </div>

    <!-- CARD 5: GOLD -->
    <div class="top-card" id="card-gold">
      <div class="top-card-header gold">GOLD</div>
      <div class="top-card-body">
        <div class="top-card-icons">
          <!-- Snowflake Logo -->
          <svg viewBox="0 0 100 100" height="38">
            <g stroke="#29B5E8" stroke-width="6" stroke-linecap="round" stroke-linejoin="round">
              <line x1="50" y1="12" x2="50" y2="88"/>
              <line x1="12" y1="50" x2="88" y2="50"/>
              <line x1="23" y1="23" x2="77" y2="77"/>
              <line x1="23" y1="77" x2="77" y2="23"/>
              <path d="M42 20 L50 12 L58 20" fill="none"/>
              <path d="M42 80 L50 88 L58 80" fill="none"/>
              <path d="M20 42 L12 50 L20 58" fill="none"/>
              <path d="M80 42 L88 50 L80 58" fill="none"/>
              <circle cx="50" cy="50" r="5" fill="#29B5E8"/>
            </g>
          </svg>
        </div>
        <div class="top-card-title">MARTS (dbt)</div>
        <div class="top-card-desc">
          dims &bull; incremental facts<br>
          fct_orders &bull; delivery SLA<br>
          snapshots (SCD Type 2)
        </div>
      </div>
    </div>

    <!-- ARROW 5 -->
    <div class="top-arrow">
      <svg class="top-arrow-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <line x1="4" y1="12" x2="20" y2="12"></line>
        <polyline points="14 6 20 12 14 18"></polyline>
      </svg>
    </div>

    <!-- CARD 6: SERVE -->
    <div class="top-card" id="card-serve">
      <div class="top-card-header serve">SERVE</div>
      <div class="top-card-body">
        <div class="top-card-icons">
          <!-- Streamlit Crown Logo -->
          <svg viewBox="0 0 100 80" height="26">
            <path d="M50 10 L68 55 L32 55 Z" fill="#FF4B4B"/>
            <path d="M15 32 L34 68 L8 68 Z" fill="#FF2B2B"/>
            <path d="M85 32 L92 68 L66 68 Z" fill="#FF2B2B"/>
            <polygon points="26,68 74,68 50,78" fill="#D32F2F"/>
          </svg>
          <!-- Snowflake Logo -->
          <svg viewBox="0 0 100 100" height="26">
            <g stroke="#29B5E8" stroke-width="7" stroke-linecap="round" stroke-linejoin="round">
              <line x1="50" y1="14" x2="50" y2="86"/>
              <line x1="14" y1="50" x2="86" y2="50"/>
              <line x1="24.5" y1="24.5" x2="75.5" y2="75.5"/>
              <line x1="24.5" y1="75.5" x2="75.5" y2="24.5"/>
            </g>
          </svg>
          <!-- Next.js Logo -->
          <svg viewBox="0 0 180 180" height="24">
            <circle cx="90" cy="90" r="85" fill="#000000"/>
            <path d="M149.5 163.5L67.5 56H52V124H63.5V72.5L138 168.5Z" fill="#ffffff"/>
            <path d="M117 56H128.5V106.5L117 92V56Z" fill="#ffffff"/>
          </svg>
        </div>
        <div class="top-card-title">Next.js &middot; Streamlit</div>
        <div class="top-card-desc">
          Real-Time SSE Tracking &middot; Snowsight<br>
          BI Dashboard &middot; DAC Portals<br>
          Voice Agent (&lt;300ms) &middot; MCP
        </div>
      </div>
    </div>
  </div>


  <!-- =======================================================================
       2. AI LANE - FOUR ENTERPRISE CAPABILITIES (DASHED BLUE BOX)
       ======================================================================= -->
  <div class="section-lane ai-lane-box" id="ai-lane">
    <div class="lane-header">
      <div class="lane-title-badge blue">AI LANE &ndash; FOUR ENTERPRISE CAPABILITIES</div>
      <div class="lane-tech-stack">OpenAI &middot; GPT-4o mini &middot; text-embedding-3-small &middot; LangGraph Loops &middot; Silero VAD &middot; Faster-Whisper &middot; MCP</div>
    </div>

    <!-- CAPABILITY 1: LLM ENRICHMENT -->
    <div class="lane-row">
      <div class="lane-label-col">
        <div class="lane-num-badge blue">1</div>
        <div class="lane-label-info">
          <div class="lane-row-title">LLM ENRICHMENT</div>
          <div class="lane-row-sub">LLM as a transform step</div>
        </div>
      </div>

      <div class="step-chain">
        <div class="step-box" id="node-stg-reviews">
          <div class="step-box-icon">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#64748b" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2"/>
              <line x1="3" y1="9" x2="21" y2="9"/>
              <line x1="9" y1="3" x2="9" y2="21"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">stg_reviews</div>
            <div class="step-box-sub">Silver cleansed text</div>
          </div>
        </div>

        <div class="step-arrow">&rarr;</div>

        <div class="step-box highlight-blue" id="node-enrich-summary">
          <div class="step-box-icon">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#2563eb" stroke-width="2">
              <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">enrich_summary</div>
            <div class="step-box-sub">prompted &bull; type: JSON</div>
          </div>
        </div>

        <div class="step-arrow">&rarr;</div>

        <div class="step-box" id="node-review-enriched">
          <div class="step-box-icon">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="#0284c7">
              <path d="M22.28 11.23a5.52 5.52 0 0 0-.48-4.52 5.6 5.6 0 0 0-3.85-2.6 5.56 5.56 0 0 0-4.83.69 5.5 5.5 0 0 0-3.32-1.8 5.6 5.6 0 0 0-5.18 2.37 5.54 5.54 0 0 0-1.87 4.6 5.6 5.6 0 0 0-2.48 4.2 5.57 5.57 0 0 0 1.2 5.15 5.54 5.54 0 0 0 3.86 2.6 5.57 5.57 0 0 0 4.82-.69 5.53 5.53 0 0 0 3.32 1.8 5.6 5.6 0 0 0 5.19-2.38 5.55 5.55 0 0 0 1.86-4.6 5.6 5.6 0 0 0 2.48-4.2 5.56 5.56 0 0 0-.92-4.62zm-8.88 9.38a3.94 3.94 0 0 1-2.47-.87l.14-.08 4.1-2.37a.82.82 0 0 0 .41-.71v-5.78l1.73 1v4.77a3.96 3.96 0 0 1-3.91 4.04zm-8.6-3.81a3.93 3.93 0 0 1-.5-2.58l.14.08 4.1 2.37a.81.81 0 0 0 .82 0l5-2.89v2l-4.13 2.39a3.95 3.95 0 0 1-5.43-1.37zm-1.08-8.82a3.94 3.94 0 0 1 1.97-1.71v4.9a.83.83 0 0 0 .41.72l5 2.89-1.73 1-4.14-2.39a3.96 3.96 0 0 1-1.51-5.41zm15.15 4.31l-5-2.89 1.73-1 4.14 2.39a3.96 3.96 0 0 1 1.51 5.41 3.94 3.94 0 0 1-1.97 1.71v-4.9a.82.82 0 0 0-.41-.72zm2.14-3.08l-.14-.08-4.1-2.37a.83.83 0 0 0-.82 0l-5 2.89v-2l4.13-2.39a3.95 3.95 0 0 1 5.43 1.37 3.94 3.94 0 0 1 .5 2.58zm-11.45-3.3a3.95 3.95 0 0 1 3.9-4.04 3.94 3.94 0 0 1 2.48.87l-.14.08-4.1 2.37a.82.82 0 0 0-.41.71v5.78l-1.73-1v-4.77zm1.18 5.46l2.25-1.3 2.25 1.3v2.6l-2.25 1.3-2.25-1.3z"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">AI.REVIEW_ENRICHED</div>
            <div class="step-box-sub">Sentiment &bull; tags &bull; issues</div>
          </div>
        </div>

        <div class="step-arrow">&rarr;</div>

        <div class="step-box" id="node-review-insights">
          <div class="step-box-icon">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#64748b" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2"/>
              <line x1="3" y1="9" x2="21" y2="9"/>
              <line x1="9" y1="3" x2="9" y2="21"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">mart_review_insights</div>
            <div class="step-box-sub">Gold analytics mart</div>
          </div>
        </div>
      </div>
    </div>

    <!-- CAPABILITY 2: RAG & LANGGRAPH -->
    <div class="lane-row">
      <div class="lane-label-col">
        <div class="lane-num-badge blue">2</div>
        <div class="lane-label-info">
          <div class="lane-row-title">AGENTIC RAG</div>
          <div class="lane-row-sub">chat with your reviews</div>
        </div>
      </div>

      <div class="step-chain">
        <div class="step-box">
          <div class="step-box-icon">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#64748b" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2"/>
              <line x1="3" y1="9" x2="21" y2="9"/>
              <line x1="9" y1="3" x2="9" y2="21"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">reviews</div>
            <div class="step-box-sub">300K customer texts</div>
          </div>
        </div>

        <div class="step-arrow">&rarr;</div>

        <div class="step-box highlight-blue">
          <div class="step-box-icon">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#2563eb" stroke-width="2">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">embed &rarr; vectors</div>
            <div class="step-box-sub">text-embedding-3-small</div>
          </div>
        </div>

        <div class="step-arrow">&rarr;</div>

        <div class="step-box">
          <div class="step-box-icon">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#64748b" stroke-width="2">
              <ellipse cx="12" cy="5" rx="9" ry="3"/>
              <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
              <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">vector_store</div>
            <div class="step-box-sub">Cosine similarity search</div>
          </div>
        </div>

        <div class="step-arrow">&rarr;</div>

        <div class="step-box highlight-blue" id="node-rag-chat">
          <div class="step-box-icon">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#2563eb" stroke-width="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">rag_chat.py (LangGraph)</div>
            <div class="step-box-sub">grounded answer &bull; sources</div>
          </div>
        </div>
      </div>
    </div>

    <!-- CAPABILITY 3: TEXT-TO-SQL & MCP -->
    <div class="lane-row">
      <div class="lane-label-col">
        <div class="lane-num-badge blue">3</div>
        <div class="lane-label-info">
          <div class="lane-row-title">TEXT-TO-SQL &amp; MCP</div>
          <div class="lane-row-sub">chat with warehouse &bull; tools</div>
        </div>
      </div>

      <div class="step-chain">
        <div class="step-box" id="node-marts-schema">
          <div class="step-box-icon">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#64748b" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2"/>
              <line x1="3" y1="9" x2="21" y2="9"/>
              <line x1="9" y1="3" x2="9" y2="21"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">MARTS schema</div>
            <div class="step-box-sub">DDL &amp; Gold metadata</div>
          </div>
        </div>

        <div class="step-arrow">&rarr;</div>

        <div class="step-box highlight-blue">
          <div class="step-box-icon">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#2563eb" stroke-width="2">
              <polyline points="16 18 22 12 16 6"/>
              <polyline points="8 6 2 12 8 18"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">&lt;/&gt; text_to_sql.py</div>
            <div class="step-box-sub">NL &rarr; SQL engine</div>
          </div>
        </div>

        <div class="step-arrow">&rarr;</div>

        <div class="step-box">
          <div class="step-box-icon">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#16a34a" stroke-width="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              <polyline points="9 12 11 14 15 10"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">SELECT-only guard</div>
            <div class="step-box-sub">AST syntax parser</div>
          </div>
        </div>

        <div class="step-arrow">&rarr;</div>

        <div class="step-box">
          <div class="step-box-icon">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#64748b" stroke-width="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
              <circle cx="12" cy="7" r="4"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">run as DBT_ROLE</div>
            <div class="step-box-sub">Read-only RBAC sandbox</div>
          </div>
        </div>

        <div class="step-arrow">&rarr;</div>

        <div class="step-box highlight-purple" id="node-mcp-tools">
          <div class="step-box-icon">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#7c3aed" stroke-width="2">
              <path d="M12 2v6m0 8v6M4.93 4.93l4.24 4.24m5.66 5.66l4.24 4.24M2 12h6m8 0h6M4.93 19.07l4.24-4.24m5.66-5.66l4.24-4.24"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">MCP Server Tools</div>
            <div class="step-box-sub">JSON-RPC Claude / Cursor</div>
          </div>
        </div>
      </div>
    </div>

    <!-- CAPABILITY 4: REAL-TIME VOICE -->
    <div class="lane-row">
      <div class="lane-label-col">
        <div class="lane-num-badge blue">4</div>
        <div class="lane-label-info">
          <div class="lane-row-title">REAL-TIME VOICE AGENT</div>
          <div class="lane-row-sub">full-duplex conversational AI</div>
        </div>
      </div>

      <div class="step-chain">
        <div class="step-box">
          <div class="step-box-icon">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#64748b" stroke-width="2">
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
              <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
              <line x1="12" y1="19" x2="12" y2="23"/>
              <line x1="8" y1="23" x2="16" y2="23"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">WebRTC Audio</div>
            <div class="step-box-sub">16kHz PCM stream</div>
          </div>
        </div>

        <div class="step-arrow">&rarr;</div>

        <div class="step-box highlight-blue">
          <div class="step-box-icon">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#2563eb" stroke-width="2">
              <path d="M2 12h2M6 8v8M10 4v16M14 6v12M18 9v6M22 12h-2"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">Silero VAD</div>
            <div class="step-box-sub">latency &lt; 15ms</div>
          </div>
        </div>

        <div class="step-arrow">&rarr;</div>

        <div class="step-box">
          <div class="step-box-icon">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#64748b" stroke-width="2">
              <path d="M3 18v-6a9 9 0 0 1 18 0v6"/>
              <path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">Faster-Whisper</div>
            <div class="step-box-sub">Quantized int8 STT</div>
          </div>
        </div>

        <div class="step-arrow">&rarr;</div>

        <div class="step-box highlight-blue" id="node-streaming-llm">
          <div class="step-box-icon">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#2563eb" stroke-width="2">
              <circle cx="12" cy="12" r="3"/>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">Streaming LLM</div>
            <div class="step-box-sub">Token stream &bull; vLLM</div>
          </div>
        </div>

        <div class="step-arrow">&rarr;</div>

        <div class="step-box">
          <div class="step-box-icon">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#64748b" stroke-width="2">
              <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
              <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">Edge-TTS Chunks</div>
            <div class="step-box-sub">Voice audio synthesis</div>
          </div>
        </div>

        <div class="step-arrow">&rarr;</div>

        <div class="step-box alert" id="node-barge-in">
          <div class="step-box-icon">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#ef4444" stroke-width="2.5">
              <circle cx="12" cy="12" r="10"/>
              <line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">Barge-in Cancel</div>
            <div class="step-box-sub">Instant buffer flush</div>
          </div>
        </div>
      </div>
    </div>
  </div>


  <!-- =======================================================================
       3. MLOPS & GPU SERVING INFRASTRUCTURE (DASHED GREEN BOX)
       ======================================================================= -->
  <div class="section-lane mlops-lane-box" id="mlops-lane">
    <div class="lane-header">
      <div class="lane-title-badge green">MLOPS &amp; HIGH-THROUGHPUT GPU SERVING</div>
      <div class="lane-tech-stack">Kubeflow Pipelines &middot; MLflow Registry &middot; NVIDIA A10G/T4 &middot; vLLM PagedAttention &middot; TensorZero &middot; Redis Semantic Cache</div>
    </div>

    <!-- MLOPS ROW 1: ETA PREDICTION PIPELINE -->
    <div class="lane-row">
      <div class="lane-label-col">
        <div class="lane-num-badge green">5</div>
        <div class="lane-label-info">
          <div class="lane-row-title">DELIVERY ETA SLA</div>
          <div class="lane-row-sub">Continuous ML training</div>
        </div>
      </div>

      <div class="step-chain">
        <div class="step-box" id="node-fct-orders">
          <div class="step-box-icon">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#64748b" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2"/>
              <line x1="3" y1="9" x2="21" y2="9"/>
              <line x1="9" y1="3" x2="9" y2="21"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">FCT_ORDERS Features</div>
            <div class="step-box-sub">Snowflake Gold feature store</div>
          </div>
        </div>

        <div class="step-arrow">&rarr;</div>

        <div class="step-box highlight-green">
          <div class="step-box-icon">
            <!-- Kubeflow Logo -->
            <svg viewBox="0 0 24 24" width="20" height="20" fill="#007d9c">
              <path d="M12 2L3 7v10l9 5 9-5V7l-9-5zm0 2.2L18.8 8 12 11.8 5.2 8 12 4.2zM5 9.8l6 3.4v6.6l-6-3.3V9.8zm8 10V13.2l6-3.4v6.7l-6 3.5z"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">Kubeflow Pipeline</div>
            <div class="step-box-sub">XGBoost &bull; LightGBM HPO</div>
          </div>
        </div>

        <div class="step-arrow">&rarr;</div>

        <div class="step-box">
          <div class="step-box-icon">
            <!-- MLflow Logo -->
            <svg viewBox="0 0 24 24" width="20" height="20" fill="#0194E2">
              <path d="M3 18V6l6 6 6-6v12h-3V11l-3 3-3-3v7H3zm15-12h3v12h-3V6z"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">MLflow Registry</div>
            <div class="step-box-sub">Versioned models &bull; MAE &bull; SLA %</div>
          </div>
        </div>

        <div class="step-arrow">&rarr;</div>

        <div class="step-box highlight-green" id="node-eta-api">
          <div class="step-box-icon">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#059669" stroke-width="2">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">ETA Serving API</div>
            <div class="step-box-sub">Latency &lt; 20ms &bull; gRPC / REST</div>
          </div>
        </div>

        <div class="step-arrow">&rarr;</div>

        <div class="step-box">
          <div class="step-box-icon">
            <!-- Go Logo -->
            <svg viewBox="0 0 24 24" width="20" height="20" fill="#00ADD8">
              <path d="M1.5 8.5h4v7h-4zm5 0h4v7h-4zm5 0h4v7h-4zm5 0h4v7h-4z"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">Go Delivery Service</div>
            <div class="step-box-sub">Distributed Saga SLA Check</div>
          </div>
        </div>
      </div>
    </div>

    <!-- MLOPS ROW 2: GPU SERVING & LLMOPS -->
    <div class="lane-row">
      <div class="lane-label-col">
        <div class="lane-num-badge green">6</div>
        <div class="lane-label-info">
          <div class="lane-row-title">GPU SERVING (vLLM)</div>
          <div class="lane-row-sub">Tensor Parallel &bull; Cache</div>
        </div>
      </div>

      <div class="step-chain">
        <div class="step-box">
          <div class="step-box-icon">
            <!-- NVIDIA Logo -->
            <svg viewBox="0 0 24 24" width="22" height="22" fill="#76B900">
              <path d="M8.9 4.3c-2.4.5-4.5 1.8-6.1 3.7-1 1.2-1.7 2.6-2.1 4.1-.2.8-.2 1.8 0 2.6.5 2.1 1.7 4 3.4 5.3 1.9 1.4 4.2 2.1 6.5 1.9 1.8-.2 3.6-.9 5-2.1l-.8-1.1c-1.3 1-2.9 1.6-4.5 1.7-2.1.1-4.2-.6-5.8-1.9-1.4-1.2-2.3-2.8-2.7-4.6-.2-.8-.2-1.6 0-2.4.4-1.7 1.4-3.3 2.7-4.4 1.5-1.2 3.4-1.8 5.3-1.7 2 .1 3.9.9 5.3 2.3l1-1C14.7 5.1 11.8 4.1 8.9 4.3z"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">NVIDIA GPU Nodes</div>
            <div class="step-box-sub">Kubernetes A10G / T4 Spot</div>
          </div>
        </div>

        <div class="step-arrow">&rarr;</div>

        <div class="step-box highlight-green" id="node-vllm-engine">
          <div class="step-box-icon">
            <!-- vLLM Acceleration Logo -->
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#059669" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">vLLM Inference Engine</div>
            <div class="step-box-sub">PagedAttention &bull; TP=2</div>
          </div>
        </div>

        <div class="step-arrow">&rarr;</div>

        <div class="step-box">
          <div class="step-box-icon">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#64748b" stroke-width="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">TensorZero Gateway</div>
            <div class="step-box-sub">Dynamic Model Router &bull; Fallback</div>
          </div>
        </div>

        <div class="step-arrow">&rarr;</div>

        <div class="step-box highlight-green">
          <div class="step-box-icon">
            <!-- Redis Logo -->
            <svg viewBox="0 0 24 24" width="20" height="20" fill="#DC382D">
              <path d="M12 2L2 7l10 5 10-5-10-5zm0 9l-9-4.5V11l9 4.5 9-4.5V6.5L12 11zm0 5l-9-4.5V16l9 4.5 9-4.5v-4.5L12 16z"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">Redis Semantic Cache</div>
            <div class="step-box-sub">65% Cost &amp; Latency Reduction</div>
          </div>
        </div>

        <div class="step-arrow">&rarr;</div>

        <div class="step-box">
          <div class="step-box-icon">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#2563eb" stroke-width="2">
              <circle cx="12" cy="12" r="3"/>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">Voice &amp; RAG Feeds</div>
            <div class="step-box-sub">Sub-30ms TTFT Token Stream</div>
          </div>
        </div>
      </div>
    </div>
  </div>


  <!-- =======================================================================
       4. DEVOPS, GITOPS & ADVERSARIAL AI SECURITY (DASHED PURPLE BOX)
       ======================================================================= -->
  <div class="section-lane devops-lane-box" id="devops-lane">
    <div class="lane-header">
      <div class="lane-title-badge purple">DEVOPS, GITOPS &amp; ADVERSARIAL AI SECURITY</div>
      <div class="lane-tech-stack">Terraform Multi-Cloud &middot; ArgoCD Continuous Sync &middot; SonarQube Gate &middot; Trivy CVE &middot; Microsoft PyRIT Red Team</div>
    </div>

    <!-- DEVOPS ROW 1: GITOPS & MULTI-CLOUD -->
    <div class="lane-row">
      <div class="lane-label-col">
        <div class="lane-num-badge purple">7</div>
        <div class="lane-label-info">
          <div class="lane-row-title">MULTI-CLOUD GITOPS</div>
          <div class="lane-row-sub">Terraform &bull; ArgoCD sync</div>
        </div>
      </div>

      <div class="step-chain">
        <div class="step-box highlight-purple">
          <div class="step-box-icon">
            <!-- Terraform Logo -->
            <svg viewBox="0 0 24 24" width="20" height="20" fill="#7B42BC">
              <path d="M1.5 2h6.5v6.5H1.5zm7.5 7.5h6.5V16H9zm0-7.5h6.5v6.5H9zm7.5 7.5H23V16h-6.5zM9 16.5h6.5V23H9z"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">Terraform Multi-Cloud</div>
            <div class="step-box-sub">AWS EKS &bull; GCP GKE &bull; Azure AKS</div>
          </div>
        </div>

        <div class="step-arrow">&rarr;</div>

        <div class="step-box highlight-purple">
          <div class="step-box-icon">
            <!-- ArgoCD Logo -->
            <svg viewBox="0 0 24 24" width="20" height="20" fill="#EF7B4D">
              <circle cx="12" cy="12" r="10" fill="none" stroke="#EF7B4D" stroke-width="2"/>
              <circle cx="12" cy="12" r="4" fill="#00ADEE"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">ArgoCD Continuous Sync</div>
            <div class="step-box-sub">Automated cluster drift defense</div>
          </div>
        </div>

        <div class="step-arrow">&rarr;</div>

        <div class="step-box">
          <div class="step-box-icon">
            <!-- Kubernetes Logo -->
            <svg viewBox="0 0 24 24" width="20" height="20" fill="#326CE5">
              <path d="M12 2l8.66 5v10L12 22l-8.66-5V7L12 2zm0 2.31L5.34 7.85v8.3L12 19.69l6.66-3.54v-8.3L12 4.31zM12 7a5 5 0 1 1 0 10 5 5 0 0 1 0-10z"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">Kubernetes Mesh (Istio)</div>
            <div class="step-box-sub">mTLS &bull; Canary 90/10 traffic splits</div>
          </div>
        </div>

        <div class="step-arrow">&rarr;</div>

        <div class="step-box">
          <div class="step-box-icon">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#16a34a" stroke-width="2">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">Active-Active Resilience</div>
            <div class="step-box-sub">RTO &lt; 30s &bull; RPO &lt; 1s Failover</div>
          </div>
        </div>
      </div>
    </div>

    <!-- DEVOPS ROW 2: DEVSECOPS & PYRIT RED TEAMING -->
    <div class="lane-row">
      <div class="lane-label-col">
        <div class="lane-num-badge purple">8</div>
        <div class="lane-label-info">
          <div class="lane-row-title">DEVSECOPS &amp; PYRIT</div>
          <div class="lane-row-sub">Quality &bull; AI Red Team</div>
        </div>
      </div>

      <div class="step-chain">
        <div class="step-box">
          <div class="step-box-icon">
            <!-- SonarQube Logo -->
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#4B9CD3" stroke-width="2.2" stroke-linecap="round">
              <path d="M2 12c0-5.5 4.5-10 10-10s10 4.5 10 10"/>
              <path d="M6 12c0-3.3 2.7-6 6-6s6 2.7 6 6"/>
              <circle cx="12" cy="12" r="2" fill="#CB333B"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">SonarQube Quality Gate</div>
            <div class="step-box-sub">&gt;80% coverage &bull; 0 vulnerabilities</div>
          </div>
        </div>

        <div class="step-arrow">&rarr;</div>

        <div class="step-box">
          <div class="step-box-icon">
            <!-- Trivy Logo -->
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#19A8B6" stroke-width="2">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">Nexus &amp; Trivy Scan</div>
            <div class="step-box-sub">Container CVEs &bull; SBOM attestation</div>
          </div>
        </div>

        <div class="step-arrow">&rarr;</div>

        <div class="step-box highlight-purple">
          <div class="step-box-icon">
            <!-- PyRIT AI Red Team Logo -->
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#E11D48" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="2" x2="12" y2="6"/>
              <line x1="12" y1="18" x2="12" y2="22"/>
              <line x1="2" y1="12" x2="6" y2="12"/>
              <line x1="18" y1="12" x2="22" y2="12"/>
              <circle cx="12" cy="12" r="3" fill="#E11D48"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">Microsoft PyRIT Red Team</div>
            <div class="step-box-sub">Jailbreak &bull; Injection Evasion = 0.0%</div>
          </div>
        </div>

        <div class="step-arrow">&rarr;</div>

        <div class="step-box">
          <div class="step-box-icon">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#16a34a" stroke-width="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              <polyline points="9 12 11 14 15 10"/>
            </svg>
          </div>
          <div class="step-box-content">
            <div class="step-box-title">Zero-Trust Deploy Gate</div>
            <div class="step-box-sub">Cosign signed &bull; Automated release</div>
          </div>
        </div>
      </div>
    </div>
  </div>


  <!-- =======================================================================
       5. ORCHESTRATION LANE (APACHE AIRFLOW)
       ======================================================================= -->
  <div class="orchestration-container" id="orchestration">
    <div class="orchestration-brand-card">
      <svg class="orchestration-brand-icon" viewBox="0 0 100 100">
        <path d="M50 50 L50 10 A40 40 0 0 1 90 50 Z" fill="#017CEE"/>
        <path d="M50 50 L90 50 A40 40 0 0 1 50 90 Z" fill="#00D084"/>
        <path d="M50 50 L50 90 A40 40 0 0 1 10 50 Z" fill="#FF5A5F"/>
        <path d="M50 50 L10 50 A40 40 0 0 1 50 10 Z" fill="#00ADEE"/>
        <circle cx="50" cy="50" r="12" fill="#ffffff"/>
      </svg>
      <div class="orchestration-brand-info">
        <div class="orchestration-brand-tag">ORCHESTRATION</div>
        <div class="orchestration-brand-name">Apache Airflow</div>
        <div class="orchestration-brand-dag">DAGs (zomato_batch)</div>
      </div>
    </div>

    <div class="orchestration-chain">
      <!-- Task 1: upload_raw -->
      <div class="orch-task-box" id="task-upload-raw">
        <div class="orch-task-icon">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="#16a34a" stroke-width="2">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
          </svg>
        </div>
        <div class="orch-task-text">
          <div class="orch-task-title">upload_raw</div>
          <div class="orch-task-sub">S3 &rarr; RAW (COPY)</div>
        </div>
      </div>

      <div class="step-arrow">&rarr;</div>

      <!-- Task 2: dbt_build_core -->
      <div class="orch-task-box" id="task-dbt-core">
        <div class="orch-task-icon">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="#16a34a" stroke-width="2">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
          </svg>
        </div>
        <div class="orch-task-text">
          <div class="orch-task-title">dbt_build_core</div>
          <div class="orch-task-sub">RAW &rarr; STAGING</div>
        </div>
      </div>

      <div class="step-arrow">&rarr;</div>

      <!-- Task 3: enrich_reviews -->
      <div class="orch-task-box purple" id="task-enrich">
        <div class="orch-task-icon">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="#a855f7" stroke-width="2">
            <path d="M12 2a4 4 0 0 0-4 4v1a4 4 0 0 0-4 4 4 4 0 0 0 4 4v1a4 4 0 0 0 4 4 4 4 0 0 0 4-4v-1a4 4 0 0 0 4-4 4 4 0 0 0-4-4V6a4 4 0 0 0-4-4z"/>
          </svg>
        </div>
        <div class="orch-task-text">
          <div class="orch-task-title" style="color:#7e22ce;">enrich_reviews</div>
          <div class="orch-task-sub">AI Review Enrichment</div>
        </div>
      </div>

      <div class="step-arrow">&rarr;</div>

      <!-- Task 4: dbt_build_all -->
      <div class="orch-task-box purple" id="task-dbt-all">
        <div class="orch-task-icon">
          <svg viewBox="0 0 24 24" width="18" height="18">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="#a855f7"/>
            <path d="M2 17L12 22L22 17V12L12 17L2 12V17Z" fill="#7e22ce"/>
          </svg>
        </div>
        <div class="orch-task-text">
          <div class="orch-task-title" style="color:#7e22ce;">dbt_build_all</div>
          <div class="orch-task-sub">AI &rarr; MARTS Incremental</div>
        </div>
      </div>

      <div class="step-arrow">&rarr;</div>

      <!-- Task 5: ml_predict_eta -->
      <div class="orch-task-box blue" id="task-ml-eta">
        <div class="orch-task-icon">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="#2563eb" stroke-width="2">
            <rect x="2" y="3" width="20" height="14" rx="2"/>
            <line x1="8" y1="21" x2="16" y2="21"/>
            <line x1="12" y1="17" x2="12" y2="21"/>
          </svg>
        </div>
        <div class="orch-task-text">
          <div class="orch-task-title" style="color:#1d4ed8;">ml_predict_eta</div>
          <div class="orch-task-sub">Kubeflow Trigger</div>
        </div>
      </div>

      <div class="step-arrow">&rarr;</div>

      <!-- Task 6: n8n_alert_trigger -->
      <div class="orch-task-box orange" id="task-n8n">
        <div class="orch-task-icon">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="#f97316">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
          </svg>
        </div>
        <div class="orch-task-text">
          <div class="orch-task-title" style="color:#c2410c;">n8n_alert_trigger</div>
          <div class="orch-task-sub">Auto Slack &amp; Ops</div>
        </div>
      </div>
    </div>
  </div>


  <!-- =======================================================================
       6. FOUNDATION & TOOLS & SECURITY BAR
       ======================================================================= -->
  <div class="footer-bar">
    <div class="foundation-col">
      <div class="foundation-label">FOUNDATION &amp; TOOLS</div>

      <div class="tech-badges-list">
        <!-- Python -->
        <div class="tech-item">
          <svg viewBox="0 0 110 110">
            <path d="M54 2C32 2 33 11 33 11L33 21L55 21L55 24L24 24C12 24 2 28 2 46C2 63 10 65 17 65L24 65L24 55C24 43 33 43 33 43L55 43C65 43 65 33 65 33L65 12C65 12 66 2 54 2Z" fill="#366A96"/>
            <path d="M56 108C78 108 77 99 77 99L77 89L55 89L55 86L86 86C98 86 108 82 108 64C108 47 100 45 93 45L86 45L86 55C86 67 77 67 77 67L55 67C45 67 45 77 45 77L45 98C45 98 44 108 56 108Z" fill="#FFD43B"/>
            <circle cx="43" cy="11" r="3.5" fill="#ffffff"/>
            <circle cx="67" cy="99" r="3.5" fill="#ffffff"/>
          </svg>
          Python
        </div>

        <!-- Pandas -->
        <div class="tech-item">
          <svg viewBox="0 0 100 100">
            <rect x="20" y="20" width="14" height="60" rx="3" fill="#130654"/>
            <rect x="43" y="35" width="14" height="45" rx="3" fill="#FF4A00"/>
            <rect x="66" y="10" width="14" height="70" rx="3" fill="#4B9CD3"/>
          </svg>
          Pandas
        </div>

        <!-- Snowflake -->
        <div class="tech-item">
          <svg viewBox="0 0 100 100">
            <g stroke="#29B5E8" stroke-width="7" stroke-linecap="round">
              <line x1="50" y1="14" x2="50" y2="86"/>
              <line x1="14" y1="50" x2="86" y2="50"/>
              <line x1="24.5" y1="24.5" x2="75.5" y2="75.5"/>
              <line x1="24.5" y1="75.5" x2="75.5" y2="24.5"/>
            </g>
          </svg>
          Snowflake
        </div>

        <!-- dbt -->
        <div class="tech-item">
          <svg viewBox="0 0 24 24">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="#FF694B"/>
            <path d="M2 17L12 22L22 17V12L12 17L2 12V17Z" fill="#E04E31"/>
          </svg>
          dbt
        </div>

        <!-- OpenAI -->
        <div class="tech-item">
          <svg viewBox="0 0 24 24" fill="none" stroke="#000000" stroke-width="2">
            <path d="M12 2a10 10 0 0 1 10 10 10 10 0 0 1-10 10A10 10 0 0 1 2 12 10 10 0 0 1 12 2z"/>
            <circle cx="12" cy="12" r="4"/>
          </svg>
          OpenAI
        </div>

        <!-- Next.js 16+ -->
        <div class="tech-item">
          <svg viewBox="0 0 180 180">
            <circle cx="90" cy="90" r="85" fill="#000000"/>
            <path d="M149.5 163.5L67.5 56H52V124H63.5V72.5L138 168.5Z" fill="#ffffff"/>
            <path d="M117 56H128.5V106.5L117 92V56Z" fill="#ffffff"/>
          </svg>
          Next.js 16+
        </div>

        <!-- Go -->
        <div class="tech-item">
          <svg viewBox="0 0 24 24" fill="#00ADD8">
            <path d="M1.5 8.5h4v7h-4zm5 0h4v7h-4zm5 0h4v7h-4zm5 0h4v7h-4z"/>
          </svg>
          Go 1.24
        </div>

        <!-- Kafka -->
        <div class="tech-item">
          <svg viewBox="0 0 24 24" fill="#000000">
            <circle cx="12" cy="12" r="3"/>
            <path d="M12 2a10 10 0 0 0-7.07 2.93l2.12 2.12A7 7 0 0 1 12 5zM22 12a10 10 0 0 0-2.93-7.07l-2.12 2.12A7 7 0 0 1 19 12zM12 22a10 10 0 0 0 7.07-2.93l-2.12-2.12A7 7 0 0 1 12 19z"/>
          </svg>
          Kafka
        </div>

        <!-- Redis -->
        <div class="tech-item">
          <svg viewBox="0 0 24 24" fill="#DC382D">
            <path d="M12 2L2 7l10 5 10-5-10-5zm0 9l-9-4.5V11l9 4.5 9-4.5V6.5L12 11zm0 5l-9-4.5V16l9 4.5 9-4.5v-4.5L12 16z"/>
          </svg>
          Redis
        </div>

        <!-- NVIDIA -->
        <div class="tech-item">
          <svg viewBox="0 0 24 24" fill="#76B900">
            <path d="M8.9 4.3c-2.4.5-4.5 1.8-6.1 3.7-1 1.2-1.7 2.6-2.1 4.1-.2.8-.2 1.8 0 2.6.5 2.1 1.7 4 3.4 5.3 1.9 1.4 4.2 2.1 6.5 1.9 1.8-.2 3.6-.9 5-2.1l-.8-1.1c-1.3 1-2.9 1.6-4.5 1.7-2.1.1-4.2-.6-5.8-1.9-1.4-1.2-2.3-2.8-2.7-4.6-.2-.8-.2-1.6 0-2.4.4-1.7 1.4-3.3 2.7-4.4 1.5-1.2 3.4-1.8 5.3-1.7 2 .1 3.9.9 5.3 2.3l1-1C14.7 5.1 11.8 4.1 8.9 4.3z"/>
          </svg>
          NVIDIA
        </div>

        <!-- Kubeflow -->
        <div class="tech-item">
          <svg viewBox="0 0 24 24" fill="#007d9c">
            <path d="M12 2L3 7v10l9 5 9-5V7l-9-5zm0 2.2L18.8 8 12 11.8 5.2 8 12 4.2zM5 9.8l6 3.4v6.6l-6-3.3V9.8zm8 10V13.2l6-3.4v6.7l-6 3.5z"/>
          </svg>
          Kubeflow
        </div>

        <!-- MLflow -->
        <div class="tech-item">
          <svg viewBox="0 0 24 24" fill="#0194E2">
            <path d="M3 18V6l6 6 6-6v12h-3V11l-3 3-3-3v7H3zm15-12h3v12h-3V6z"/>
          </svg>
          MLflow
        </div>

        <!-- Terraform -->
        <div class="tech-item">
          <svg viewBox="0 0 24 24" fill="#7B42BC">
            <path d="M1.5 2h6.5v6.5H1.5zm7.5 7.5h6.5V16H9zm0-7.5h6.5v6.5H9zm7.5 7.5H23V16h-6.5zM9 16.5h6.5V23H9z"/>
          </svg>
          Terraform
        </div>

        <!-- ArgoCD -->
        <div class="tech-item">
          <svg viewBox="0 0 24 24" fill="#EF7B4D">
            <circle cx="12" cy="12" r="10" fill="none" stroke="#EF7B4D" stroke-width="2"/>
            <circle cx="12" cy="12" r="4" fill="#00ADEE"/>
          </svg>
          ArgoCD
        </div>

        <!-- SonarQube -->
        <div class="tech-item">
          <svg viewBox="0 0 24 24" fill="none" stroke="#4B9CD3" stroke-width="2.2">
            <path d="M2 12c0-5.5 4.5-10 10-10s10 4.5 10 10"/>
            <circle cx="12" cy="12" r="2" fill="#CB333B"/>
          </svg>
          SonarQube
        </div>

        <!-- PyRIT -->
        <div class="tech-item">
          <svg viewBox="0 0 24 24" fill="none" stroke="#E11D48" stroke-width="2.2">
            <circle cx="12" cy="12" r="10"/>
            <circle cx="12" cy="12" r="3" fill="#E11D48"/>
          </svg>
          PyRIT Red Team
        </div>
      </div>
    </div>

    <!-- Security Column -->
    <div class="security-box">
      <svg class="security-icon" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
        <rect x="9" y="9" width="6" height="5" rx="1" fill="#16a34a"/>
        <path d="M10 9V7a2 2 0 0 1 4 0v2"/>
      </svg>
      <div class="security-info">
        <div class="security-title">Security &amp; Governance</div>
        <div class="security-sub">IAM STS &bull; KMS &bull; Warehouse Network Policies &bull; AST Guard &bull; PyRIT</div>
      </div>
    </div>
  </div>


  <!-- =======================================================================
       7. DYNAMIC SVG DASHED CONNECTOR ARROWS OVERLAY
       ======================================================================= -->
  <svg class="connector-overlay" id="svg-connectors">
    <defs>
      <!-- Blue Arrowhead Marker -->
      <marker id="arrow-blue" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#2563eb"/>
      </marker>
      <!-- Green Arrowhead Marker -->
      <marker id="arrow-green" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#059669"/>
      </marker>
      <!-- Purple Arrowhead Marker -->
      <marker id="arrow-purple" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#7c3aed"/>
      </marker>
    </defs>
  </svg>

  <script>
    // Dynamically calculate and inject SVG dashed connector lines with pixel precision
    window.addEventListener('DOMContentLoaded', () => {
      const svg = document.getElementById('svg-connectors');

      function getCenter(el) {
        const r = el.getBoundingClientRect();
        return {
          x: r.left + r.width / 2,
          y: r.top + r.height / 2,
          top: r.top,
          bottom: r.bottom,
          left: r.left,
          right: r.right
        };
      }

      function createPath(d, color = '#2563eb', marker = 'arrow-blue') {
        const p = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        p.setAttribute('d', d);
        p.setAttribute('stroke', color);
        p.setAttribute('stroke-width', '2');
        p.setAttribute('stroke-dasharray', '5,4');
        p.setAttribute('fill', 'none');
        p.setAttribute('marker-end', `url(#${marker})`);
        svg.appendChild(p);
      }

      const aiLane = document.getElementById('ai-lane');
      const aiRect = aiLane.getBoundingClientRect();
      const cardSilver = document.getElementById('card-silver');
      const cardGold = document.getElementById('card-gold');
      const cardServe = document.getElementById('card-serve');

      // 1. Top border of AI Lane UP into SILVER (STAGING dbt)
      if (cardSilver) {
        const c = getCenter(cardSilver);
        createPath(`M ${c.x} ${aiRect.top} L ${c.x} ${c.bottom + 2}`);
      }

      // 2. Top border of AI Lane UP into GOLD (MARTS dbt)
      if (cardGold) {
        const c = getCenter(cardGold);
        createPath(`M ${c.x} ${aiRect.top} L ${c.x} ${c.bottom + 2}`);
      }

      // 3. mart_review_insights (Capability 1) CURVED UP-RIGHT directly to SERVE (CARD 6)
      const nodeInsights = document.getElementById('node-review-insights');
      if (nodeInsights && cardServe) {
        const cIns = getCenter(nodeInsights);
        const cServe = getCenter(cardServe);
        const startX = cIns.right + 4;
        const startY = cIns.y;
        const endX = cServe.left + 50;
        const endY = cServe.bottom + 2;
        createPath(`M ${startX} ${startY} C ${startX + 80} ${startY}, ${endX - 30} ${startY - 40}, ${endX} ${endY}`);
      }

      // 4. rag_chat (Capability 2) CURVED UP-RIGHT directly to SERVE (CARD 6)
      const nodeRag = document.getElementById('node-rag-chat');
      if (nodeRag && cardServe) {
        const cRag = getCenter(nodeRag);
        const cServe = getCenter(cardServe);
        const startX = cRag.right + 4;
        const startY = cRag.y;
        const endX = cServe.left + 110;
        const endY = cServe.bottom + 2;
        createPath(`M ${startX} ${startY} C ${startX + 110} ${startY}, ${endX - 30} ${startY - 60}, ${endX} ${endY}`);
      }

      // 5. GOLD (MARTS dbt) straight DOWN to FCT_ORDERS in MLOps Lane
      const nodeFct = document.getElementById('node-fct-orders');
      if (cardGold && nodeFct) {
        const cGold = getCenter(cardGold);
        const cFct = getCenter(nodeFct);
        createPath(`M ${cGold.x} ${aiRect.bottom} L ${cGold.x} ${cFct.top - 2}`, '#059669', 'arrow-green');
      }

      // 6. vLLM Engine in MLOps curved UP into Streaming LLM in AI Lane
      const nodeVllm = document.getElementById('node-vllm-engine');
      const nodeStreaming = document.getElementById('node-streaming-llm');
      if (nodeVllm && nodeStreaming) {
        const cVllm = getCenter(nodeVllm);
        const cStream = getCenter(nodeStreaming);
        createPath(`M ${cVllm.x + 30} ${cVllm.top} C ${cVllm.x + 30} ${cVllm.top - 30}, ${cStream.x} ${cStream.bottom + 30}, ${cStream.x} ${cStream.bottom + 2}`, '#059669', 'arrow-green');
      }

      // 7. ETA Serving API in MLOps curved UP-RIGHT into SERVE
      const nodeEta = document.getElementById('node-eta-api');
      if (nodeEta && cardServe) {
        const cEta = getCenter(nodeEta);
        const cServe = getCenter(cardServe);
        const startX = cEta.right + 4;
        const startY = cEta.y;
        const endX = cServe.right - 40;
        const endY = cServe.bottom + 2;
        createPath(`M ${startX} ${startY} C ${startX + 140} ${startY}, ${endX + 30} ${startY - 120}, ${endX} ${endY}`, '#059669', 'arrow-green');
      }

      // 8. Airflow upload_raw UP to bottom of DevOps lane
      const devopsLane = document.getElementById('devops-lane');
      const devopsRect = devopsLane.getBoundingClientRect();
      const tUpload = document.getElementById('task-upload-raw');
      if (tUpload) {
        const c = getCenter(tUpload);
        createPath(`M ${c.x} ${c.top} L ${c.x} ${devopsRect.bottom + 2}`);
      }

      // 9. Airflow dbt_build_core UP to bottom of DevOps lane
      const tCore = document.getElementById('task-dbt-core');
      if (tCore) {
        const c = getCenter(tCore);
        createPath(`M ${c.x} ${c.top} L ${c.x} ${devopsRect.bottom + 2}`);
      }

      // 10. Airflow enrich_reviews UP
      const tEnrich = document.getElementById('task-enrich');
      if (tEnrich) {
        const c = getCenter(tEnrich);
        createPath(`M ${c.x} ${c.top} L ${c.x} ${devopsRect.bottom + 2}`);
      }

      // 11. Airflow dbt_build_all UP
      const tAll = document.getElementById('task-dbt-all');
      if (tAll) {
        const c = getCenter(tAll);
        createPath(`M ${c.x} ${c.top} L ${c.x} ${devopsRect.bottom + 2}`);
      }
    });
  </script>

</body>
</html>
'''

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    html_path = os.path.join(script_dir, "render_design.html")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(HTML_TEMPLATE)
    print(f"Written HTML template to {html_path}")

    out_paths = [
        os.path.join(project_dir, "design.png"),
        os.path.join(project_dir, "docs", "design.png")
    ]

    chrome_cmd = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "--headless",
        "--disable-gpu",
        "--hide-scrollbars",
        "--virtual-time-budget=2000",
        "--force-device-scale-factor=2",
        "--window-size=2200,1440",
        f"--screenshot={out_paths[0]}",
        f"file://{html_path}"
    ]

    print("Running Google Chrome headless to render retina design.png with DevOps + MLOps + GPU Serving...")
    res = subprocess.run(chrome_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error rendering Chrome: {res.stderr}")
        return

    shutil.copy2(out_paths[0], out_paths[1])
    print(f"Successfully generated retina design.png at:\n  - {out_paths[0]}\n  - {out_paths[1]}")

if __name__ == "__main__":
    main()
