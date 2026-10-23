# 🚀 DevOps RAG System using Ollama, LangChain, ChromaDB & Sentence Transformers

> Build your own **100% Local AI-powered DevOps Assistant** using Retrieval-Augmented Generation (RAG). Query your Kubernetes manifests, Terraform code, Jenkins pipelines, Dockerfiles, and infrastructure documentation using natural language—all without sending data to external APIs.

---

# 📖 Overview

This project solves that problem by building a **Retrieval-Augmented Generation (RAG)** system that understands your DevOps repository and answers questions using your own project files.

The entire solution runs **locally** using **Ollama**, **LangChain**, **ChromaDB**, and **Sentence Transformers**, ensuring complete privacy while providing intelligent AI-powered answers.

Instead of relying on the LLM's general knowledge, the system retrieves the most relevant documents from your repository and uses them as context before generating the final answer.

---

# 🎯 Why Build a DevOps RAG System?

Large Language Models are knowledgeable, but they do not know anything about your own infrastructure.

For example:

* Your Kubernetes manifests
* Terraform modules
* Jenkins pipelines
* Dockerfiles
* Internal DevOps documentation
* Organization-specific configurations

Without RAG, an LLM may:

* Hallucinate infrastructure details
* Generate incorrect Kubernetes commands
* Assume Terraform resources that do not exist
* Ignore your organization's deployment standards

A RAG system solves this by retrieving relevant project files first and then asking the LLM to answer using only those retrieved documents.

---

# ❌ Problems Without RAG

Traditional AI assistants:

* Cannot understand your project repository
* Have no access to internal DevOps documentation
* Frequently hallucinate answers
* Cannot reference actual infrastructure files
* Produce generic responses instead of project-specific ones

Example:

Question:

> Which Kubernetes Deployment exposes the payment service?

Without RAG:

> The model guesses based on public Kubernetes examples.

With RAG:

> The model retrieves the exact Deployment YAML from your repository and answers accurately.

---

# ✅ Benefits of Using RAG

* Private AI assistant
* No cloud APIs required
* Runs completely offline
* Understands your own DevOps repository
* Reduces hallucinations
* Source-aware responses
* Easily extendable
* Faster knowledge retrieval
* Better developer productivity

---

# 🛠 Technology Stack

| Category             | Technology                        |
| -------------------- | --------------------------------- |
| Programming Language | Python                            |
| LLM                  | Ollama (Llama 3)                  |
| Framework            | LangChain                         |
| Vector Database      | ChromaDB                          |
| Embedding Model      | Sentence Transformers             |
| Embedding Library    | HuggingFace Embeddings            |
| Text Splitter        | Recursive Character Text Splitter |
| Document Loader      | Directory Loader                  |
| Retrieval Method     | Semantic Similarity Search        |
| Interface            | Command Line                      |

---

# 📁 Project Structure

```
project/
│
├── data/
│   ├── kubernetes/
│   ├── terraform/
│   ├── Jenkinsfile
│   └── Dockerfile
│
├── modules/
│   ├── loader.py
│   ├── splitter.py
│   ├── vector_store.py
│
├── ingest.py
├── app.py
├── chroma_db/
├── requirements.txt
└── README.md
```

---
<p align="center">
  <img src="/RAG-for-devops/architecture.png" alt="DevOps RAG Architecture" width="800">
</p>
---

# 🏗 System Architecture

```
                 DevOps Repository
                        │
                        ▼
             Document Loader (LangChain)
                        │
                        ▼
            Recursive Text Splitter
                        │
                        ▼
      Sentence Transformer Embeddings
                        │
                        ▼
            Store in ChromaDB Vector DB
                        │
──────────────────────────────────────────────

                 User Question
                        │
                        ▼
             Similarity Search (Top-K)
                        │
                        ▼
           Retrieved DevOps Chunks
                        │
                        ▼
        Prompt Augmentation with Context
                        │
                        ▼
            Ollama (Llama 3 Local LLM)
                        │
                        ▼
          AI Generated Answer + Sources
```

---

# 📚 Step-by-Step Implementation Guide

## Step 1 — Prepare the DevOps Repository

Create a `data/` directory containing your DevOps resources.

Typical examples include:

* Kubernetes YAML files
* Terraform files
* Dockerfiles
* Jenkinsfiles
* Configuration files
* Internal documentation

This repository becomes the knowledge base for the AI assistant.

---

## Step 2 — Load Documents

[loader.py](/RAG-for-devops/RAG-Pipeline-Devops/modules/loader.py)

The first stage scans the entire repository recursively.

Responsibilities:

* Traverse every folder
* Detect supported files
* Read file contents
* Preserve metadata
* Return LangChain Document objects

This creates a unified representation of all project documents.

---

## Step 3 — Split Documents into Chunks

[splitter.py](/RAG-for-devops/RAG-Pipeline-Devops/modules/splitter.py)

Large files cannot be embedded efficiently.

Therefore the documents are divided into smaller overlapping chunks.

Benefits:

* Better semantic search
* Reduced embedding size
* Improved retrieval accuracy
* Maintains contextual continuity

Each chunk remembers its original source file.

---
[vector_store.py](/RAG-for-devops/RAG-Pipeline-Devops/modules/vector_store.py)

## Step 4 — Generate Vector Embeddings

Each chunk is converted into a numerical vector using the Sentence Transformer embedding model.

These vectors capture semantic meaning rather than simple keywords.

Advantages include:

* Understands similar concepts
* Finds related content
* Better than keyword matching
* Language-aware retrieval

---

## Step 5 — Store Embeddings in ChromaDB

The generated embeddings are stored inside a local Chroma vector database.

Each stored record contains:

* Document chunk
* Embedding vector
* Metadata
* Source filename

This database becomes the searchable knowledge base.

---
[app.py](/RAG-for-devops/RAG-Pipeline-Devops/app.py)

## Step 6 — Ask Questions

The user enters a natural language question.

Examples:

* Which Deployment exposes payment-service?
* Explain this Jenkins pipeline.
* What Terraform providers are configured?
* Which Docker image is used?
* How many Kubernetes Services exist?

---

## Step 7 — Retrieve Relevant Chunks

Instead of sending every document to the LLM, the system performs semantic similarity search.

It retrieves only the most relevant document chunks.

Typical retrieval:

Top 5 relevant chunks.

This dramatically reduces prompt size while improving answer quality.

---

## Step 8 — Prompt Augmentation

The retrieved chunks are combined into a single prompt.

The prompt instructs the LLM:

* Use only the provided context
* Do not hallucinate
* Say "I don't know" if the answer is not present

This is the "Augmented Generation" stage.

---

## Step 9 — Generate the Final Answer

The augmented prompt is sent to Ollama.

The LLM reads:

* User question
* Retrieved DevOps documents
* Prompt instructions

It then generates an accurate, context-aware answer.

---

## Step 10 — Display Sources

The application also prints the files used to generate the answer.

Example:

```
Sources Used

kubernetes/deployment.yaml

terraform/main.tf

Dockerfile
```

This increases transparency and trust.

---

# 🧠 How Retrieval-Augmented Generation Works

The RAG pipeline consists of two major phases:

## Phase 1 — Indexing

During indexing:

* Load documents
* Split documents
* Generate embeddings
* Store vectors in ChromaDB

This is typically performed once or whenever the knowledge base changes.

---

## Phase 2 — Retrieval and Generation

During querying:

* User asks a question
* Similarity search retrieves relevant chunks
* Context is added to the prompt
* Ollama generates an answer
* Sources are returned

This process happens for every user query.

---
