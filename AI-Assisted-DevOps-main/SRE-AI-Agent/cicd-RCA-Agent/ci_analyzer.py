import os
import re
import pathlib
import subprocess
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langchain.agents import create_agent as create_react_agent

# ------------------------------------------------------------------
# 1. CI/CD & Git Diagnostic Tools
# ------------------------------------------------------------------

@tool
def list_workflow_runs(status: str = "failure", limit: int = 5) -> str:
    """List recent GitHub Actions workflow runs (default: failures).
    Returns run ID, status, workflow name, branch, and commit hash.
    """
    try:
        result = subprocess.run(
            ["gh", "run", "list", "--status", status, "--limit", str(limit), 
             "--json", "databaseId,name,headBranch,headSha,conclusion,createdAt"],
            capture_output=True, text=True, check=True
        )
        return result.stdout or "No workflow runs found."
    except subprocess.CalledProcessError as e:
        return f"Error executing 'gh run list': {e.stderr}"


@tool
def get_failed_logs(run_id: str) -> str:
    """Get sanitized, failure-focused step logs for a specific GitHub Actions run ID."""
    try:
        result = subprocess.run(
            ["gh", "run", "view", str(run_id), "--log-failed"],
            capture_output=True, text=True
        )
        output = result.stdout + result.stderr
        return output
    except Exception as e:
        return f"Error fetching logs for run {run_id}: {str(e)}"


@tool
def get_recent_commit_diff(commit_sha: str = "HEAD~1") -> str:
    """Get the git diff for recent code changes. 
    Use this to correlate CI failures with recent code modifications.
    """
    try:
        result = subprocess.run(
            ["git", "diff", commit_sha],
            capture_output=True, text=True
        )
        diff = result.stdout
        if not diff:
            return "No diff found for the specified commit context."
        return diff
    except Exception as e:
        return f"Error fetching git diff: {str(e)}"


@tool
def get_workflow_file(workflow_name: str) -> str:
    """Read a GitHub Actions workflow YAML file from .github/workflows/ (e.g., 'ci.yml')."""
    # Prevent directory traversal attacks
    clean_name = os.path.basename(workflow_name)
    path = pathlib.Path(f".github/workflows/{clean_name}")
    
    if path.exists():
        return path.read_text()[:4000] # Cap workflow size
    return f"Workflow file not found at: {path}"


# ------------------------------------------------------------------
# 2. SRE System Prompt
# ------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert DevOps and SRE CI/CD Failure Analyzer. Your task is to perform Root Cause Analysis (RCA) on GitHub Actions workflow failures.

Follow this systematic investigation process:
1. If no run ID is given, use `list_workflow_runs` to locate recent failed runs.
2. Fetch the failure logs using `get_failed_logs(run_id)`.
3. Inspect code changes using `get_recent_commit_diff` or workflow definitions using `get_workflow_file` to see if a recent change caused the failure.
4. Synthesize your final answer into a clear RCA report structured as:
   - **Symptom**: Which job/step failed and what error message was thrown.
   - **Root Cause**: The underlying reason (e.g., syntax error, missing dependency, flaky test, bad secret/permission).
   - **Remediation**: Exact, step-by-step fix (e.g., YAML correction, code change, dependency update).

Keep your explanations technical, concise, and focused on practical fixes.
"""

# Initialize Ollama & Agent
llm = ChatOllama(model="gemma4", temperature=0)
tools = [list_workflow_runs, get_failed_logs, get_recent_commit_diff, get_workflow_file]

agent = create_react_agent(llm, tools)


# ------------------------------------------------------------------
# 3. Interactive CLI Loop
# ------------------------------------------------------------------

print("\n🚀 GitHub Actions CI/CD Failure Analyzer")
print("------------------------------------------")
print("Ask me about pipeline failures (e.g., 'Why did the last run fail?'). Type 'quit' to exit.\n")

messages_history = [SystemMessage(content=SYSTEM_PROMPT)]

while True:
    question = input("> ").strip()
    if question.lower() in ("quit", "exit", "q"):
        break
    if not question:
        continue

    print("\nAnalyzing pipeline logs & git context...\n")
    
    messages_history.append(("user", question))

    try:
        result = agent.invoke({"messages": messages_history})
        final_answer = result["messages"][-1].content
        
        print(final_answer)
        print()
        
        # Save response in memory for follow-up questions
        messages_history.append(("assistant", final_answer))
        
    except Exception as e:
        print(f"Error during execution: {str(e)}\n")