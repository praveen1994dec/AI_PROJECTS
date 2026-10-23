# 🤖 AI-Assisted DevOps 
---

## Use AI FOR DevOps, SRE, AWS, and infrastructure automation. **AI automation projects FOR DevOps,Cloud.**

### **A collection of AI Projects for DevOps, SRE, observability, Kubernetes, AWS, CICD and infrastructure AI automation projects.**

---

## 📌 Repository Overview

### 🧰 **Purpose**
  - Demonstrate practical ways to apply **AI to DevOps and cloud operations**.
  - Provide standalone examples that can be explored independently.
  - Combine local LLMs, hosted AI services, AWS, Kubernetes, CI/CD, monitoring, and Infrastructure as Code.

### 🧭 **What you will find**
  - AI-assisted troubleshooting and root-cause analysis.
  - Predictive monitoring and anomaly detection.
  - Self-healing CI/CD and Kubernetes agents.
  - Natural-language interfaces for Kubernetes, GitHub, and AWS.
  - RAG systems that answer questions from DevOps source files.
  - Built-In MCP servers and custom MCP implementations.
  - AI-Agents , SRE-Agents , AIOPS
  - AI-Monitoring
  - Learning material for LLMs, MCP, and prompt engineering.

### 🗂️ **Repository style**
  - Each top-level folder is a solution area or learning area.
  - Some solution areas contain one project.
  - Some solution areas contain multiple independent sub-projects.
  - Detailed setup instructions remain in the README files inside each project.

---

## 🗺️ Solution Directory

```text
AI-Assisted-DevOps/
├── AI-DockerFile-Generator/       # AI-generated Dockerfiles
├── AI-Troubleshooting-RCA/        # AWS AIOps assistant and EKS deployment platform / AI-Troubleshooting
├── AIOPS-AI-base-observibility/   # Anomaly detection, forecasting, and Honeycomb observability
├── Cloud-Cost-Optimization-AI/    # AWS cost intelligence and optimization dashboard
├── CrewAi-Agents/                 # CrewAI Kubernetes RCA and travel-planning agents / Multi-Agent System
├── LLM-Local-Model/               # LLM concepts ,local-vs-hosted model and Run Models locally
├── MCP/                           # built-in MCP servers and custom MCP implementations
├── Prompt-engineering/            # Prompt design techniques for AI-assisted engineering
├── RAG-for-devops/                # Local RAG assistant for DevOps repositories
├── SRE-AI-Agent/                  # CI/CD, Docker, and Kubernetes SRE agents
└── Terraform-AI-Agent/            # Natural-language AWS Terraform provisioner (AI)
```

---

## 📚 Project Catalogue

### 🐳 [`AI-DockerFile-Generator`](./AI-DockerFile-Generator/)

- **Project:** AI Dockerfile Generator.
- **What it does**
  - Accepts a programming language such as Python, Node.js, or Java.
  - Uses a local Ollama Llama model to generate an optimized Dockerfile.
- **How it works**
  - User enters a language.
  - The Python application calls the local Ollama API.
  - The model returns a Dockerfile with best-practice guidance.
- **Why it is useful**
  - Speeds up container onboarding.
  - Gives developers a repeatable starting point for container builds.
- **Included variants**
  - [`generate_dockerfile.py`](./AI-DockerFile-Generator/generate_dockerfile.py) uses the local model flow.
  - [`using-openai-api/`](./AI-DockerFile-Generator/using-openai-api/) contains an alternative Gemini/OpenAI-style implementation.

- 📖 [Detailed guide](./AI-DockerFile-Generator/readme.md)

---

### 🩺 [`AI-Troubleshooting-RCA`](./AI-Troubleshooting-RCA/)

- **Project family:** AWS cloud-native DevOps platform and AIOps incident response.
- **[`aiops-assistant/`](./AI-Troubleshooting-RCA/aiops-assistant/) — Kira AIOps Assistant**
  - **What it does**
    - Investigates production incidents through natural-language questions.
    - Correlates CloudWatch logs, Prometheus metrics, and EKS health data.
  - **How it works**
    - Streamlit UI sends a question to an Amazon Bedrock Agent.
    - Bedrock invokes Lambda action groups for logs, metrics, and service health.
    - The agent returns evidence, probable root cause, and remediation guidance.
  - **Why it is useful**
    - Reduces manual console switching during incidents.
    - Helps shorten investigation and mean-time-to-recovery.

