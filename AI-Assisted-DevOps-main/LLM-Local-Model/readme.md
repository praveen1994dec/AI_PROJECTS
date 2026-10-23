# Large Language Models (LLMs) - 
---

# 1. What is an LLM?

## Definition

**LLM (Large Language Model)** is an Artificial Intelligence model trained on enormous amounts of text data that understands and generates human-like language.

It predicts the **next most likely word (token)** based on everything that came before it.

Example:

```
Input:
Linux is an operating...

Prediction:
system
```

```
Input:
Kubernetes is used for...

Prediction:
container orchestration
```

The model doesn't memorize answers like a database.

Instead, it learns **patterns**, **grammar**, **reasoning**, **programming**, **documentation**, and **language relationships**.

---

## Think of an LLM like this

```
Books
Blogs
Wikipedia
GitHub
Research Papers
Documentation
StackOverflow
News

        ↓

 Training

        ↓

Large Language Model

        ↓

You ask a question

        ↓

Model predicts the best answer
```

---

## Popular LLMs

Open Source

* Llama
* Mistral
* Qwen
* Gemma
* DeepSeek
* Phi

Closed Source

* GPT
* Claude
* Gemini

---

# 5. Local Models vs Hosted Models

## Local Model

The model runs on **your own machine**.

No internet is required after downloading the model.

Examples

* Ollama
* Docker Model Runner

---

## Hosted Model

The model runs in the cloud.

```
Your App

↓

Internet

↓

OpenAI API

↓

GPT

↓

Response
```

Examples

* OpenAI
* Anthropic
* Google
* Together AI
* Groq

---

## Local vs Hosted Comparison

| Feature     | Local Model                   | Hosted Model                |
| ----------- | ----------------------------- | --------------------------- |
| Internet    | Not required                  | Required                    |
| Privacy     | Excellent                     | Depends on provider         |
| Latency     | Very low                      | Depends on network          |
| Cost        | Hardware only                 | Pay per request/token       |
| Speed       | Depends on hardware           | High-performance cloud GPUs |
| Setup       | Initial installation required | Minimal                     |
| Fine-tuning | Supported                     | Limited                     |
| Maintenance | User-managed                  | Provider-managed            |
| Scalability | Limited by hardware           | Easily scalable             |

---

# 6. Advantages of Running Models Locally

Running an LLM locally provides several benefits:

## 1. Privacy

Your prompts and data never leave your computer.

Ideal for:

* Company source code
* Internal documentation
* Customer data
* Production logs

---

## 2. No API Cost

No charges for:

* Tokens
* Requests
* API subscriptions

After downloading the model, you can use it repeatedly without per-request fees.

---

## 3. Offline Usage

Works without internet after the model is downloaded.

Useful for:

* Secure environments
* Air-gapped networks
* Travel
* Restricted corporate networks

---

## 4. Faster Response (No Network Delay)

No internet round-trip.

```
Python

↓

Local Model

↓

Answer
```

---

## 5. Better Customization

You can:

* Change prompts
* Add RAG
* Fine-tune models
* Build custom AI assistants

---

## 6. Better Security

Sensitive data remains inside your infrastructure.

Examples:

* Kubernetes logs
* AWS credentials (handle carefully)
* Infrastructure configurations
* CI/CD pipelines

---

## 7. Full Control

You decide:

* Which model to use
* Which version to install
* When to upgrade
* Hardware allocation

---

# 7. Options to Run Local LLMs

There are multiple ways to run local models.

For beginners, two of the most popular options are:

1. Ollama
2. Docker Model Runner (DMR)

---

# Option 1 — Ollama

## What is Ollama?

Ollama is a lightweight tool that makes it easy to download, manage, and run open-source LLMs locally.

Think of it as:

```
Docker

is for Containers

↓

Ollama

is for AI Models
```

---

## Pros

* Extremely easy to use
* Excellent documentation
* Large model library
* Great community support
* Perfect for learning and prototypes

---

## Cons

* Runs outside the Docker ecosystem
* Less integrated with containerized workflows

---

# Option 2 — Docker Model Runner (DMR)

## What is Docker Model Runner?

Docker Model Runner (DMR) is Docker's built-in capability for running AI models using Docker Desktop.

It enables developers to manage containers and AI models within the same Docker environment.

---

## Pros

* Excellent for Docker users
* Fits naturally into container-based development
* Centralized management of containers and models
* Ideal for AI-assisted DevOps projects

---

## Cons

* Newer ecosystem than Ollama
* Smaller model ecosystem
* Fewer community tutorials

---

