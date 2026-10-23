# 🚀 CI/CD RCA Agent

An AI-powered **CI/CD Root Cause Analysis (RCA) Agent** that automatically investigates failed **GitHub Actions** workflow runs using **LangChain**, **Ollama**, and the **GitHub CLI**.

Instead of manually searching through workflow logs, commit history, and workflow YAML files, the agent performs an automated investigation and generates a structured **Root Cause Analysis (RCA)** report with actionable remediation steps.

---


# ⚙️ How It Works

The agent follows a systematic troubleshooting workflow.

```text
User Question
      │
      ▼
Find Failed Workflow Run
      │
      ▼
Download Failed Logs
      │
      ▼
Inspect Recent Git Changes
      │
      ▼
Read Workflow YAML
      │
      ▼
Analyze with LLM
      │
      ▼
Generate RCA Report
```

---

# 🧰 Built-in Diagnostic Tools

## 1. List Workflow Runs

Retrieves recent failed GitHub Actions workflow runs.

```python
list_workflow_runs()
```

Returns

- Workflow Name
- Run ID
- Branch
- Commit SHA
- Status
- Created Time

---

## 2. Get Failed Logs

Downloads failure-focused logs.

```python
get_failed_logs(run_id)
```

Useful for identifying:

- Build failures
- Test failures
- Deployment failures
- Authentication issues
- Missing dependencies

---

## 3. Get Recent Commit Diff

Retrieves recent code changes.

```python
get_recent_commit_diff()
```

Helps correlate failures with recent commits.

---

## 4. Read Workflow File

Reads GitHub Actions workflow YAML.

```python
get_workflow_file("ci.yml")
```

Useful for detecting:

- YAML syntax errors
- Incorrect action versions
- Missing permissions
- Invalid environment variables

---

# 📦 Prerequisites

- Python 3.11+
- Git
- GitHub CLI (`gh`)
- Ollama
- Gemma 4 model

---

# ▶️ Running the Agent

```bash
python app.py
```

Example

```text
🚀 GitHub Actions CI/CD Failure Analyzer

> Why did the latest workflow fail?
```

---

# 📌 Example Output

```text
Symptom
--------
The Build job failed during dependency installation.

Root Cause
----------
The requirements.txt file referenced a package version
that does not exist on PyPI.

Remediation
-----------
1. Update the package version.
2. Commit the changes.
3. Re-run the workflow.

Preventive Actions
------------------
Pin dependency versions and validate them locally before merging.
```

---

# 🛠️ Tech Stack

| Technology | Purpose |
|------------|----------|
| Python | Application |
| LangChain | Agent Framework |
| Ollama | Local LLM Runtime |
| Gemma 4 | AI Reasoning |
| GitHub CLI | Workflow Inspection |
| Git | Commit Analysis |

---