- **[`deployment/`](./AI-Troubleshooting-RCA/deployment/) — Cloud-Native Boutique Microservices Platform**
  - **What it contains**
    - React frontend, Node.js services, PostgreSQL, Docker, Kubernetes, Terraform, CI/CD, GitOps, and observability.
  - **How it works**
    - Runs locally with Docker Compose.
    - Provisions AWS networking and EKS infrastructure with Terraform.
    - Deploys services through Kubernetes, Argo CD, and Kustomize.
    - Monitors the platform with Prometheus and Grafana.
  - **Why it is useful**
    - Demonstrates an end-to-end production-style DevOps lifecycle.

- **[`cloude/`](./AI-Troubleshooting-RCA/cloude/)**
  - Contains Claude Code and MCP setup notes used with the platform.

- 📖 [Area overview](./AI-Troubleshooting-RCA/README.md) · [Deployment guide](./AI-Troubleshooting-RCA/deployment/README.md) · [Kira guide](./AI-Troubleshooting-RCA/aiops-assistant/README.md)

---

### 📈 [`AIOPS-AI-base-observibility`](./AIOPS-AI-base-observibility/)

- **[`Anomaly-Detection/`](./AIOPS-AI-base-observibility/Anomaly-Detection/) — CPU Anomaly Detection**
  - **What it does**
    - Detects unusual CPU utilization with an Isolation Forest model.
  - **How it works**
    - Prometheus and Node Exporter collect metrics.
    - Historical data trains the model.
    - Real-time anomalies trigger Slack notifications.
    - Grafana visualizes infrastructure behavior.
  - **Why it is useful**
    - Finds abnormal behavior before a hard threshold becomes an incident.

- **[`incident-prediction/`](./AIOPS-AI-base-observibility/incident-prediction/) — Memory Exhaustion Forecasting**
  - **What it does**
    - Forecasts future memory utilization with Prophet.
  - **How it works**
    - Reads historical Prometheus memory metrics.
    - Predicts memory saturation up to two hours ahead.
    - Sends a proactive Slack alert when predicted usage exceeds the configured limit.
  - **Why it is useful**
    - Supports preventive capacity planning and incident response.

- **[`honeycomb-obervibility/`](./AIOPS-AI-base-observibility/honeycomb-obervibility/) — AI Observability**
  - **What it does**
    - Builds an OpenTelemetry and Honeycomb workflow for metrics, logs, and traces.
  - **How it works**
    - Kubernetes and the OpenTelemetry demo emit telemetry.
    - Honeycomb stores and visualizes distributed traces.
    - Honeycomb MCP enables natural-language investigation and Slack alerting.
  - **Why it is useful**
    - Connects observability data with AI-assisted root-cause analysis.

- 📖 [CPU anomaly guide](./AIOPS-AI-base-observibility/Anomaly-Detection/README.md) · [Memory prediction guide](./AIOPS-AI-base-observibility/incident-prediction/readme.md) · [Honeycomb guide](./AIOPS-AI-base-observibility/honeycomb-obervibility/readme.md)

---
### 💰 [`Cloud-Cost-Optimization-AI`](./Cloud-Cost-Optimization-AI/)

- **Project:** AI Cloud Cost Detective.
- **What it does**
  - Provides a full-stack AWS cost visibility and resource optimization dashboard.
  - Tracks budgets, cost trends, anomalies, reports, and possible savings.
- **How it works**
  - React/Vite frontend communicates with a FastAPI backend.
  - AWS Cost Explorer and AWS resource scanners collect cost and resource data.
  - OpenAI analyzes findings and produces prioritized recommendations.
  - PostgreSQL stores users, budgets, snapshots, and analysis history.
  - WebSockets stream scan progress; PDF and CSV reports can be exported.
- **Why it is useful**
  - Makes idle, unused, over-provisioned, or misconfigured AWS resources easier to find.

- 📖 [Detailed guide](./Cloud-Cost-Optimization-AI/README.md)

---

### 🧑‍💻 [`CrewAi-Agents`](./CrewAi-Agents/)

- **[`K8-RCA-Agent/`](./CrewAi-Agents/K8-RCA-Agent/) — Kubernetes Multi-Agent RCA**
  - **What it does**
    - Investigates failing Kubernetes pods and produces a downloadable incident report.
  - **How it works**
    - A data-gatherer collects logs, events, status, YAML, and resource information.
    - An RCA analyst correlates evidence and identifies the failure mechanism.
    - A DevOps reporter creates fixes, commands, and Kubernetes YAML guidance.
  - **Why it is useful**
    - Turns a multi-command Kubernetes investigation into a structured workflow.

