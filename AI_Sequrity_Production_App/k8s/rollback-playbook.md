# Kubernetes Automated & Manual Rollback Playbook (K8S-ROLLBACK)

## Severity: SEV-1 / CRITICAL
**Scope**: Production Kubernetes Cluster (`ai-production` namespace)

---

## 1. Automated Rollback Triggers (Prometheus & Argo Rollouts)
An automated rollback executes instantly if any of the following SLO conditions are breached during a canary release:
1. **Error Rate**: HTTP 5xx responses exceed 0.5% of total requests over a 2-minute evaluation window.
2. **Latency SLO**: P95 latency exceeds 2,000ms.
3. **G-Eval Groundedness**: Mean batch quality index drops below 0.80.

---

## 2. Emergency Manual Rollback (< 60 Seconds)

### Step 1: Drain Canary Traffic to 0%
If Istio VirtualService is active, immediately set Canary traffic weight to 0%:
```bash
kubectl patch virtualservice enterprise-rag-canary-router -n ai-production --type='json' -p='[
  {"op": "replace", "path": "/spec/http/1/route/0/weight", "value": 100},
  {"op": "replace", "path": "/spec/http/1/route/1/weight", "value": 0}
]'
```

### Step 2: Rollback Deployment Revision
Revert to the previous healthy deployment replica set:
```bash
kubectl rollout undo deployment/enterprise-rag-api -n ai-production
```

### Step 3: Verify Rollback Status
```bash
kubectl rollout status deployment/enterprise-rag-api -n ai-production
kubectl get pods -n ai-production -l app=enterprise-rag-api
```

---

## 3. Post-Rollback Verification
1. Run liveness probe verification:
   ```bash
   kubectl run test-probe --rm -i --tty --image=curlimages/curl -- \
     curl -s http://enterprise-rag-api-svc.ai-production.svc.cluster.local:8080/health
   ```
2. Flush degraded Redis cache keys:
   ```bash
   kubectl exec -it redis-master-0 -n ai-production -- redis-cli flushdb
   ```
3. Notify Lead Incident Commander on the security operations Slack channel.
