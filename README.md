
Name: Rabi Gautam
Contact: 9863445987/ rabigautam43@gmail.com
#####################################################
# Part 1: Infrastructure Analysis

## Approach

I approached this task as a production-readiness and risk assessment exercise. Instead of only identifying syntax or Terraform issues, I evaluated the infrastructure across four critical dimensions:

* Security (least privilege, exposure risks)
* Reliability & Availability (single points of failure, redundancy)
* Scalability (ability to handle growth and traffic)
* Maintainability (Infrastructure as Code practices, modularity, and extensibility)

I systematically reviewed each resource (VPC, EC2, RDS, S3, Security Groups) and identified both explicit misconfigurations and architectural gaps.

---

## Key Findings

### Security Risks

* SSH (port 22) exposed to the entire internet (`0.0.0.0/0`)
* HTTP-only access (no HTTPS/TLS encryption)
* Hardcoded database credentials in Terraform code
* No encryption enabled for RDS or S3
* Database sharing the same security group as web servers
* No IAM roles for EC2 instances (risk of credential misuse)
* No logging/auditing (CloudTrail, VPC Flow Logs missing)

---

### Architectural Issues

* No private subnets (all resources publicly accessible)
* No NAT Gateway for secure outbound access
* Missing Internet Gateway and route tables
* No Load Balancer (direct EC2 exposure)
* No Auto Scaling Group (fixed capacity, no self-healing)
* RDS not configured for Multi-AZ or backups
* Hardcoded AMI (not future-proof)
* No tagging strategy (impacts cost tracking and operations)

---

## Improvements for Production Readiness

### 1. Network Redesign

* Introduced public and private subnets across multiple Availability Zones
* Added Internet Gateway and NAT Gateways
* Implemented proper route tables and associations

### 2. Security Hardening

* Restricted SSH access (or replaced with SSM Session Manager)
* Separated security groups (ALB → App → DB)
* Moved secrets to AWS Secrets Manager / Parameter Store
* Enabled encryption for RDS and S3
* Applied principle of least privilege

### 3. High Availability & Scalability

* Added Application Load Balancer (ALB)
* Introduced Auto Scaling Group (ASG)
* Enabled Multi-AZ RDS deployment

### 4. Observability & Operations

* CloudWatch metrics and alarms
* CloudTrail for auditing
* Centralized logging (e.g., ELK/OpenSearch)

### 5. Infrastructure as Code Best Practices

* Replaced hardcoded values with variables
* Suggested modular Terraform structure
* Proposed remote state management (S3 + DynamoDB locking)

---

## Assumptions

* The system is intended for a production backend workload
* Traffic is expected to grow, requiring horizontal scalability
* Security and uptime are high priority
* The team has basic AWS knowledge but limited DevOps maturity
* Budget allows use of managed AWS services

---


### Tools Used
Terraform (Infrastructure as Code review)
AWS Console (conceptual validation of resources)
AWS Well-Architected Framework (security, reliability principles)
Linux networking tools (conceptual: VPC, routing, SG analysis)

## Time Spent

Task                                   Time      

* Code Review & Issue Identification: 12 minutes
* Categorization (Security vs Architecture): 5 minutes
* Designing Improvements: 8 minutes
* Writing Documentation: 5 minutes

Total: 30 minutes





# Part 2: Linux System Administration

## A. Troubleshooting Scenario

## Objective

Diagnose why EC2 instance `10.0.1.50` is unreachable via SSH (connection timeout).

A SSH timeout typically indicates a network or firewall-related issue, not an operating system or SSH service failure.

---

## Step-by-Step Diagnostic Order

### 1. Verify Network Connectivity (Jump Host)

ping -c 4 10.0.1.50
nc -zv 10.0.1.50 22
traceroute 10.0.1.50
nslookup <hostname>

### 2. Check SSH Service Availability (If Network is OK)
ssh -vvv ec2-user@10.0.1.50

On the target system (via SSM/console):

sudo systemctl status sshd
sudo ss -tulnp | grep :22
#### 3. If SSH is Running but Connection Fails

Possible causes:

