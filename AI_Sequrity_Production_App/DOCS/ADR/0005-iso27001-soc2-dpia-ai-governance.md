# ADR 0005: Enterprise ISO 27001, SOC 2 Type II, and DPIA Governance Architecture

## Status
**ACCEPTED** (Production Deployed)

## Date
2026-10-23

## Context & Problem Statement
Deploying autonomous agentic AI in enterprise regulated environments requires adherence to international compliance frameworks (ISO/IEC 27001:2022, SOC 2 Type II Trust Services Criteria, and NIST AI RMF 1.0). In addition, European GDPR Article 35 mandates a formal Data Protection Impact Assessment (DPIA) whenever AI pipelines process personal or sensitive customer records. Compliance cannot remain static paper documentation—it must be continuously verifiable in the runtime codebase.

## Decision
We implement a programmatic **Compliance Verification & DPIA Engine**:

1. **Formal Control Mapping**:
   - Programmatic verification of 14 technical controls across ISO 27001 (A.5.8, A.8.7, A.8.11, A.8.16, A.8.24, A.8.28), SOC 2 Type II (CC6.1, CC6.6, CC6.7, CC7.2, CC8.1), and NIST AI RMF (GOVERN, MAP, MEASURE, MANAGE).
   - Live endpoint `GET /api/v1/compliance/audit` auditing implementation status, component mapping, and evidence links in real-time.
2. **Automated DPIA Generator**:
   - Generates regulatory-grade assessment reports (`GET /api/v1/compliance/dpia`) evaluating lawful basis (GDPR Art. 6), data minimization (PII tokenization), risk assessment matrix, and DPO sign-off recommendations.
3. **Cryptographic Human-in-the-Loop (HITL) Gate**:
   - High-impact tool executions (e.g. system firewall rule updates) pause the agent graph in an interrupted state until authorized by a signed admin approval.

## Consequences
- **Positive**: Satisfies enterprise security questionnaires and auditor reviews automatically; minimizes compliance drift.
- **Negative**: Adds governance maintenance overhead when modifying existing tool schemas.
