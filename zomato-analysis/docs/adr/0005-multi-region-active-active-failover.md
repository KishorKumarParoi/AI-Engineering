# ADR 0005: Multi-Region Active-Active Architecture with Sub-30s Automated Failover

## Status: ACCEPTED (Production Standard)

## Context & Problem Statement
During major Indian festive events (e.g. Diwali, IPL Finals, New Year's Eve), regional cloud provider outages or network fiber cuts could paralyze food ordering across major metropolitan areas, causing tens of millions of INR in lost Gross Merchandise Value (GMV).

## Decision
We establish an **Active-Active Multi-Region Cloud Architecture (ap-south-1 Mumbai + ap-south-2 Hyderabad)**:
1. **Global Traffic Management**: AWS Route 53 Latency-Based Routing + CloudFront CDN + BotShield Edge WAF.
2. **Data Layer Replication**: Aurora Global Database with sub-second replication + bi-directional Redis active-active clusters.
3. **Automated Health Probes**: Synthetic canary health checks shifting ingress within 18 seconds of regional degradation.
4. **SLO Targets**: **RTO < 30s**, **RPO < 5s**.

## Consequences
- **Positive**: Resilient against catastrophic regional cloud outages; 99.99% platform availability.
- **Negative**: Inter-region data transfer egress costs and distributed conflict resolution management.