Security Group blocking port 22
Network ACL denying traffic
Incorrect SSH key or permissions
SSH bound to wrong interface
Firewall rules (iptables/ufw)
Fail2ban blocking IP
Route table misconfiguration
Instance overload
#### 4. Check System Resource Health
top
htop
free -m
df -h
uptime
#### 5. Check System Logs
sudo journalctl -xe
sudo tail -n 100 /var/log/auth.log
sudo tail -n 100 /var/log/syslog
Key Diagnostic Insight
Symptom	Likely Cause
SSH Timeout	Network / SG / NACL / routing issue
Connection Refused	SSH service not running
Connection Hangs	Firewall drop
Intermittent Access	Resource exhaustion
Important Observation

Typical order of investigation:

Security Group rules
Network ACLs
Route tables
OS-level checks

##### Tools Used
Linux CLI tools
ping
nc (netcat)
traceroute
nslookup
ssh
systemctl
ss
top, htop, free, df, uptime
journalctl
AWS Systems Manager (SSM) (for instance access assumption)
AWS EC2 Security Groups / NACL concepts  

#### Time Breakdown

Network checks: 10 minutes
System checks: 8 minutes
Logs and analysis: 7 minutes

Total: 25 minutes


---


# Part 3: Python Scripting (EC2 Monitoring)

## Overview

This script monitors AWS EC2 instances and collects CPU utilization metrics using boto3 and CloudWatch. It generates a structured JSON report and flags instances exceeding a defined CPU threshold.

The solution focuses on automation, observability, and safe handling of AWS API interactions.

---

## Features

- Lists all running EC2 instances in a given region
- Fetches CPU utilization metrics from CloudWatch (last 1 hour, 5-minute intervals)
- Calculates:
  - Average CPU usage
  - Minimum CPU usage
  - Maximum CPU usage
- Flags instances exceeding CPU threshold
- Reads configuration from JSON file
- Outputs structured JSON report
- Includes error handling and logging

---

## Requirements

- Python 3.11+
- AWS credentials configured (via IAM role or AWS CLI)
- boto3 installed

Install dependencies:


pip install boto3
Usage
python ec2_monitor.py \
  --region us-east-1 \
  --threshold 80 \
  --output report.json \
  --config config.json
Arguments
Argument	Description	Required
--region	AWS region to query	Yes
--threshold	CPU threshold for flagging instances	No (default: 80)
--output	Output JSON file path	Yes
--config	Config file path	No (default: config.json)
Config File (config.json)
{
  "alert_threshold": 80,
  "notification_email": "ops@techkraft.com",
  "regions": ["us-east-1", "us-west-2"]
}
Output Format

The script generates a JSON report with the following structure:

[
  {
    "InstanceId": "i-1234567890abcdef",
    "Name": "web-server-1",
    "Type": "t3.medium",
    "CPU": {
      "Average": 45.32,
      "Minimum": 10.12,
      "Maximum": 78.55
    },
    "Flagged": false
  }
]
Architecture

The script follows a modular design:

1. EC2 Data Collection
Retrieves running instances using describe_instances
2. Metrics Collection
Queries CloudWatch CPUUtilization
Uses 1-hour window with 5-minute granularity
3. Processing Logic
Aggregates CPU statistics
Applies threshold-based flagging
4. Reporting
Generates structured JSON output
Logging

The script includes structured logging for:

AWS API requests
Data processing steps
Error handling
Output generation status
Error Handling

Handled scenarios:

AWS API failures (EC2 / CloudWatch)
Missing or empty CloudWatch datapoints
Invalid configuration file
File write failures

All errors are logged and do not crash the entire execution flow.

Key Design Decisions
Modular Functions

Each responsibility is separated into functions:

EC2 retrieval
Metric collection
Report generation
File output
Safe AWS Integration
Uses boto3 exception handling (ClientError, BotoCoreError)
Prevents pipeline failure on partial data loss
Metric Handling
Handles empty CloudWatch responses
Aggregates datapoints safely
Threshold-Based Alerting
Simple rule-based flagging system for CPU usage
Assumptions
EC2 instances have CloudWatch monitoring enabled
IAM role or AWS credentials are properly configured
Instances are tagged with Name (optional)
CloudWatch data is available for the last 1 hour
Limitations
Does not send notifications (email/Slack not implemented)
Does not store historical trends
Only supports CPU metrics (extensible for memory/disk)
Time Complexity
EC2 listing: O(n)
CloudWatch queries: O(n) per instance
Total runtime depends on number of running instances
Summary

