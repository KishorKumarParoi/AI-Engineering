# Reference Architecture 03: Multi-Region Active-Active AI & Lakehouse Failover

**Domain**: High Availability Enterprise Infrastructure, Disaster Recovery (DR), 99.99% Uptime  
**Regions**: Primary: AWS `ap-south-1` (Mumbai); Secondary: AWS `ap-southeast-1` (Singapore)  
**RTO (Recovery Time Objective)**: < 30 seconds  
**RPO (Recovery Point Objective)**: < 5 seconds

---

## 1. Architectural Topology

```mermaid
flowchart TD
    subgraph GlobalEdge["Global Traffic & Edge Shield"]
        A[Mobile Apps / Consumers] --> B[AWS Route53 Latency & Health-Check Routing]
        B --> C[AWS CloudFront CDN + AWS WAF BotShield]
    end

    subgraph RegionPrimary["Region 1: Mumbai (ap-south-1) - Active 85%"]
        C -->|Primary Inbound| D[ALB + EKS Cluster Mumbai]
        D --> E[(Aurora PostgreSQL Global Database)]
        D --> F[MSK Kafka Primary]
        D --> G[(S3 Delta Lake Bucket)]
    end

    subgraph CrossRegionSync["Sub-Second Cross-Region Replication"]
        E -.->|Aurora Physical Replication <1s| H[(Aurora PostgreSQL Replica)]
        F -.->|MirrorMaker 2 Active Replication| I[MSK Kafka Secondary]
        G -.->|S3 Cross-Region Replication (CRR)| J[(S3 Delta Lake Bucket Secondary)]
    end

    subgraph RegionSecondary["Region 2: Singapore (ap-southeast-1) - Standby / Active 15%"]
        C -.->|Auto Failover on Probe Failure| K[ALB + EKS Cluster Singapore]
        K --> H
        K --> I
        K --> J
    end
```

---

## 2. Disaster Recovery Strategy & Failover Mechanics

### Automatic Health-Check Probing
Route 53 executes HTTP health checks every 10 seconds against `/healthz/deep` across 3 distinct edge locations. The health check verifies:
1. PostgreSQL primary connection and write capability.
2. Kafka broker heartbeat response within 200ms.
3. GPU inference pod readiness.

### Failover Trigger Sequence
```
Probe Failure Detected (3 consecutive failures over 30s)
  │
  ├── 1. Route 53 marks Mumbai endpoint UNHEALTHY
  ├── 2. DNS traffic shifts 100% to Singapore ALB within 15 seconds (TTL: 15s)
  ├── 3. AWS Lambda triggers Aurora Global Database promotion:
  │      `aws rds failover-global-cluster --global-cluster-identifier zomato-global-db`
  ├── 4. EKS Singapore HPA scales consumer deployment from standby (4 pods) to full capacity (32 pods)
  └── 5. PagerDuty pages Incident Commander with SEV-1 notification
```

---

## 3. Architecture Decision Records (ADRs) Linked
- [ADR 0005: Multi-Region Active-Active LLM Gateway and Auto-Failover](../adr/0005-multi-region-active-active-failover.md)
- [ADR 0002: Change Data Capture (CDC) via Debezium and Transactional Outbox](../adr/0002-cdc-kafka-streaming-and-outbox-pattern.md)

---

## 4. Cost Breakdown & Overheads (Monthly)

| Service | Mumbai (Primary) | Singapore (Replica / Standby) | Notes |
|---|---|---|---|
| **EKS Compute** | $2,400.00 | $1,200.00 | Singapore runs 40% base capacity with fast HPA |
| **Aurora PostgreSQL** | $1,800.00 | $1,800.00 | Global Database Read/Write Replica |
| **Kafka MSK + MirrorMaker** | $2,160.00 | $2,160.00 | Mirrored topics for order continuity |
| **S3 Storage + CRR** | $1,280.00 | $1,340.00 | Cross-region data transfer fees ($0.02/GB) |
| **Route 53 & CloudFront** | $450.00 | $450.00 | Global health checks & anycast routing |
| **Total Monthly Spend** | **$8,090.00** | **$6,950.00** | **Total DR Active-Active: $15,040.00 / mo** |

---

## 5. Annual Disaster Recovery Drill (Chaos Engineering)
1. **Scenario**: Simulate complete AZ failure and partition isolation in AWS Mumbai data center.
2. **Frequency**: Bi-annual scheduled drill during lowest traffic window (Tuesday 03:00 - 04:00 IST).
3. **Criteria for Success**:
   - Zero lost committed financial transactions.
   - Traffic fully restored in Singapore in < 28 seconds.
   - Zero double-allocation of delivery fleet.
