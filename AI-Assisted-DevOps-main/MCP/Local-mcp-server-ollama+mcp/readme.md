# 🚀 Build a Custom GitHub MCP Server with Your Own MCP Client using Ollama (100% Local)

> Build your own **Model Context Protocol (MCP)** server and client from scratch, integrate it with **GitHub**, and run everything **100% locally** using **Ollama Llama 3.2** without relying on Cloud-hosted AI assistants.

---

# ⭐ Project Overview

existing MCP client like **Cloudy Desktop** (or similar AI desktop clients).

While that is great for getting started, in production there are several limitations:

* ❌ Hosted by a third party
* ❌ Limited customization
* ❌ Limited control over tool execution
* ❌ Data leaves your machine
* ❌ Can become expensive
* ❌ Hard to integrate into your own applications
* ❌ Not ideal for enterprise security requirements

This project solves that problem by building everything ourselves.

We will build:

```
GitHub API
      │
      │
      ▼
Custom GitHub MCP Server
      │
      │ SSE
      ▼
Custom MCP Client
      │
      │ Tool Calling
      ▼
Ollama (Llama 3.2)
      │
      ▼
Final AI Response
```

Everything runs **locally**.

No OpenAI API.

No Claude API.

No hosted AI.

No external MCP client.

---

# Why Build Your Own MCP Client?

Many developers use AI desktop applications such as Cloudy Desktop because they already implement an MCP client.

The problem is that these clients are general-purpose tools.

For real-world AI applications, we usually want:

* Complete ownership
* Full customization
* Better security
* Offline execution
* Local LLM support
* Enterprise deployment
* Integration into our own software

Instead of depending on another application, we can simply build our own MCP client in Python.

---

# Why Not Use Cloudy Desktop?

Cloudy Desktop is an excellent application for learning MCP.

However, it has some limitations when building production systems.

## 1. Hosted Application

The client itself is maintained by another company.

You do not control how it evolves.

---

## 2. Limited Customization

You cannot easily customize:

* AI workflow
* Tool execution
* Memory
* Prompt routing
* Logging
* Authentication
* Business logic

---

## 3. Security

Many organizations require:

* Internal AI
* Private infrastructure
* Local execution
* Air-gapped environments

A custom client gives full control over security.

---

## 4. Cost

Many hosted AI assistants require:

* API keys
* Monthly subscriptions
* Usage limits

With Ollama:

* No API cost
* No token cost
* Unlimited local inference

---

## 5. Complete Ownership

You own:

* MCP Client
* MCP Server
* AI Model
* Tool Execution
* Logging
* Security
* Deployment

---

# Tech Stack

* Python
* FastMCP
* Ollama
* Llama 3.2
* PyGithub
* SSE Transport
* AsyncIO
* MCP Python SDK

---

# Features

Current MCP tools:

* List repositories
* Get repository information
* Create repository
* Delete repository

Resources:

* GitHub Server Information

Prompts:

* GitHub Assistant Prompt

Everything is automatically discovered by the client.

No hardcoding.

---


# Step-by-Step Implementation

## Step 1 — Install Ollama

Install Ollama.

Pull the model.

```
ollama pull llama3.2
```

Verify:

```
ollama list
```

---

## Step 2 — Clone the Repository

```
git clone https://github.com/akashkayande/AI-Assited-Devops.git

cd MCP/local-mcp-server-ollama+mcp
```

---

## Step 3 — Create Virtual Environment

Windows

```
python -m venv .venv

.venv\Scripts\activate
```
---

## Step 4 — Install Dependencies

* [requirements.txt](/MCP/Local-mcp-server-ollama+mcp/requirement.txt)
```
pip install -r requirements.txt
```

---

## Step 5 — Create GitHub Personal Access Token

Generate a GitHub Personal Access Token with the required repository permissions and store it securely.

---

## Step 6 — Configure Environment Variables

Create:

```
.env
```

```
GITHUB_TOKEN=your_github_token
```

---

## Step 7 — Start Ollama

```
ollama serve
```

---

## Step 8 — Start the MCP Server

* [server.py](/MCP/Local-mcp-server-ollama+mcp/server.py)
```
python server.py
```

Server:

```
http://localhost:9090/sse
```

---

## Step 9 — Run the Custom MCP Client

* [client.py](/MCP/Local-mcp-server-ollama+mcp/client.py)
```
python client.py
```

---

## Step 10 — Ask Questions

```
List repositories of torvalds
```

```
Create repository called AI-Demo
```

```
Delete repository username/test-repo
```

```
Get information of repository owner/repo
```

---

# How Tool Calling Works

```
User Prompt
      │
      ▼
Ollama
      │
      ▼
Needs GitHub Information?
      │
      ├── No
      │      │
      │      ▼
      │  Return Answer
      │
      ▼
Yes
      │
      ▼
Call MCP Tool
      │
      ▼
GitHub MCP Server
      │
      ▼
GitHub API
      │
      ▼
Return JSON
      │
      ▼
Ollama
      │
      ▼
Final AI Response
```

---