# Running Llama Model Locally Using Ollama

---

## 1. Install Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

---

# 5. Verify Installation

Open a terminal and run:

```bash
ollama --version
```
---

# 6. Download a Llama Model

Ollama automatically downloads models when you run them for the first time.

For example:

```bash
ollama pull llama3
```

What happens?

```
Command

↓

Checks local storage

↓

Model not found

↓

Downloads model

↓

Stores locally

↓

Starts the model
```

After the first download, future runs use the local copy.

---

# 7. Run the Model

Start an interactive chat session:

```bash
ollama run llama3
```

Example:

```text
>>> Explain Kubernetes.
```

Response:

```text
Kubernetes is an open-source container orchestration platform...
```

Exit the chat using:

```text
/bye
```

---

# 8. Chat with the Model

Example interaction:

```text
>>> What is Docker?

Docker is a container platform...

>>> Write a Python script.

Sure! Here's a Python example...

>>> Explain Terraform.

Terraform is an Infrastructure as Code tool...
```

The conversation remains in context until you exit.

---

# 9. List Installed Models

View all locally installed models:

```bash
ollama list
```


# 10. Remove a Model

Delete an installed model:

```bash
ollama rm llama3
```


## Show installed models

```bash
ollama list
```
---
## Manual Usage vs Automation with Ollama

Running a model from the terminal is useful for learning, testing prompts, and experimenting. However, real-world AI applications and AI-Assisted DevOps platforms rarely interact with the model manually. Instead, they communicate with Ollama through its REST API.

---

# Option 1: Manual Usage (CLI)

In manual mode, you interact directly with the model using the terminal.

Example:

```bash
ollama run llama3
```

You can then ask questions such as:

```text
>>> Explain Kubernetes.
>>> Generate a Dockerfile.
>>> Write a Jenkins Pipeline.
>>> Explain this error log.
```
---
# Option 2: Automation Using the Ollama REST API

In production applications, users do **not** type prompts into the terminal. Instead, applications send HTTP requests to Ollama's REST API, receive responses, and process them automatically.

This is how AI-powered software, automation tools, and DevOps assistants interact with local LLMs.

Example architecture:

```text
Python Script
      │
      ▼
HTTP POST Request
      │
      ▼
Ollama REST API (localhost:11434)
      │
      ▼
Llama Model
      │
      ▼
Generated Response

```
---

# Why Use the API Instead of the CLI?

The REST API allows your programs to communicate with the model automatically without any manual interaction.

Benefits include:

* Automate repetitive tasks
* Integrate AI into Python scripts
* Build AI-powered DevOps tools
* Process logs automatically
* Generate Kubernetes YAML
* Review CI/CD pipelines
* Analyze infrastructure issues
* Create chatbots and internal assistants
* Connect AI with web applications and microservices

# Running Llama Model Locally using Docker Model Runner (DMR)
---

# Prerequisites

Before starting, ensure you have:

* Docker Desktop installed
* Docker Desktop updated to the latest version
* Docker Model Runner enabled
* Internet connection (only for downloading the model)
* At least:

  * 8 GB RAM (minimum)
  * 16 GB RAM (recommended)
  * 20 GB free storage

---

# Step 1 — Verify Docker Installation

Open a terminal and run:

```bash
docker --version
```

If Docker information is displayed, Docker Desktop is running successfully.

---

# Step 2 — Verify Docker Model Runner

Check whether Docker Model Runner is available:

```bash
docker model version
```

If a version is displayed, DMR is installed correctly.

---

# Step 3 — Search Available Models

View available models:

```bash
docker model list
```

Example output:

```
ai/llama3.2
ai/mistral
ai/gemma
ai/qwen
```

---

# Step 4 — Download the Llama Model

Pull the model to your local machine:

```bash
docker model pull ai/llama3.2
```

Docker downloads the model weights.

This step may take several minutes depending on your internet speed.

---

# Step 5 — Verify Downloaded Models

List downloaded models:

```bash
docker model list
```

Example:

```
MODEL

ai/llama3.2
```

---

# Step 6 — Run the Model

Start an interactive chat session:

```bash
docker model run ai/llama3.2
```

Example:

```
You:
Explain Kubernetes

AI:
Kubernetes is an open-source container orchestration platform...
```

The model is now running locally.

---

# Step 8 — Running Through REST API

Docker Model Runner exposes a local API.

Example endpoint:

```
http://localhost:12434
```

You can send prompts from any programming language.

---


Example:

```
User

↓

Python Script

↓

Docker Model Runner

↓

Llama Model

↓

Generated Response
```

---