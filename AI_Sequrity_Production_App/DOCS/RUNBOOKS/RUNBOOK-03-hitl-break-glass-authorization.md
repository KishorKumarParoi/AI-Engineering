# Operational Runbook: Human-in-the-Loop (HITL) Break-Glass Authorization (RUNBOOK-03)

## Severity Level: SEV-2 / HIGH
**Target Systems**: LangGraph Supervisor State Machine, FastMCP Tool Execution, Streamlit UI

---

## 1. Overview & Purpose
In compliance with **SOC 2 Type II (CC8.1)** and **NIST AI RMF (MANAGE 1.3)**, autonomous agents are prohibited from unilaterally executing destructive infrastructure mutations, modifying firewall policies, or deploying unreviewed code patches to production.
When an agent attempts such actions, the LangGraph graph interrupts execution and transitions state to `hitl_pending = True`.

---

## 2. Supervisor Authorization Procedure

### Option A: Via Streamlit Interactive UI
1. Navigate to `http://localhost:8501` (or cloud dashboard).
2. The active chat session displays a highlighted amber box:
   `⚠️ ACTION REQUIRED: Supervisor Approval Required`
   - Tool Name: e.g. `deploy_waf_rule`
   - Proposed Payload & Blast Radius.
3. Review technical parameters and click **✅ Approve & Deploy** or **❌ Reject & Abort**.

### Option B: Via Command Line / REST API
1. Inspect pending action details:
   ```bash
   curl -s http://localhost:8080/api/v1/hitl/pending/THREAD_ID | jq .
   ```
2. Authorize the action with signed justification:
   ```bash
   curl -X POST http://localhost:8080/api/v1/hitl/approve \
     -H "Content-Type: application/json" \
     -d '{
       "thread_id": "THREAD_ID",
       "decision": "approved",
       "supervisor_notes": "Reviewed rule syntax; passed staging test harness."
     }'
   ```
3. Or reject the action:
   ```bash
   curl -X POST http://localhost:8080/api/v1/hitl/approve \
     -H "Content-Type: application/json" \
     -d '{
       "thread_id": "THREAD_ID",
       "decision": "rejected",
       "supervisor_notes": "Overly broad regex could drop benign client traffic."
     }'
   ```

---

## 3. Emergency Break-Glass Bypass
If an automated system or security incident demands immediate bypass during off-hours:
1. Export environment flag `HITL_AUTO_APPROVE_EMERGENCY=true`.
2. Reload backend service: `docker compose restart api`.
3. Log incident ticket within 2 hours in compliance with SOC 2 audit policies.