- **[`Trip-Planner-agent/`](./CrewAi-Agents/Trip-Planner-agent/) — CrewAI Travel Planner**
  - **What it does**
    - Creates a personalized seven-day itinerary from travel preferences.
  - **How it works**
    - City-selection, local-expert, and travel-concierge agents research destinations.
    - Search and calculation tools provide weather, activities, accommodation, and budget details.
  - **Why it is useful**
    - Demonstrates reusable CrewAI multi-agent orchestration outside infrastructure operations.

- 📖 [Kubernetes RCA guide](./CrewAi-Agents/K8-RCA-Agent/readme.md) · [Trip Planner guide](./CrewAi-Agents/Trip-Planner-agent/README(1).md)

---
### 🧠 [`LLM-Local-Model`](./LLM-Local-Model/)

- **Project:** Large Language Model learning notes & Run model Locally.
- **What it covers**
  - LLM fundamentals, tokens, training, and common model families.
  - Local models such as Ollama versus hosted providers.
  - Privacy, cost, latency, hardware, and operational trade-offs.
- **Why it is useful**
  - Provides background for choosing the model runtime used by the other projects.
- 📖 [Learning notes](./LLM-Local-Model/readme.md)

---
### 🔌 [`MCP`](./MCP/)

- **Project family:** Model Context Protocol learning material and implementations.
- **[`Built-in-mcp-server/`](./MCP/Built-in-mcp-server/)**
  - Shows how to connect a built-in Kubernetes MCP server to Claude Desktop.
  - Enables natural-language access to pods, logs, deployments, resources, and troubleshooting.

- **[`custom-k8-mcp-server/`](./MCP/custom-k8-mcp-server/)**
  - Implements a custom Kubernetes MCP server in Python.
  - Exposes selected cluster operations through controlled tools instead of unrestricted shell commands.

- **[`Local-mcp-server-ollama+mcp/`](./MCP/Local-mcp-server-ollama+mcp/)**
  - Builds a GitHub MCP server and client that run locally with Ollama.
  - Demonstrates tool discovery, SSE transport, and GitHub repository operations without a hosted AI provider.

- **[`images/`](./MCP/images/)**
  - Contains supporting documentation imagery.
- **Why this area is useful**
  - Explains how AI assistants can securely access live DevOps systems through a standard tool protocol.

- 📖 [MCP concepts](./MCP/readme.md) · [Built-in server](./MCP/Built-in-mcp-server/use-built-in-mcp-server.md) · [Custom Kubernetes server](./MCP/custom-k8-mcp-server/readme.md) · [Local GitHub server](./MCP/Local-mcp-server-ollama+mcp/readme.md)

---
### 📝 [`Prompt-engineering`](./Prompt-engineering/)

- **Project:** Prompt engineering reference for AI-assisted DevOps.
- **What it covers**
  - Roles, tasks, context, constraints, output formats, and step-by-step prompting.
  - Zero-shot, few-shot, and other techniques for more consistent AI output.
- **Why it is useful**
  - Helps users write safer and more precise prompts for troubleshooting, code, and infrastructure tasks.
- 📖 [Prompt engineering notes](./Prompt-engineering/readme.md)

---

### 🔎 [`RAG-for-devops`](./RAG-for-devops/)

- **Project:** Local DevOps Retrieval-Augmented Generation assistant.
- **What it does**
  - Answers questions about Kubernetes manifests, Terraform, Jenkinsfiles, Dockerfiles, and documentation.
- **How it works**
  - [`data/`](./RAG-for-devops/data/) stores the source knowledge base.
  - LangChain loads and splits documents into searchable chunks.
  - Sentence Transformer embeddings are stored in ChromaDB.
  - Ollama retrieves relevant context and generates a source-aware answer.
- **Why it is useful**
  - Keeps infrastructure knowledge private and reduces hallucinations about repository-specific resources.
- 📖 [RAG overview](./RAG-for-devops/readme.md)

---

### 🛡️ [`SRE-AI-Agent`](./SRE-AI-Agent/)

- **[`CICD-Copilot/`](./SRE-AI-Agent/CICD-Copilot/) — Jenkins CI/CD Copilot**
  - **What it does**
    - Analyzes failed Jenkins pipelines with Gemini and AWS Lambda.
  - **How it works**
    - Jenkins invokes Lambda on failure.
    - Lambda collects console logs and sends them to Gemini.
    - The generated RCA and remediation advice are printed in Jenkins.
  - **Why it is useful**
    - Reduces the time spent searching long build and deployment logs.

- **[`cicd-RCA-Agent/`](./SRE-AI-Agent/cicd-RCA-Agent/) — GitHub Actions RCA**
  - **What it does**
    - Investigates failed GitHub Actions runs with LangChain, Ollama, and GitHub CLI.
  - **How it works**
    - Finds failed runs, downloads logs, checks recent diffs and workflow YAML, then creates an RCA report.
  - **Why it is useful**
    - Correlates pipeline configuration and code changes instead of inspecting logs in isolation.

