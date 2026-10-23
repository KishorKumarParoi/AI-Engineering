# Runbook: Canary Rollback & Production Incident Triage

**Severity Level**: SEV-1 / Critical (if canary promoted) or SEV-2 / High  
**Service Impact**: Order Placement / Delivery Estimation Errors during new release deployment  
**Primary On-Call Role**: Principal Platform Engineer / Incident Commander  
**SLO Target**: Abort canary < 30 seconds; Complete blue-green rollback < 60 seconds.

---

## 1. Automated Canary Failure Triggers

Argo Rollouts automatically halts and marks canary steps degraded if:
- **`MetricAnalysisFailed`**: P99 latency on new canary pods exceeds 120ms (baseline: 45ms).
- **`ErrorRateThresholdExceeded`**: HTTP 5xx responses exceed 0.5% during any 5-minute pause step.
- **`DataContractViolationsSpike`**: Contract validation error rate increases by > 1.0% following a schema release.

---

## 2. Immediate Action: Abort Canary & Instant Rollback

### Step 2.1: Abort In-Flight Argo Rollout
```bash
# Abort the active rollout and pin traffic 100% to stable revision
kubectl argo rollouts abort eta-serving-rollout -n ml-serving

# Check current traffic weight
kubectl argo rollouts get rollout eta-serving-rollout -n ml-serving
```
*Expected State:* Weight reverts immediately to `100% stable`, `0% canary`.

### Step 2.2: Hard Blue-Green Rollback (Fallback)
If using the Blue-Green Kubernetes deployment (`k8s/blue-green-deployment.yaml`):
```bash
# Point active service selector directly back to blue deployment
kubectl patch service eta-serving-active -n ml-serving \
  -p '{"spec":{"selector":{"deployment-color":"blue"}}}'
```
Verify active traffic route:
```bash
kubectl get endpoints eta-serving-active -n ml-serving -o wide
```

---

## 3. Incident Triage & Forensic Capture

### Step 3.1: Dump Canary Crash / Error Logs
```bash
kubectl logs -n ml-serving -l app=eta-serving,rollouts-pod-template-hash=<canary_hash> \
  --tail=500 > /tmp/canary_incident_logs.txt
```

### Step 3.2: Inspect Prometheus Canary vs Stable Metrics
Compare HTTP error rates:
```promql
sum(rate(http_requests_total{status=~"5..", role="canary"}[5m]))
/
sum(rate(http_requests_total{role="canary"}[5m]))
```

### Step 3.3: Capture Heap & Thread Profile
```bash
kubectl exec -it deployment/eta-serving-canary -n ml-serving -- \
  py-spy dump --pid 1 > /tmp/canary_pyspy.txt
```

---

## 4. Post-Rollback Sign-off
- [ ] Active service is 100% routed to known-good stable pods.
- [ ] End-to-end order placement success rate is >= 99.95%.
- [ ] P99 latency returns below 50ms.
- [ ] Open JIRA/Linear SEV ticket and initiate root cause analysis for the postmortem.
