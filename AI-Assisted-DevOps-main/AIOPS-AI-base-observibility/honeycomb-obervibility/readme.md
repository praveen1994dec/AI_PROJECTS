# 🚀 AI-Based Observability using Honeycomb, OpenTelemetry, Kubernetes & MCP

> Build a complete **AI-powered Observability Platform** using **Honeycomb**, **OpenTelemetry**, **Kubernetes**, and **Honeycomb MCP** to monitor, analyze, troubleshoot, **Detect root cause** **Real time slack alerting** and understand distributed applications using natural language.

---


## ⭐ Introduction

Modern applications consist of dozens or even hundreds of microservices running inside Kubernetes.

When something goes wrong, traditional monitoring tools only tell us **what happened**.


In this project, we'll build a complete **AI-powered Observability Platform** using:

- Kubernetes (Minikube)
- OpenTelemetry
- Honeycomb
- OpenTelemetry Demo Application
- Honeycomb MCP
- AI-powered Natural Language Queries
- Slack alerting

Instead of manually searching dashboards, you'll simply ask:

> "Why is checkout slow?"

or

> "Show me the slowest endpoint."

Honeycomb AI will analyze telemetry data for you & Give Accurate Response.

---

### 🎯 Project Goal

Build a production-style AI-observability pipeline that can:

- Collect metrics,traces,logs
- Export telemetry to Honeycomb
- Analyze distributed traces
- Detect bottlenecks
- Perform AI-powered root cause analysis
- Configure Slack alerting
- Answer observability questions using natural language

---
<p align="center">
  <img src="/AIOPS-AI-base-observibility/honeycomb-obervibility/images/architecture.png" width="800">
</p>

### 🏗 Project Architecture

```
                User Traffic
                     │
                     ▼
      OpenTelemetry Demo Application
                     │
                     ▼
     OpenTelemetry SDKs (Auto Instrumentation)
                     │
                     ▼
          OTLP Telemetry Data
                     │
                     ▼
             Honeycomb Platform
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
 Dashboards              Distributed Traces
 Metrics                 Service Map
 Logs                    Waterfall Analysis
        │
        ▼
 Honeycomb MCP
        │
        ▼
VS Code / Claude Desktop
        │
        ▼
Natural Language AI Queries
        │
        ▼
    Slack Alert
```

---
## 🍯 What is Honeycomb?

**Honeycomb** is a modern, cloud-native **AI-observability** platform designed to help developers and SREs understand, monitor, and troubleshoot complex distributed applications. It collects and analyzes **telemetry data**—including **traces, metrics, and logs**—to provide deep insights into application performance, reliability, and user experience.

Unlike traditional monitoring tools that rely on predefined dashboards and static metrics, Honeycomb enables engineers to explore high-cardinality data in real time, making it easier to investigate unknown issues, identify performance bottlenecks, and perform root cause analysis.

### Key Capabilities

- 📊 Collects metrics, logs, and distributed traces
- 🔍 High-cardinality and real-time data exploration
- ⚡ Fast root cause analysis and performance debugging
- 🌐 Native OpenTelemetry integration
- 🗺️ Service maps and distributed trace visualization
- 🤖 AI-powered observability through Honeycomb MCP
- 📈 Interactive dashboards and advanced query engine
- 🚀 Built for modern cloud-native and Kubernetes environments

## ✨ Honeycomb Features

Honeycomb provides a modern, AI-powered observability platform that helps engineers quickly understand, troubleshoot, and optimize distributed applications. Its powerful features enable deep visibility into application performance, making incident investigation and root cause analysis significantly faster.

| Feature | Description |
|----------|-------------|
| 🔭 **End-to-End Observability** | Gain complete visibility across your entire application by correlating metrics, logs, and distributed traces in a single platform. |

| 🤖 **AI-Powered Observability** | Use AI to investigate performance issues, identify anomalies, and accelerate troubleshooting with intelligent insights. |

| 🧩 **Distributed Tracing** | Follow a request as it travels across multiple microservices to understand latency, dependencies, and failures. |

| 🎨 **Honeycomb Canvas** | Create interactive visual workflows that combine queries, charts, traces, and insights into a collaborative troubleshooting workspace. |