This script demonstrates:

AWS automation using boto3
CloudWatch metric retrieval
Structured data processing
JSON report generation
CLI-based tool design
Production-safe error handling approach


#### Tools Used
Python 3.11
boto3 (AWS SDK for Python)
AWS EC2 (DescribeInstances API)
AWS CloudWatch (GetMetricStatistics / GetMetricData)
argparse (CLI handling)
logging module (structured logs)
JSON (config + output handling)

##### Time Spent

Total time required: 30 minutes

Breakdown:

Design and planning: 10 minutes
Implementation: 15 minutes
Testing and validation thinking: 5 minutes

#### Part 4: Bash Scripting (Nginx Log Analysis)

## Overview

This script analyzes Nginx access logs and generates a summary report including:

- Top 10 IP addresses by request count
- Error rate analysis (4xx and 5xx)
- Top 10 most accessed endpoints
- Structured formatted output to stdout

The solution is designed using standard Linux tools only, with no external dependencies.

---

## Script Requirements

- Accept log file path as input argument
- Use standard Linux utilities only (`awk`, `sort`, `uniq`, `grep`)
- Handle missing or malformed log entries gracefully
- Output results in readable format
- Work with standard Nginx log format

---

## Expected Log Format

The script assumes standard Nginx access logs:


IP - - [date] "GET /endpoint HTTP/1.1" status ...


Field mapping:

- `$1` → IP Address
- `$7` → Endpoint
- `$9` → HTTP Status Code

---

## Usage

chmod +x analyze_nginx_logs.sh

./analyze_nginx_logs.sh /var/log/nginx/access.log
Output Example
======================================
         Nginx Log Report
======================================

Total Requests: 15234

Top 10 IP Addresses:
2341 203.0.113.50
1892 198.51.100.23
...

Error Analysis:
4xx Errors: 234 (1.54%)
5xx Errors: 12 (0.08%)

Top 10 Endpoints:
3421 /api/v1/users
2156 /api/v1/products

======================================
Report Completed
======================================
Key Fixes and Design Considerations
1. Handles Malformed Logs
Ignores empty or missing fields
Prevents pipeline failures due to invalid lines
2. No External Dependencies

Only standard Linux tools are used:

awk
sort
uniq
grep

This ensures portability across all Linux systems.

3. Safe Calculations
Prevents division by zero errors
Uses awk BEGIN blocks for safe percentage computation
4. Standard Log Format Assumption

Works with default Nginx access log structure:

$1 → Client IP
$7 → Requested endpoint
$9 → HTTP status code
Important Considerations
Field Parsing Risk

If log format differs, field positions may shift.
This script assumes a standard Nginx configuration.

Data Validation

The script:

Skips empty endpoints
Avoids malformed entries
Ensures stable pipeline execution
Performance

Efficient streaming design:

No in-memory data storage
Uses Unix pipelines for processing large logs
Time Complexity
IP analysis: O(n log n)
Endpoint analysis: O(n log n)
Error analysis: O(n)

Suitable for large production log files.

##### Tools Used
Bash scripting
awk (log parsing & computation)
sort (ranking results)
uniq (aggregation)
grep (filtering logs)
sed (optional text processing)
Nginx access logs (/var/log/nginx/access.log)


#### Time Spent

Total time required: 20 minutes

Log parsing logic design: 7 minutes
Script implementation: 10 minutes
Validation and edge case handling: 3 minutes


--
# Part 5: Network Architecture Design (DNS Redundancy)

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

## Tools Used
AWS Route 53 (DNS + failover routing)
AWS EC2 (Unbound DNS servers)
AWS Health Checks (Route 53 monitoring)
Multi-AZ AWS architecture design
AWS latency-based routing (conceptual)
Networking fundamentals (DNS, TCP/UDP 53) 
## Summary

This architecture improves:

