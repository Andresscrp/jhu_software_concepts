# Module 7 — Cloud Computing (AWS S3, SageMaker, EC2 Deployment)

**Name:** Andres Sanchez-Castellanos  
**JHED ID:** asanch69  
**Course:** EN.605.256 Modern Software Concepts in Python  
**Module:** Module 7 — Cloud Computing

---

# Sources

- Course lecture materials  
- AWS Documentation  
- Amazon S3 documentation  
- Amazon SageMaker documentation  
- Amazon EC2 documentation  
- boto3 documentation  
- Docker documentation  
- Docker Compose documentation  
- RabbitMQ documentation  
- PostgreSQL documentation  
- Flask documentation  
- Psycopg documentation  
- Pytest documentation  
- Pylint documentation  
- ChatGPT  

---

# Overview

Module 7 extends the GradCafe Analytics platform into the cloud using Amazon Web Services (AWS).

This module introduces two major capabilities:

1. **Cloud Data Pipeline**

Data stored in **Amazon S3** is programmatically downloaded into a **SageMaker Jupyter Notebook** using the AWS SDK (`boto3`).

2. **Cloud Deployment**

The full **Docker Compose microservice system from Module 6** is deployed onto a live **EC2 instance**, demonstrating real-world deployment of containerized infrastructure in the cloud.

This produces a full cloud workflow:

S3 Storage  
↓  
boto3 Retrieval  
↓  
SageMaker Notebook Environment  
↓  
Dockerized Microservice Stack  
↓  
Flask Web App + Worker + RabbitMQ + PostgreSQL  
↓  
EC2 Cloud Server

---

# Part 1 — S3 → SageMaker Data Pipeline

## S3 Storage

A private S3 bucket stores the GradCafe dataset:

Bucket name: **grad-cafe**

Files uploaded:

- applicant_data.json

Public access is blocked to ensure secure storage.

---

## SageMaker Notebook

A SageMaker notebook instance provides a managed Jupyter environment for running Python code and accessing AWS services.

Configuration:

Notebook name: **s3-to-sagemaker-grad-cafe-pipeline**  
Instance type: **ml.t2.medium**  
Platform: **Amazon Linux 2**

The notebook used in this module is:

grad-cafe-pipeline.ipynb

---

## boto3 Integration

The dataset is downloaded from S3 using the AWS Python SDK (`boto3`).

The implementation is located in:

module_7/src/s3_fetch.py

Example logic:

    import boto3

    s3 = boto3.client("s3")

    s3.download_file(
        "grad-cafe",
        "applicant_data.json",
        "applicant_data_SM.json"
    )

The file is saved locally inside the SageMaker notebook workspace as:

applicant_data_SM.json

---

# Part 2 — Deploy Microservices to EC2

The containerized microservice architecture created in **Module 6** is deployed onto an AWS EC2 server.

---

# EC2 Instance Configuration

Instance Type: **t3.micro**  
Operating System: **Ubuntu 22.04**

Security Group Rules:

Inbound SSH — Port 22  
Inbound Web App — Port 8080

PostgreSQL (5432) is **not publicly exposed**.  
RabbitMQ management (15672) is **not publicly exposed**.

---

# Microservice Architecture

The deployed system includes the following services:

Flask Web Application  
RabbitMQ Message Broker  
Worker Consumer Service  
PostgreSQL Database  

Data flow:

Client Browser  
↓  
Flask Web Service (Port 8080)  
↓ publish_task()  
RabbitMQ Queue  
↓  
Worker Consumer  
↓  
PostgreSQL Database

All background processing tasks are handled asynchronously through RabbitMQ.

---

# Docker Compose Deployment

Deployment configuration is stored in:

module_7/ec2/docker-compose.ec2.yml

Services included:

- db → PostgreSQL database  
- rabbitmq → message broker  
- web → Flask application server  
- worker → background processing service  
- db_init → one-time database loader  

---

# Running the Stack on EC2

Typical deployment commands used:

    sudo apt update
    sudo apt install docker.io docker-compose-plugin -y

    git clone <repository>

    docker compose up -d --build

    docker compose ps

After deployment, the application is accessible at:

http://<EC2_PUBLIC_IP>:8080

---

# Verifying Deployment

### Containers Running

    docker compose ps

Expected services:

- db  
- rabbitmq  
- web  
- worker  

---

### Web Application

Open in browser:

http://<EC2_PUBLIC_IP>:8080/analysis

The GradCafe analytics dashboard should load successfully.

---

### Worker Processing

Worker services consume tasks from RabbitMQ and update PostgreSQL asynchronously.

Pipeline:

web → RabbitMQ → worker → PostgreSQL

---

# Repository Structure

module_7/

grad-cafe-pipeline.ipynb  
requirements.txt  
README.md  

src/  
 s3_fetch.py  
 web/  
 worker/  

ec2/  
 docker-compose.ec2.yml  
 EC2_DEPLOYMENT.md  

Screenshots:  
 mfa.png  
 dailyWork.png  
 grad-cafe-bucket.png  
 liveNotebook.png  
 ec2-instance.png  
 ec2-security-group.png  
 ec2-compose-ps.png  
 ec2-app.png  

---

# Required Screenshots

The following verification screenshots are included:

mfa.png — Root account MFA enabled  
dailyWork.png — IAM user permissions  
grad-cafe-bucket.png — S3 bucket contents  
liveNotebook.png — SageMaker notebook instance running  
ec2-instance.png — EC2 instance details  
ec2-security-group.png — EC2 inbound security rules  
ec2-compose-ps.png — Docker services running  
ec2-app.png — Live EC2 application

---

# Testing

Run tests with:

    python -m pytest

Coverage:

    python -m pytest --cov=src

---

# Static Analysis

Code quality verified with:

    pylint src --fail-under=10

Target score: **10.00/10**

---

# Security Practices

Security measures implemented:

- AWS root account protected with MFA  
- IAM user created for daily operations  
- S3 bucket private (public access blocked)  
- EC2 security groups restricted  
- RabbitMQ not exposed publicly  
- PostgreSQL not exposed publicly  
- Secrets excluded from repository  

---

# Stopping AWS Resources

To avoid unnecessary charges after completing the assignment:

Stop EC2 instance:

AWS Console → EC2 → Instances → Stop

Stop SageMaker notebook:

AWS Console → SageMaker → Notebook Instances → Stop

Resources are **stopped but not deleted** because they will be used again in Module 8.

---

# Final Deliverables

Submitted to Canvas:

module_7.zip

GitHub repository contains:

- SageMaker pipeline notebook  
- boto3 S3 integration  
- EC2 deployment configuration  
- Docker Compose microservice system  
- required screenshots  
- tests and linting artifacts  

---

# Summary

This module demonstrates a complete cloud workflow including:

- AWS account security configuration  
- S3 object storage  
- boto3 cloud integration  
- SageMaker data processing environment  
- Docker container orchestration  
- RabbitMQ asynchronous task processing  
- PostgreSQL persistent storage  
- Live EC2 deployment

The GradCafe Analytics platform now runs fully in a cloud infrastructure environment.