| 🔌 **Honeycomb MCP** | Connect AI assistants such as Claude or VS Code through the Model Context Protocol (MCP) to ask natural-language questions about your telemetry data. |

| 🫧 **BubbleUp Analysis** | Automatically compare normal and problematic requests to highlight the fields most responsible for performance issues or failures. |

| 📈 **Bubble Graphs** | Visualize latency, request volume, errors, and other telemetry dimensions using interactive bubble charts for faster anomaly detection. |

| 🎯 **Service Level Objectives (SLOs)** | Define, monitor, and track SLOs to measure service reliability, error budgets, and user experience over time. |

| 🚨 **Alerting & Notifications** | Configure intelligent alerts and integrate with platforms like Slack, PagerDuty, and Microsoft Teams for real-time incident notifications. |

| 🔍 **Root Cause Analysis** | Quickly identify the underlying cause of latency spikes, failed requests, and production incidents using correlated telemetry data. |

| 🗺️ **Service Map** | Automatically visualize service dependencies and communication paths across your distributed architecture. |

| 🌊 **Trace Waterfall View** | Analyze every span within a request to pinpoint slow operations and performance bottlenecks. |

---

## 🤖 Why AI Observability?

Traditional monitoring requires engineers to:

- Open dashboards
- Filter services
- Search logs
- Correlate metrics
- Follow traces
- Guess the root cause

AI Observability automates this entire workflow.

Instead of manually investigating:

```
CPU ↑
Latency ↑
Error ↑
```

You simply ask:

> Why is checkout failing?

AI analyzes:

- traces
- spans
- latency
- services
- dependencies
- bottlenecks

* and provides an explanation & Root Cause.

---


### 🛠 Technology Stack

| Category | Technology |
|-----------|------------|
| Container Orchestration | Kubernetes |
| Local Cluster | Minikube |
| Package Manager | Helm |
| Observability | OpenTelemetry |
| Collector | OpenTelemetry Collector |
| Backend | Honeycomb |
| AI Integration | Honeycomb MCP |
| IDE | VS Code / Claude Desktop |
| Demo Application | OpenTelemetry Demo |
| Protocol | OTLP |
| Language | YAML |

---


## ✅ Prerequisites

Install the following tools before starting:

- Docker Desktop
- Minikube
- kubectl
- Helm
- Honeycomb Account

---

## ⭐ Step 1 – Start Kubernetes Cluster

### Start Minikube

```bash
minikube start --cpus=4 --memory=6g
```

Verify nodes:

```bash
kubectl get nodes
```

---

## ⭐ Step 2 – Create Honeycomb Account

1. Visit:

```
https://ui.honeycomb.io
```

2. Sign up

3. Create an Environment

4. Navigate to:

```
Settings
    ↓
API Keys
```

5. Copy your Team API Key

Dataset:

```
otel-demo
```

---
<p align="center">
  <img src="/AIOPS-AI-base-observibility/honeycomb-obervibility/images/honeycomb.png" width="800">
</p>

---

## ⭐ Step 3 – Setup Opentelementry Demo Application (Auto-Instrumented)

```bash
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts

helm repo update
```

Create namespace:

```bash
kubectl create namespace otel-demo
```

---

## ⭐ Step 4 – Configure OpenTelemetry Collector

Create a `values.yaml` file.

[values.yaml](/AIOPS-AI-base-observibility/honeycomb-obervibility/values.yaml)

### 📡 Why Configure the OpenTelemetry Collector?

- **For Export Data (traces, metrics, and logs) To Honeycomb**

The **OpenTelemetry Collector** acts as the central telemetry pipeline between your application and Honeycomb. Although the OpenTelemetry Demo Application is **auto-instrumented** and generates traces, metrics, and logs, it still needs a component to receive, process, and export that telemetry to an observability backend.

- 📥 Receive telemetry data (OTLP over HTTP and gRPC) from all demo application services.
- 📤 Export traces, metrics, and logs securely to **Honeycomb** using the OTLP HTTP exporter.

---
## ⭐ Step 5 – Deploy OpenTelemetry Demo Application

Deploy using Helm:

