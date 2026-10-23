# DevOps + AIOps 
---

# Cloud-Native DevOps & AIOps Platform on AWS

### End-to-End Kubernetes Deployment, GitOps, CI/CD, Observability, and AI-Powered Incident Response with Amazon Bedrock

---

# 📖 Project Overview

This project demonstrates a complete **production-grade DevOps, Cloud, and AIOps implementation** for deploying and operating a cloud-native **boutique e-commerce microservices application** on **Amazon Web Services (AWS)**.

The repository covers the entire application lifecycle—from local development with **Docker**, infrastructure provisioning using **Terraform**, Kubernetes deployment on **Amazon EKS**, automated **CI/CD pipelines**, **GitOps-based continuous delivery**, and a comprehensive **observability platform**. It further extends into **AIOps** by integrating an intelligent SRE assistant named **Kira**, powered by **Amazon Bedrock Agents**, to automate production incident investigation and root cause analysis.

The infrastructure follows modern DevOps best practices, including **Infrastructure as Code (IaC)**, containerization, Kubernetes orchestration, GitOps workflows, centralized monitoring, log aggregation, distributed tracing, and AI-assisted operational intelligence. Together, these components simulate the architecture and operational practices used by modern cloud-native engineering teams.

---

## Repository Structure

```
DevOps-Practice-Guide/
├── cloude/
│   └── claude-setup.md            # Claude Code + MCP server setup
├── deployment/
│   ├── README.md                  # EKS deployment guide 
│   ├── boutique-microservices/    # The application (7 services)
│   ├── Infrastructure/            # Terraform for AWS provisioning
│   └── aiops-assistant/           # Bedrock Agent — Kira 
|   ├──gitops/
│   ├── argo-cd.yml                # ArgoCD Application manifest
│   ├── kustomization.yml          # Kustomize entry point
│   └── k8s/                       # All Kubernetes manifests
└── .github/
    └── workflows/ci.yml           # GitHub Actions CI pipeline
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Application | React, Node.js, PostgreSQL |
| Containers | Docker, Docker Compose |
| Orchestration | Kubernetes (AWS EKS) |
| Infrastructure | Terraform |
| CI/CD | GitHub Actions |
| GitOps | ArgoCD + Kustomize |
| Monitoring | Prometheus + Grafana |
| Log Forwarding | AWS Fluent Bit → CloudWatch |
| AIOps | AWS Bedrock Agent (Kira) |
| AI Assistant | Claude Code + MCP Servers |


# Boutique Microservices — Deployment Guide

This guide walks through the full deployment of the **boutique e-commerce application** — from running it locally with **Docker**, to provisioning **AWS infrastructure** with **Terraform**, to running it on **Kubernetes** with a full **CI/CD pipeline**, **GitOps**, and **observability stack**.


---
## Architecture

<p align="center">
  <img src="/AI-Troubleshooting-RCA/deployment/images/workflow0.png" width="850">
</p>

---
<p align="center">
  <img src="/AI-Troubleshooting-RCA/deployment/images/workflow2.png" width="850">
</p>

---
<p align="center">
  <img src="/AI-Troubleshooting-RCA/deployment/images/workflow3.png" width="850">
</p>

---
<p align="center">
  <img src="/AI-Troubleshooting-RCA/deployment/images/workflow4.png" width="850">
</p>

---
<p align="center">
  <img src="/AI-Troubleshooting-RCA/deployment/images/workflow5.png"" width="850">
</p>

---
| Service | Port | Role |
|---------|------|------|
| Frontend | 3000 | React UI |
| Gateway | 3001 | Routes all client requests to backend services |
| Auth | 3002 | Login and registration |
| Product Service | 3003 | Product catalog and inventory |
| Order Service | 3004 | Cart and checkout |
| Orders | 3005 | Order history and management |
| User Service | 3006 | User profiles and account management |
| PostgreSQL | 5432 | Stores auth_db, products_db, orders_db, users_db |
| Prometheus | 9090 | Metrics collection |
| Grafana | 8080 | Metrics dashboards |

---

# 🤖 AIOps Assistant — Kira

## **An AI-Powered Site Reliability Engineering (SRE) Assistant Built with Amazon Bedrock Agents**

### Diagnose production incidents in seconds using **Amazon Bedrock Agents**, **AWS Lambda**, **Amazon CloudWatch**, **Prometheus**, **Amazon EKS**, and **Streamlit**.

<p align="center">
  <img src="/AI-Troubleshooting-RCA/aiops-assistant/images/kira (2).png" alt="Kira - AI AIOps Assistant" width="850">
</p>

<p align="center">
  <img src="/AI-Troubleshooting-RCA/aiops-assistant/images/kira (1).png" alt="Kira - AI AIOps Assistant" width="850">
</p>

<p align="center">
  <img src="/AI-Troubleshooting-RCA/aiops-assistant/images/kira (3).png" alt="Kira - AI AIOps Assistant" width="850">
</p>
---

# 📖 Overview

**Kira** is an **AI-powered AIOps and Site Reliability Engineering (SRE) assistant** that helps DevOps engineers investigate production incidents through natural language conversations.

Instead of manually navigating multiple AWS consoles, querying CloudWatch Logs, writing PromQL queries, or inspecting Kubernetes resources, engineers can simply ask questions such as:

* *Why are users receiving HTTP 503 errors?*
* *Is CPU usage increasing across the cluster?*
* *Which pods are unhealthy?*
* *What is causing the service outage?*

Kira orchestrates **Amazon Bedrock Agents** with multiple AWS Lambda action groups to automatically collect operational data from **Amazon CloudWatch Logs**, **Prometheus metrics**, and **Amazon EKS cluster health**. It correlates this information to identify probable root causes, provide supporting evidence, and recommend actionable remediation steps.

---

## ✨ Key Features

* 🤖 AI-powered incident diagnosis using Amazon Bedrock Agents
* 📊 Retrieve infrastructure metrics directly from Prometheus
* 📜 Search and analyze CloudWatch Logs automatically
* ☸️ Monitor Amazon EKS cluster, node groups, and pod health
* 🔍 Correlate logs, metrics, and cluster status for root cause analysis
* 💡 Generate remediation recommendations with supporting evidence
---

<p align="center">
  <img src="/AI-Troubleshooting-RCA/aiops-assistant/images/architecture.png" alt="Kira - AI AIOps Assistant" width="850">
</p>

## Architecture

```
Streamlit UI (app.py)
      │
      ▼
Bedrock Agent (Kira)
      │
      ├── fetch_logs         → CloudWatch Logs
      ├── fetch_metrics      → Prometheus (ELB endpoint)
      └── fetch_service_health → EKS cluster + node groups
```