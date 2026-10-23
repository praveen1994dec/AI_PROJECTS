import os
import re
import sys
from pathlib import Path
import anthropic

# Initialize Anthropic client (automatically reads ANTHROPIC_API_KEY from environment)
client = anthropic.Anthropic()

def propose_fix():
    # Safe file reads with fallbacks using pathlib
    error_log_path = Path("/tmp/error.log")
    diff_path = Path("/tmp/diff.txt")
    changed_path = Path("/tmp/changed.txt")

    error_log = error_log_path.read_text(encoding="utf-8") if error_log_path.exists() else ""
    diff = diff_path.read_text(encoding="utf-8") if diff_path.exists() else ""
    
    changed_files = []
    if changed_path.exists():
        changed_files = [line.strip() for line in changed_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    # Read relevant content of changed files (limited to first 5)
    file_contents_list = []
    for f in changed_files[:5]:
        f_path = Path(f)
        try:
            if f_path.exists() and f_path.is_file():
                content = f_path.read_text(encoding="utf-8")
                file_contents_list.append(f"--- File: {f} ---\n{content}")
            else:
                file_contents_list.append(f"--- File: {f} --- (File missing or deleted)")
        except Exception:
            file_contents_list.append(f"--- File: {f} --- (Unreadable)")

    file_contents = "\n\n".join(file_contents_list)

    prompt = f"""You are a Principal DevOps and Software Engineer fixing a CI build failure.
Analyze the logs and code changes below and generate a minimal unified patch.

## CI Failure Logs
{error_log or "No log files captured."}

## Recent Commit Diff
{diff}

## Relevant File Contents
{file_contents}

## Requirements:
1. Identify the single root cause.
2. Provide a MINIMAL unified diff patch that can be applied directly using 'git apply'.
3. The diff header MUST use relative repository paths (e.g., a/path/to/file.js b/path/to/file.js).

Output your response using EXACTLY this schema:
CONFIDENCE: [HIGH|MEDIUM|LOW]
EXPLANATION: [Brief sentence]
---PATCH---
[Valid git unified diff content]
---END---"""

    # Call Claude API
    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=3000,
        temperature=0.1,
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.content[0].text

    # Parse confidence and patch block using regular expressions
    confidence_match = re.search(r"CONFIDENCE:\s*(HIGH|MEDIUM|LOW)", text, re.IGNORECASE)
    patch_match = re.search(r"---PATCH---([\s\S]*?)---END---", text)

    github_output = os.getenv("GITHUB_OUTPUT")

    if patch_match and patch_match.group(1).strip():
        patch_content = patch_match.group(1).strip() + "\n"
        confidence = confidence_match.group(1).upper() if confidence_match else "MEDIUM"

        Path("/tmp/proposed-fix.patch").write_text(patch_content, encoding="utf-8")
        Path("/tmp/confidence.txt").write_text(confidence, encoding="utf-8")

        if github_output:
            with open(github_output, "a", encoding="utf-8") as f:
                f.write("has_fix=true\n")
        print("Successfully generated AI patch.")
    else:
        print("No valid patch syntax received from AI model.")
        if github_output:
            with open(github_output, "a", encoding="utf-8") as f:
                f.write("has_fix=false\n")

if __name__ == "__main__":
    try:
        propose_fix()
    except Exception as err:
        print(f"AI fix generation execution error: {err}", file=sys.stderr)
        github_output = os.getenv("GITHUB_OUTPUT")
        if github_output:
            with open(github_output, "a", encoding="utf-8") as f:
                f.write("has_fix=false\n")
        sys.exit(1)