```bash
helm upgrade --install otel-demo open-telemetry/opentelemetry-demo \
  -n otel-demo \
  -f values.yaml
```

Verify deployment:

```bash
kubectl get pods -n otel-demo
```
<p align="center">
  <img src="/AIOPS-AI-base-observibility/honeycomb-obervibility/images/get-pods.png" width="800">
</p>
---

## ⭐ Step 6 – opentelementry demo Application deploy

Expose the frontend:

```bash
kubectl port-forward \
-n otel-demo \
svc/otel-demo-frontendproxy \
8080:8080
```

<p align="center">
  <img src="/AIOPS-AI-base-observibility/honeycomb-obervibility/images/app.png" width="800">
</p>
---

## ⭐ Step 7 – Verify Telemetry in Honeycomb

Open Honeycomb and select the `otel-demo` dataset.

You should see:

- Incoming traces
- Metrics
- Logs
- Span waterfalls
- Service dependency map
- Latency graphs
- Error rates
- Request volume

If telemetry is visible, your OpenTelemetry Collector is successfully exporting data to Honeycomb.

<p align="center">
  <img src="/AIOPS-AI-base-observibility/honeycomb-obervibility/images/data.png" width="800">
</p>

---
<p align="center">
  <img src="/AIOPS-AI-base-observibility/honeycomb-obervibility/images/more-data.png" width="800">
</p>
---


## 🫧 BubbleUp in Honeycomb

**BubbleUp** is one of Honeycomb’s most powerful analysis features, designed to help you quickly identify **what makes a group of requests different from the rest**. Instead of manually filtering through thousands of traces or events

### 🚀 Key Benefits

- 🔍 Automatically identifies unusual patterns in telemetry data
- ⚡ Accelerates root cause analysis during incidents
- 📊 Compares selected events against the overall dataset
- 🧠 Highlights the attributes that contribute to performance issues
- 🌐 Works seamlessly with traces, logs, and metrics
- ☁️ Ideal for debugging distributed microservices and Kubernetes workloads
- 🤖 Reduces manual investigation and speeds up troubleshooting

> **Example:** If the `/checkout` endpoint suddenly becomes slow, BubbleUp may reveal that all slow requests originate from a specific Kubernetes pod or a newly deployed application version, helping you identify the issue within seconds.

<p align="center">
  <img src="/AIOPS-AI-base-observibility/honeycomb-obervibility/images/pre-babble.png" width="800">
</p>

---

<p align="center">
  <img src="/AIOPS-AI-base-observibility/honeycomb-obervibility/images/babble.png" width="800">
</p>
---

## ⭐ 8. Set Up Honeycomb MCP in VS Code

### 📖 What is Honeycomb MCP?

**Honeycomb MCP (Model Context Protocol)** is an AI integration that allows AI assistants, such as **GitHub Copilot Chat in VS Code**, to securely connect to your Honeycomb account. Instead of manually navigating dashboards or writing complex queries, you can ask questions in natural language, and the AI retrieves and analyzes your observability data directly from Honeycomb.

---

* With Honeycomb MCP, you can:

- 🤖 Ask observability questions using natural language
- 🔍 Perform faster root cause analysis
- ⚡ Troubleshoot production issues without complex queries
- 📊 Analyze traces, metrics, and logs directly from VS Code
- 🚀 Improve developer productivity by keeping debugging inside the IDE

---

### Open VS Code Settings

Search for:

**Model Context Protocol**

---

### Add Honeycomb MCP Server Configuration

Add the following configuration to your VS Code MCP settings:

```json
{
  "servers": {
    "honeycomb": {
      "url": "https://mcp.honeycomb.io/mcp",
      "type": "http"
    }
  },
  "inputs": []
}
```

---

### Restart VS Code

Restart VS Code to load the newly configured MCP server.

---

### Authenticate with Honeycomb

After restarting, VS Code will open your browser for OAuth authentication.

1. Sign in to your Honeycomb account.
2. Review the requested permissions.
3. Click **Allow** to authorize the connection.

* Once authentication is complete, **GitHub Copilot Chat** can securely access your Honeycomb telemetry through the MCP server, enabling AI-powered observability directly within VS Code.

