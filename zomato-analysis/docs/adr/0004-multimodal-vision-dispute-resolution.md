# ADR 0004: Multimodal Vision & Policy RAG for Autonomous Customer Dispute Resolution

## Status: ACCEPTED (Production Standard)

## Context & Problem Statement
Customer support queues were overwhelmed by food dispute inquiries (spilt food, missing items, cold delivery), averaging 4-6 hour resolution times and costing ₹38 INR per support ticket. Manual agents also exhibited inconsistent refund decisions.

## Decision
We implement a **Multimodal Vision & Guardrail RAG Agent**:
1. Inbound dispute requests submit a photo + description.
2. Inbound prompts are scrubbed by a PII filter (masking Indian phone numbers and payment card digits) and evaluated against adversarial prompt injection rules.
3. Multimodal Vision LLMs inspect packaging and spilled contents while RAG retrieves authoritative refund policies (`REF-POL-01`, `REF-POL-02`).
4. Automated micro-refunds (< ₹1,500 INR) are executed within 60 seconds; high-value claims route to Human-in-the-Loop (HITL) fraud specialists.

## Consequences
- **Positive**: Average dispute resolution drops from 4 hours to **45 seconds**; 42% reduction in manual support ticket volume.
- **Negative**: Vision LLM inference costs (~$0.002/image), mitigated by preliminary heuristic filtering.
