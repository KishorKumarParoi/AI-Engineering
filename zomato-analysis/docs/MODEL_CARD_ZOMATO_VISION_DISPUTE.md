# Model Card: Zomato Autonomous Vision & Customer Dispute AI

## 1. Model Details & Scope
- **Model Name**: Zomato Multimodal Vision Dispute & Fraud Settlement Engine
- **Version**: 2.1.0-prod
- **Architecture**: Qwen-2.5-VL / Gemini 1.5 Flash Vision + Dual-Tier Policy RAG
- **Release Date**: 2026-10-23
- **Primary Domain**: Autonomous customer refund verification, missing item validation, food spill detection.

---

## 2. Intended Applications & Ethical Bounds
- **Authorized Use**:
  - Validating user-submitted meal photographs against merchant receipts.
  - Verifying spilled packaging, burnt food, or missing items.
  - Issuing automated micro-refunds (< ₹1,500 INR) within 60 seconds.
- **Prohibited & Out-of-Scope Use**:
  - Processing photos containing human faces or identity documents (automatically dropped by PII filters).
  - Unilateral account blacklisting without human fraud operations review.

---

## 3. Evaluation & Quality Metrics
Audited across 5,000 real-world customer dispute cases:
- **G-Eval Groundedness to Refund Policy**: **0.940 / 1.00**
- **Dispute Settlement Fairness Score**: **0.920 / 1.00**
- **Fraud Precision**: **94.8%** (False Positive Rate < 2.1%)
- **End-to-End P95 Processing Latency**: **2.80 Seconds**
- **Financial Savings**: Cut manual customer support operational tickets by **42%**.
