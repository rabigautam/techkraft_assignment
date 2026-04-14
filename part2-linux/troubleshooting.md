 Part 2: Linux System Administration

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
Time Breakdown

Network checks: 10 minutes
System checks: 8 minutes
Logs and analysis: 7 minutes

Total: 25 minutes


---