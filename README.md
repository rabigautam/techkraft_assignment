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


