# Operational Runbook: Latency & Cost Spike Mitigation (RUNBOOK-02)

## Severity Level: SEV-3 / MEDIUM
**Target Systems**: Groq Cloud, Portkey Gateway, Cohere Re-rank, FastAPI Uvicorn Server

---

## 1. Trigger Conditions & Detection
- Alert `LatencySLOBreach`: P95 latency > 2,000ms over a 5-minute rolling window.
- Alert `CostSpikeHourly`: Hourly spend rate exceeds $5.00/hour.
- Groq Cloud HTTP 429 (`Rate limit reached for model llama-3.3-70b-versatile in organization`).

---

## 2. Immediate Diagnostic Checks (< 3 Minutes)
1. Query live system metrics endpoint:
   ```bash
   curl -s http://localhost:8080/metrics/summary | jq '.latency_slo, .overview'
   ```
2. Verify Portkey Semantic Cache Hit Ratio:
   - If cache hit ratio is < 5%, verify Redis connection or Portkey gateway API credentials.
3. Check Loop Engineering reflection iterations:
   - Inspect whether complex queries are cycling through 3 full reflection cycles between `RemediationPatcher` and `ComplianceAuditor`.

---

## 3. Mitigation Procedures
### Scenario A: Groq 70B Rate Limit (TPM/RPM Exhausted)
1. Switch primary model from 70B to 8B instant in `.env`:
   ```bash
   sed -i 's/GROQ_MODEL=llama-3.3-70b-versatile/GROQ_MODEL=llama-3.1-8b-instant/' .env
   docker compose restart api
   ```
2. Alternatively, enable Portkey fallback routing to secondary provider (OpenAI / Azure).

### Scenario B: Cohere Re-Ranking Latency Surge
1. Switch Re-Ranker mode to local ONNX FlashRank only:
   - Update `app/services/reranker.py` default mode to `"flashrank"`.
   - Latency drops immediately from ~350ms to <15ms with $0.00 cloud cost.

---

## 4. Verification & Recovery
1. Re-query `/metrics/summary` to verify P95 latency has stabilized below 1,000ms.
2. Confirm G-Eval Groundedness score remains above 0.85 on test query:
   ```bash
   curl -X POST http://localhost:8080/query -H "Content-Type: application/json" \
     -d '{"q": "What is our enterprise policy for secret rotation?"}'
   ```