- **[`CICD-Self-Healing-Agent/`](./SRE-AI-Agent/CICD-Self-Healing-Agent/) — Self-Healing CI/CD**
  - **What it does**
    - Attempts to repair failed GitHub Actions workflows automatically.
  - **How it works**
    - Reads failure logs and recent changes.
    - Uses Claude to generate a minimal patch.
    - Applies the patch on a branch and opens a draft pull request for review.
  - **Why it is useful**
    - Creates a safe, reviewable path from pipeline failure to proposed recovery.

- **[`docker-RCA-Agent/`](./SRE-AI-Agent/docker-RCA-Agent/) — Docker Troubleshooter**
  - **What it does**
    - Diagnoses container, image, network, volume, daemon, and log problems.
  - **How it works**
    - LangChain selects Docker CLI tools.
    - Ollama analyzes the collected output and returns RCA guidance.
  - **Why it is useful**
    - Provides conversational troubleshooting for common Docker failures.

- **[`K8-Self-Healing-Agent/`](./SRE-AI-Agent/K8-Self-Healing-Agent/) — Kubernetes Self-Healing**
  - **What it does**
    - Detects unhealthy workloads, proposes repairs, and executes approved Kubernetes changes.
  - **How it works**
    - LangChain tools inspect pods, logs, events, resources, and owners.
    - The agent asks for human approval before mutations such as restart, memory increase, or image update.
  - **Why it is useful**
    - Combines automation with an explicit safety gate for operational changes.

- 📖 [SRE area guides](./SRE-AI-Agent/)

---

### 🏗️ [`Terraform-AI-Agent`](./Terraform-AI-Agent/)

- **Project:** Natural-language AWS infrastructure provisioner.
- **What it does**
  - Converts infrastructure requirements into Terraform configurations.
  - Validates, security-scans, estimates cost, and submits approved changes through GitHub.
- **How it works**
  - Streamlit collects the request.
  - Claude, LangChain, and LangGraph generate and refine Terraform.
  - Terraform validation, TFLint/TFSec checks, and Infracost estimation run before approval.
  - Approved output is pushed to a private GitHub repository and opened as a pull request.
  - GitHub Actions can run the Terraform plan/apply workflow.
- **Why it is useful**
  - Adds review, validation, security, and cost controls to AI-generated Infrastructure as Code.
- 📖 [Detailed guide](./Terraform-AI-Agent/readme.md)

---

## 🧩 Technology Map

| Area | Main technologies used |
|---|---|
| 🤖 AI and LLMs | Ollama, Llama, Claude, Gemini, OpenAI, Amazon Bedrock |
| 🧠 Agent frameworks | LangChain, LangGraph, CrewAI |
| ☸️ Kubernetes | Kubernetes API, EKS, Kind, Helm, Argo CD, Argo Rollouts |
| ☁️ AWS | EKS, Lambda, CloudWatch, Cost Explorer, ECR, VPC, IAM, S3 |
| 🔄 CI/CD | GitHub Actions, Jenkins, Docker, GitOps |
| 📊 Observability | Prometheus, Grafana, OpenTelemetry, Honeycomb, Slack |
| 🏗️ Infrastructure | Terraform, TFLint, TFSec, Infracost |
| 🔎 Knowledge retrieval | LangChain, ChromaDB, Sentence Transformers, RAG |
| 🖥️ Interfaces | Streamlit, React, FastAPI, CLI applications |

---

## 🚀 How to Use This Repository

- 1️⃣ **Choose a project**
  - Use the catalogue above to find the project matching your goal.
- 2️⃣ **Open its local README**
  - Each project README contains its own prerequisites, environment variables, and run commands.
- 3️⃣ **Check cloud and AI prerequisites**
  - AWS projects may require an AWS account, IAM permissions, and configured AWS CLI credentials.
  - Hosted-model projects may require provider API keys.
  - Local-model projects generally require Ollama and a downloaded model.
- 4️⃣ **Keep credentials private**
  - Start from `.env.example` files where available.
  - Never commit API keys, AWS secrets, kubeconfig files, or production credentials.
- 5️⃣ **Run projects independently**
  - Treat each nested application as an individual experiment unless its local README describes an integration.

---

## 🧑‍💻 Author

**Akash Kayande**
DevOps | AWS | AI | SRE | Developer 

---
⭐ If you like this project
Give it a ⭐ on GitHub and feel free to fork or raise issues! 