# ⚖️ Enterprise Compliance Mapping (ISO 27001, SOC 2) & DPIA for Zomato Platform

## 1. Regulatory Context
The Zomato AI & Streaming Data Platform processes consumer food orders, real-time GPS delivery coordinates, mobile telephone numbers, and UPI transaction metadata across 500+ Indian cities. Compliance is governed by:
- **Digital Personal Data Protection Act (DPDP Act, India 2023)**
- **ISO/IEC 27001:2022** (Information Security Management)
- **SOC 2 Type II** (Security, Availability, and Confidentiality)
- **GDPR Article 35** (Data Protection Impact Assessment)

---

## 2. Technical Control Mapping Matrix

| Control ID | Framework | Control Objective | Implemented Technical Safeguard | Component Verification |
| :--- | :--- | :--- | :--- | :--- |
| **A.8.11** | ISO 27001 | Data Masking & PII Redaction | Automated phone & payment masking before lakehouse ingestion | `ai/dispute_rag_service.py` |
| **A.8.24** | ISO 27001 | Cryptography & KMS | AWS KMS Customer-Managed Keys (CMK) for S3 Delta Lake & MSK | `terraform/aws/main.tf` |
| **A.8.28** | ISO 27001 | Secure Coding & AI Defenses | Prompt Injection Shield & delimiter neutralization | `ai/dispute_rag_service.py` |
| **CC6.1** | SOC 2 | Access Control & Least Privilege | AWS IAM Role-based EKS Service Account permissions (IRSA) | `terraform/aws/main.tf` |
| **CC6.6** | SOC 2 | Boundary Defense & DoS | Rate-limiting and WAF honeypots dropping automated scrapers | `app/middleware/bot_shield.py` |
| **CC7.2** | SOC 2 | Continuous Monitoring & Drift | Population Stability Index (PSI) & KS-test feature drift alerts | `monitoring/drift_detector.py` |
| **CC8.1** | SOC 2 | Change Control & Rollbacks | Argo Rollouts Canary testing with automated rollback triggers | `k8s/canary-rollout.yaml` |

---

## 3. Data Protection Impact Assessment (DPIA)

### Assessment ID: `DPIA-2026-ZOMATO-CORE-01`
- **Data Controller**: Zomato AI Architecture Group
- **DPO Status**: **APPROVED FOR PRODUCTION**
- **Lawful Basis**: Contractual Performance (Order fulfillment & delivery) + Explicit Consent

### Risk Assessment & Mitigation Table
1. **Risk 1: Driver or Customer Phone Number Exfiltration**:
   - *Pre-Mitigation*: High Severity, High Likelihood.
   - *Mitigation*: Virtual number masking via telephony proxy; regex PII tokenizer in RAG.
   - *Residual Risk*: **LOW**.
2. **Risk 2: GPS Geolocation Tracking Abuse**:
   - *Pre-Mitigation*: High Severity, Medium Likelihood.
   - *Mitigation*: GPS points truncated to 3 decimal places (~100m radius) in analytical lakehouse Gold tables.
   - *Residual Risk*: **LOW**.
3. **Risk 3: Fraudulent Dispute System Abuse**:
   - *Pre-Mitigation*: Medium Severity, High Likelihood.
   - *Mitigation*: G-Eval groundedness verification + Feast customer fraud risk feature views.
   - *Residual Risk*: **NEGLIGIBLE**.
