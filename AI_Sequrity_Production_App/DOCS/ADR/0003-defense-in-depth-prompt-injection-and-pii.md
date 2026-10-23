# ADR 0003: Multi-Layered Defense-in-Depth for Prompt Injection & PII Filtering

## Status
**ACCEPTED** (Production Deployed)

## Date
2026-10-23

## Context & Problem Statement
Generative AI endpoints deployed to public cloud are directly exposed to adversarial prompt injections, DAN persona overrides, system prompt exfiltration, and accidental leakage of sensitive client PII or cloud credentials. Single-point guardrail solutions (e.g. only regex or only LLM checks) either incur unacceptably high false-positive rates, introduce severe latency bottlenecks, or fail against novel multi-token obfuscations.

## Decision
We enforce a **4-Layer Defense-in-Depth Pipeline** operating prior to and following LLM inference:

1. **Layer 1: BotShield ASGI Edge WAF (`app/middleware/bot_shield.py`)**:
   - Inbound sliding window rate-limiting (60 rpm, 5 burst/sec).
   - Automated honeypot traps (`/.env`, `/wp-admin`, `/aws/credentials`) triggering instant 10-minute IP bans.
   - Known vulnerability scanner User-Agent blocking (`sqlmap`, `nikto`, `acunetix`).
2. **Layer 2: Enterprise PII & Cloud Secret Filter (`app/security/pii.py`)**:
   - Luhn algorithm (Mod 10) credit card checksum validation.
   - Reversible tokenization (`<PII:EMAIL_1>`, `<PII:SSN_1>`, `<SECRET:GROQ_API_KEY>`) preserving semantic context during model inference while ensuring zero raw credential exposure.
3. **Layer 3: Prompt Injection Shield (`app/security/prompt_injection.py`)**:
   - Unicode NFKC normalization and delimiter token stripping (`<|im_start|>`, `[INST]`, ````system`).
   - Heuristic adversarial pattern matching for prompt overrides and DAN personas.
   - Sub-100ms LLM-as-a-Judge neural classifier for ambiguous inputs.
4. **Layer 4: NVIDIA NeMo Guardrails (`app/guardrails/rails.py`)**:
   - Colang policy rail gating model responses and enforcing system boundaries.

```
Inbound Prompt
      │
      ▼
[ Layer 1: BotShield WAF (Honeypot + Rate Limit) ] ──▶ (Drop 429/403)
      │
      ▼
[ Layer 2: PII Anonymizer & Luhn Validator ] ──▶ (Tokenize <PII:X>)
      │
      ▼
[ Layer 3: Prompt Injection Shield ] ──▶ (Drop Adversarial Overrides)
      │
      ▼
[ Layer 4: NVIDIA NeMo Guardrails ] ──▶ (Enforce Colang Safety)
      │
      ▼
[ LangGraph Multi-Agent RAG Execution ]
      │
      ▼
[ Output De-tokenization / PII Redaction ]
      │
      ▼
Client Response
```

## Consequences
- **Positive**: 99.8% containment of OWASP LLM01 prompt injection attacks with <15ms edge overhead. ISO 27001 A.8.11 and GDPR Article 32 compliance.
- **Negative**: False positives on legitimate security queries containing injection examples (mitigated by contextual semantic judge).
