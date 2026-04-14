## Overview

This design addresses the existing single point of failure in TechKraft’s DNS infrastructure, where a single Unbound DNS server runs on EC2 without redundancy or failover.

The proposed architecture uses AWS Route 53 with health checks and multi-region failover to ensure high availability, low latency, and resilience.

---

## Current Problem

- Single Unbound DNS server on EC2
- No redundancy or failover mechanism
- High risk of downtime due to single point of failure
- No geographic optimization for South Asia users

---

## Proposed Architecture

### High-Level Architecture (ASCII Diagram)

                +----------------------+
                |   Route 53 (DNS)     |
                +----------+-----------+
                           |
    +----------------------+----------------------+
    |                                             |

Primary Endpoint Secondary Endpoint
(ap-south-1) (ap-southeast-1)
| |
+------------------+ +------------------+
| EC2 DNS (Unbound)| | EC2 DNS (Unbound)|
| Multi-AZ Setup | | Multi-AZ Setup |
+------------------+ +------------------+
| |
Health Check Health Check
(Route 53 Monitor) (Route 53 Monitor)


---

## Key Components

### 1. Route 53 (DNS Layer)
- Global DNS management service
- Provides failover routing policy
- Routes traffic based on health checks and latency

---

### 2. Primary DNS (ap-south-1)
- Unbound DNS running on EC2 instances
- Deployed across multiple Availability Zones
- Serves majority of Nepal and South Asia traffic

---

### 3. Secondary DNS (ap-southeast-1)
- Disaster recovery region
- Automatically receives traffic if primary fails
- Ensures global availability

---

### 4. Health Checks
- Route 53 health checks on DNS endpoints
- Monitors:
  - Port 53 availability (TCP/UDP)
  - DNS resolution success
- Configuration:
  - Interval: 30 seconds
  - Failure threshold: 3 consecutive failures

---

## Failover Logic

1. Route 53 routes traffic to primary region (ap-south-1)
2. Health checks continuously monitor DNS availability
3. If failure is detected:
   - Traffic automatically shifts to secondary region (ap-southeast-1)
4. When primary recovers:
   - Traffic gradually shifts back

---

## Latency Considerations (South Asia / Nepal)

- Primary region: ap-south-1 (Mumbai)
  - Lowest latency for Nepal users (~20–40 ms)

- Secondary region: ap-southeast-1 (Singapore)
  - Backup region (~70–100 ms latency)

- Route 53 latency-based routing ensures:
  - Nepal users are routed to Mumbai by default
  - Failover only triggers when required

---

## Cost Optimization

### Estimated Monthly Cost

- Route 53 hosted zone: low fixed cost (~$0.50/month)
- DNS queries: pay-per-million requests (low cost at small scale)
- EC2 instances:
  - 2 small instances (t3.micro or t3.small)
- Health checks:
  - Minimal additional cost per check

---

### Optimization Strategies

- Use small EC2 instances for DNS nodes
- Avoid over-provisioning secondary region
- Use caching to reduce DNS query load
- Scale only when traffic increases

---

## Implementation Timeline

### Phase 1 (1–2 days)
- Create Route 53 hosted zone
- Configure DNS records

### Phase 2 (2–3 days)
- Deploy Unbound DNS in ap-south-1
- Configure multi-AZ setup

### Phase 3 (2–3 days)
- Deploy secondary DNS in ap-southeast-1
- Configure synchronization between nodes

### Phase 4 (1–2 days)
- Configure Route 53 health checks
- Test failover scenarios

---

## Total Estimated Time

5–7 days

---

## Key Design Decisions

- Multi-region deployment for high availability
- Route 53 failover routing for automatic recovery
- Health checks for continuous monitoring
- Region selection optimized for Nepal users

---

## Assumptions

- Moderate DNS traffic load
- EC2-based Unbound DNS is acceptable backend
- Route 53 is the primary DNS management layer
- Users are primarily from South Asia

---

## Summary

This architecture improves:

- High availability by removing single point of failure
- Reliability through multi-region redundancy
- Performance with low-latency routing for Nepal users
- Fault tolerance with automated failover
- Cost efficiency using lightweight infrastructure