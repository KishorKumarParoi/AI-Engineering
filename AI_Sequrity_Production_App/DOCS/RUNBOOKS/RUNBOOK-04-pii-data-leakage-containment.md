# Operational Runbook: PII & Credential Leakage Containment (RUNBOOK-04)

## Severity Level: SEV-1 / CRITICAL
**Target Systems**: PII Filter Engine, Qdrant Vector DB, Logfire Tracing, Streamlit UI

---

## 1. Trigger Conditions & Detection
- Alert `PIIFilterCriticalSecretDetected`: Inbound query or model output contained raw AWS/Groq API keys or unmasked credit cards.
- User or external audit reports sensitive data returned in RAG output.

---

## 2. Immediate Containment Workflow (< 10 Minutes)
1. **Identify Session & Query Thread**:
   ```bash
   grep "PII Filter triggered" /var/log/user-data.log | tail -n 20
   ```
2. **Purge Affected Vector Embeddings (if ingested)**:
   - If user attempted to ingest sensitive documents into Qdrant:
   ```python
   from qdrant_client import QdrantClient
   client = QdrantClient(url="http://localhost:6333")
   client.delete(collection_name="enterprise_rag", points_selector=[POINT_ID])
   ```
3. **Trigger AWS / Third-Party Secret Invalidation**:
   - If an `AKIA...` key or `sk-...` token was exposed, immediately revoke and rotate via AWS IAM / Groq console.

---

## 3. Verify PII Tokenizer Status
- Ensure `PIIFilterEngine` default mode is set to `MaskingMode.TOKENIZE` or `MaskingMode.REDACT` in `app/security/pii.py`.
- Run unit test suite:
  ```bash
  python -m pytest tests/test_security_pii.py -v
  ```

---

## 4. Regulatory Reporting & Postmortem
- If customer PII exceeded 50 records, notify Data Protection Officer (DPO) within 72 hours per GDPR Article 33.
- Generate postmortem within 24 hours.
