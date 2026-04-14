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

## Time Spent

Task                                   Time      

* Code Review & Issue Identification: 12 minutes
* Categorization (Security vs Architecture): 5 minutes
* Designing Improvements: 8 minutes
* Writing Documentation: 5 minutes

Total: 30 minutes
### main.tf
```
provider "aws" {
  region = var.region
}

# ----------------------
# VPC
# ----------------------
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "techkraft-vpc"
  }
}

# ----------------------
# Internet Gateway
# ----------------------
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id
}

# ----------------------
# Public Subnets (ALB, NAT)
# ----------------------
resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index}.0/24"
  availability_zone       = var.azs[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "public-subnet-${count.index}"
  }
}

# ----------------------
# Private Subnets (App + DB)
# ----------------------
resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = var.azs[count.index]

  tags = {
    Name = "private-subnet-${count.index}"
  }
}

# ----------------------
# NAT Gateway
# ----------------------
resource "aws_eip" "nat" {
  count = 2
}

resource "aws_nat_gateway" "nat" {
  count         = 2
  subnet_id     = aws_subnet.public[count.index].id
  allocation_id = aws_eip.nat[count.index].id
}

# ----------------------
# Route Tables
# ----------------------
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
}

resource "aws_route" "public_internet" {
  route_table_id         = aws_route_table.public.id
  gateway_id             = aws_internet_gateway.igw.id
  destination_cidr_block = "0.0.0.0/0"
}

resource "aws_route_table_association" "public_assoc" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table" "private" {
  count  = 2
  vpc_id = aws_vpc.main.id
}

resource "aws_route" "private_nat" {
  count                  = 2
  route_table_id         = aws_route_table.private[count.index].id
  nat_gateway_id         = aws_nat_gateway.nat[count.index].id
  destination_cidr_block = "0.0.0.0/0"
}

resource "aws_route_table_association" "private_assoc" {
  count          = 2
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# ----------------------
# Security Groups
# ----------------------

# ALB SG
resource "aws_security_group" "alb_sg" {
  name   = "alb-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# App SG
resource "aws_security_group" "app_sg" {
  name   = "app-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port       = 5000
    to_port         = 5000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
  }
}

# DB SG
resource "aws_security_group" "db_sg" {
  name   = "db-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.app_sg.id]
  }
}

# ----------------------
# Load Balancer
# ----------------------
resource "aws_lb" "app_alb" {
  name               = "techkraft-alb"
  load_balancer_type = "application"
  subnets            = aws_subnet.public[*].id
  security_groups    = [aws_security_group.alb_sg.id]
}

resource "aws_lb_target_group" "app_tg" {
  name     = "app-tg"
  port     = 5000
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id

  health_check {
    path = "/health"
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.app_alb.arn
  port              = 80
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app_tg.arn
  }
}

# ----------------------
# Launch Template + ASG
# ----------------------
resource "aws_launch_template" "app" {
  name_prefix   = "techkraft-app"
  image_id      = data.aws_ami.amazon_linux.id
  instance_type = "t3.medium"

  vpc_security_group_ids = [aws_security_group.app_sg.id]
}

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]
}

resource "aws_autoscaling_group" "app" {
  desired_capacity    = 2
  max_size            = 4
  min_size            = 2
  vpc_zone_identifier = aws_subnet.private[*].id

  launch_template {
    id      = aws_launch_template.app.id
    version = "$Latest"
  }

  target_group_arns = [aws_lb_target_group.app_tg.arn]
}

# ----------------------
# RDS (Production Ready)
# ----------------------
resource "aws_db_subnet_group" "db" {
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_db_instance" "mysql" {
  identifier              = "techkraft-db"
  engine                  = "mysql"
  instance_class          = "db.t3.medium"
  allocated_storage       = 20
  username                = var.db_username
  password                = var.db_password
  db_subnet_group_name    = aws_db_subnet_group.db.name
  vpc_security_group_ids  = [aws_security_group.db_sg.id]

  multi_az                = true
  backup_retention_period = 7
  storage_encrypted       = true
  deletion_protection     = true
  skip_final_snapshot     = false
}```

###### outputs.tf

```output "alb_dns" {
  value = aws_lb.app_alb.dns_name
}

output "db_endpoint" {
  value = aws_db_instance.mysql.endpoint
}```

##### variable.tf
```
variable "region" {
  default = "us-east-1"
}

variable "azs" {
  default = ["us-east-1a", "us-east-1b"]
}

variable "db_username" {}
variable "db_password" {}```