# ☸️ Build  Own Kubernetes MCP Server for AI-Assisted DevOps with Cloudy Desktop

### > Build a production-ready **Custom Kubernetes MCP (Model Context Protocol) Server** using Python, connect it with **Cloudy Desktop**, and manage Kubernetes clusters using natural language instead of `kubectl`.

---

# Introduction

Managing Kubernetes clusters generally requires writing numerous `kubectl` commands.

Examples include:

* Listing Pods
* Restarting Deployments
* Scaling Applications
* Viewing Logs
* Creating Namespaces
* Listing Services
* Checking Nodes

Although Kubernetes is powerful, remembering every command becomes difficult.

Instead of writing commands, imagine simply asking to LLM Model:

> "Show all pods in the default namespace."

or

> "Restart the payment deployment."

or

> "Scale nginx deployment to 5 replicas."

This is exactly what **Model Context Protocol (MCP)** enables.

Instead of generating shell commands, an AI directly calls Python functions that safely interact with the Kubernetes API.

---

# What is Model Context Protocol (MCP)?

Model Context Protocol (MCP) is an open protocol that allows Large Language Models (LLMs) to communicate with external tools.

Think of MCP as a bridge.

```
User
   │
Natural Language
   │
   ▼
LLM
   │
Tool Selection
   │
   ▼
MCP Server
   │
Python Function
   │
   ▼
Kubernetes API
   │
Cluster
```

The LLM never interacts directly with Kubernetes.

Instead:

* User asks a question
* LLM understands intent
* MCP selects the correct tool
* Python executes Kubernetes API calls
* Result returns to the LLM
* LLM explains the output naturally

---

# Why Build a Custom MCP Server?

Many built-in MCP servers already exist.

However, a custom server provides complete control.

Benefits include:

* Create your own tools
* Restrict operations
* Implement security rules
* Integrate internal platforms
* Add organization-specific automation
* Control AI capabilities
* Avoid exposing unnecessary cluster permissions
* Build reusable DevOps assistants

Instead of depending on generic tools, you expose only the APIs you want the AI to use.

---
# Project Architecture

```
                  User

                    │

                    ▼

          Cloudy Desktop (LLM)

                    │

            Model Context Protocol

                    │

                MCP Client

                    │

        Custom Kubernetes MCP Server

                    │

        Kubernetes Python Client SDK

                    │

              Kubernetes Cluster
```

---

# How MCP Works

Suppose the user asks:

```
List all Pods in default namespace.
```

### Step 1

Cloudy Desktop sends the request to the LLM.

---

### Step 2

The LLM reviews the tools exposed by the MCP server.

Example:

```
list_namespace_pods()

get_pod_logs()

delete_pod()

restart_deployment()
```

---

### Step 3

The LLM selects

```
list_namespace_pods()
```

---

### Step 4

The MCP server executes

```python
v1.list_namespaced_pod("default")
```

---

### Step 5

The Kubernetes API returns

```
frontend-76cb8
backend-8d7cc
redis-776fb
```

---

### Step 6

The MCP server returns structured text.

---

### Step 7

Cloudy Desktop displays

```
I found 3 running Pods:

frontend-76cb8

backend-8d7cc

redis-776fb
```

No `kubectl` command is generated.

---

# Prerequisites

Before starting, ensure the following are installed on your machine.

| Requirement        | Description                  |
| ------------------ | ---------------------------- |
| Claude Desktop     | Installed on your system     |
| Kubernetes Cluster | Local or Cloud               |
| kubectl            | Configured correctly         |
| kubeconfig         | Points to your cluster       |
| Node.js            | Required for `npx` execution |

---

#  — Verify Kubernetes Access

Before configuring MCP, verify that your Kubernetes cluster is accessible.

```bash
kubectl cluster-info
```

Expected output:

```text
Kubernetes control plane is running at https://xxxxxxxx
CoreDNS is running at ...
```

Now verify your nodes.

```bash
kubectl get nodes
```

Example:

```text
NAME           STATUS   ROLES           AGE
master-node    Ready    control-plane   20d
worker-node    Ready    <none>          20d
```

If both commands work successfully, your `kubeconfig` is correctly configured.

---

# Building the Kubernetes MCP Server

The server is built using **FastMCP**.

* [Server.py](/MCP/custom-k8-mcp-server/server.py)


# Available MCP Tools

server currently exposes the following tools.

| Tool                | Description        |
| ------------------- | ------------------ |
| create_namespace    | Create a namespace |
| list_namespace_pods | List Pods          |
| get_pod_logs        | Read Pod logs      |
| delete_pod          | Delete Pods        |
| list_deployments    | List Deployments   |
| restart_deployment  | Rolling restart    |
| scale_deployment    | Scale replicas     |
| list_services       | List Services      |
| list_nodes          | List Cluster Nodes |
| list_namespaces     | List Namespaces    |

---

# Running the MCP Server

Install dependencies

```bash
pip install -r requirements.txt
```

Run the server

```bash
python server.py
```

The server starts and waits for JSON-RPC requests over standard input/output.

---

# Connecting with Cloudy Desktop

##  — Locate Claude Desktop Configuration

Claude Desktop stores MCP server definitions inside:

```
claude_desktop_config.json
```

## Open the configuration

Inside Claude Desktop:

```
Settings
      ↓
Developer
      ↓
Edit Config
```

Claude automatically opens the configuration file.

---

# Step 3 — Configure Kubernetes MCP Server

Replace your configuration with:

```json
{
  "mcpServers": {
    "kubernetes": {
      "command": "python",
      "args": [
        "C:\\Users\\akash\\OneDrive\\Desktop\\AI-Assisted-DevOps\\MCP\\custom-k8-mcp-server\\server.py"
      ]
    }
  }
}
```

- Save the file.

* Restart Cloudy Desktop after updating the configuration.

When Cloudy Desktop launches, it starts your MCP server automatically and discovers all registered tools.

---

# Testing the Server

Once connected, open a new chat in Cloudy Desktop.

Try prompts like:

```
List all Pods.
```

```
Show all namespaces.
```


Cloudy Desktop selects the appropriate tool, invokes the MCP server, and displays the response.

---