## ⭐ Step 9 – Ask AI Observability Questions

Examples you can ask:

- Show me the slowest endpoint in the last 20 minutes.
- List the top 5 slowest services.
- Which endpoints have p95 latency greater than 500ms?
- What caused the latency spike?
- Show traces where checkout exceeded 500ms.
- Which service handled the most requests?

<p align="center">
  <img src="/AIOPS-AI-base-observibility/honeycomb-obervibility/images/mcp.png" width="800">
</p>

---

## 🎨 Honeycomb Canvas

**Honeycomb Canvas** is an interactive visual workspace that helps you investigate, analyze, and document production issues in one place. Instead of switching between multiple dashboards, queries, and notes, Canvas lets you organize your investigation by combining charts, trace queries, text notes, and insights into a single collaborative workspace.

Think of it as a **digital whiteboard for observability**, where you can build an investigation step by step and share it with your team.

### ✨ Why Use Canvas?

- 📊 View multiple charts and queries on one screen
- 🔍 Compare telemetry data from different services
- 📝 Add notes, observations, and findings
- 🤝 Share investigations with your team
- 🚀 Speed up debugging and root cause analysis
- 📌 Save your investigation for future reference

---

## ⚙️ How It Works

1. Create a new **Canvas** in Honeycomb.
2. Add charts, queries, and trace visualizations.
3. Arrange them to match your investigation workflow.
4. Add notes, observations, or conclusions.
5. Save and share the Canvas with your team for future debugging or incident reviews.

<p align="center">
  <img src="/AIOPS-AI-base-observibility/honeycomb-obervibility/images/canva.png" width="800">
</p>
---

## 🚨 Real-Time Alerting with Honeycomb & Slack

* Honeycomb's **Triggers** enable real-time alerting by continuously evaluating telemetry data against user-defined conditions. When a trigger fires, Honeycomb can immediately send notifications to collaboration platforms like **Slack**, ensuring the right team is informed without delay.

* In this project, we integrate **Slack** with **Honeycomb** and configure a real-time alert that monitors the **99th percentile (P99) request latency**. If the application's P99 latency remains above **500 milliseconds** for **five consecutive minutes**, Honeycomb automatically sends an alert to a designated Slack channel. This allows DevOps, SRE, and engineering teams to respond quickly before the issue impacts a larger number of users.

---

## 🎯 Objective

Implement a production-style alerting pipeline that:

- Continuously monitors application latency
- Detects performance degradation using P99 latency
- Automatically triggers alerts when thresholds are exceeded
- Sends instant notifications to a Slack channel
- Enables faster incident response and reduced MTTR


## 🚀 Implementation Steps

### 1. Integrate Slack with Honeycomb

1. create Slack Channel → go on **slack** Create channel `#incidents`
2. In Slack → **Apps** → search **Incoming WebHooks** → Add to Workspace
3. Choose channel `#incidents` → copy the Webhook URL
4. In Honeycomb → **Team Settings** → **Integrations** → **Add Integration**
   - **Provider:** Webhook
   - **Name:** `slack-incidents`
   - **Webhook URL:** paste your Slack Incoming Webhook URL
   - **Shared Secret:** leave blank

---

### 2. Create a Honeycomb Trigger

Navigate to your **Honeycomb Dataset** and create a new **Trigger**.

Configure the trigger with the following settings:

- **Dataset:** `otel-demo`
- **Metric:** Request Latency
- **Aggregation:** P99
- **Condition:** Greater than `500 ms`
- **Duration:** `5 Minutes`
- **Notification Channel:** Slack
- **Severity:** High

Save and enable the trigger.

<p align="center">
  <img src="/AIOPS-AI-base-observibility/honeycomb-obervibility/images/trigger.png" width="800">
</p>

---

### 3. Test the Alert

Generate application traffic using the OpenTelemetry Demo application. Simulate increased latency or load so that the **P99 latency exceeds 500 ms** for at least **5 minutes**.

Once the condition is met, Honeycomb evaluates the trigger and automatically sends an alert to the configured Slack channel.

<p align="center">
  <img src="/AIOPS-AI-base-observibility/honeycomb-obervibility/images/slack.png" width="800">
</p>
---