- High availability by removing single point of failure
- Reliability through multi-region redundancy
- Performance with low-latency routing for Nepal users
- Fault tolerance with automated failover
- Cost efficiency using lightweight infrastructure

#### Time Spent 20 minutes


# Kubernetes Section (Bonus)

## Overview

This section demonstrates a basic Kubernetes deployment for the Flask application from Part 2.  
The focus is on understanding core Kubernetes objects rather than advanced cluster design.

I am still learning Kubernetes, so this implementation focuses on simple, correct usage of fundamental resources.

---

## What is being deployed

A simple Flask application container with:

- 2 replicas for basic availability
- A Kubernetes Deployment for scaling
- A Service to expose the application
- Basic health checks (liveness/readiness probes)
- Resource requests and limits

---


# Part 6: CI/CD Pipeline Review

## Overview

This section reviews an existing GitHub Actions pipeline and identifies critical issues related to security, reliability, and production readiness. It also proposes a structured CI/CD improvement strategy including testing, approvals, and rollback mechanisms.

## Kubernetes Deployment (Bonus)

Overview

This section demonstrates a basic Kubernetes deployment for the Flask application from Part 2.

The focus is on understanding core Kubernetes objects rather than advanced cluster design.

I am still learning Kubernetes, so this implementation focuses on simple and correct usage of fundamental resources.

What is being deployed

A simple Flask application container with:

2 replicas for basic availability
Deployment for workload management
Service for network exposure
Horizontal Pod Autoscaler for scaling
Basic health checks (liveness/readiness probes)
Resource requests and limits for stability
Single Kubernetes Manifest (deployment.yaml)

All Kubernetes resources are combined into a single file using YAML multi-document format (---).

apiVersion: apps/v1
kind: Deployment
metadata:
  name: flask-app
  labels:
    app: flask-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: flask-app
  template:
    metadata:
      labels:
        app: flask-app
    spec:
      containers:
        - name: flask-app
          image: flask-app:latest
          ports:
            - containerPort: 5000

          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "250m"
              memory: "256Mi"

          livenessProbe:
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 10
            periodSeconds: 15

          readinessProbe:
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 5
            periodSeconds: 10

---
apiVersion: v1
kind: Service
metadata:
  name: flask-service
spec:
  selector:
    app: flask-app
  type: ClusterIP
  ports:
    - port: 80
      targetPort: 5000

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: flask-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: flask-app
  minReplicas: 2
  maxReplicas: 5
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
Key Concepts Used
1. Deployment
Ensures desired number of replicas (2 pods)
Handles self-healing and rolling updates

2. Service
Exposes pods internally within the cluster
Provides stable networking for the application

3. Horizontal Pod Autoscaler
Automatically scales pods based on CPU usage
Helps handle variable traffic loads

4. Resource Limits
Prevents excessive CPU/memory usage
Improves cluster stability

5. Health Probes
Liveness probe: restarts unhealthy containers
Readiness probe: ensures traffic only goes to ready pods
Assumptions
Docker image (flask-app:latest) is already built and available in registry
Kubernetes cluster is already running (EKS / Minikube / etc.)
Metrics server is installed for HPA to work properly
Limitations (My Current Understanding)
No Ingress controller configured yet
No ConfigMaps or Secrets used yet
No persistent storage configured
No advanced deployment strategies (e.g., blue-green or canary deployments)
What I Understand So Far

This setup provides:

Basic application deployment in Kubernetes
Simple scaling capability
Basic health monitoring
Internal service exposure
Automatic scaling based on CPU usage
Time Spent
Understanding requirements: 10 minutes
Writing Kubernetes manifest: 15 minutes
Structuring documentation: 10 minutes

Total: 35 minutes

## Summary

This Kubernetes setup demonstrates:

Core Kubernetes objects (Deployment, Service, HPA)
Basic scaling and reliability concepts
Health checking and resource management

It is not production-ready, but shows foundational understanding of Kubernetes architecture.
## Tools Used
Kubernetes (core objects)
Deployment
Service
Horizontal Pod Autoscaler (HPA)
Docker (container runtime)
kubectl (deployment management)
Metrics Server (HPA dependency)
AWS EKS / Minikube (assumed cluster environments)
YAML (manifest configuration format)