import os
import subprocess
import json
from typing import Dict, Any

WORKSPACE_DIR = os.path.abspath("workspace")

def _ensure_workspace():
    """Ensure the workspace directory exists."""
    if not os.path.exists(WORKSPACE_DIR):
        os.makedirs(WORKSPACE_DIR)

def read_remote_state(bucket: str, key: str, region: str) -> str:
    """Configures the S3 backend and reads the current infrastructure state."""
    _ensure_workspace()

    backend_hcl = f"""
terraform {{
  backend "s3" {{
    bucket = "{bucket}"
    key    = "{key}"
    region = "{region}"
  }}
}}
"""
    filepath = os.path.join(WORKSPACE_DIR, "backend.tf")
    with open(filepath, "w") as f:
        f.write(backend_hcl)

    init_res = subprocess.run(
        ["terraform", "init", "-reconfigure"], 
        cwd=WORKSPACE_DIR, 
        capture_output=True, 
        text=True
    )
    if init_res.returncode != 0:
        return f"Failed to connect to S3 backend. Error:\n{init_res.stderr or init_res.stdout}"

    show_res = subprocess.run(
        ["terraform", "show", "-no-color"], 
        cwd=WORKSPACE_DIR, 
        capture_output=True, 
        text=True
    )
    
    state_output = show_res.stdout.strip()
    
    if not state_output or "No state" in state_output:
        return "The S3 remote state is empty. No existing infrastructure found."

    return f"CURRENT AWS INFRASTRUCTURE STATE:\n{state_output}"


def write_terraform_files(files: Dict[str, str]) -> str:
    """
    Writes generated HCL code to standard files in the workspace.
    
    Args:
        files: Dictionary where key is filename (e.g. 'main.tf') and value is HCL code.
    """
    _ensure_workspace()
    for filename, content in files.items():
        filepath = os.path.join(WORKSPACE_DIR, filename)
        with open(filepath, "w") as f:
            f.write(content)
    return f"Successfully wrote files to {WORKSPACE_DIR}: {list(files.keys())}"

def run_terraform_fmt_and_validate() -> Dict[str, Any]:
    """Runs terraform fmt and terraform validate inside the workspace."""
    _ensure_workspace()

    subprocess.run(["terraform", "fmt"], cwd=WORKSPACE_DIR, capture_output=True, text=True)
    
    init_res = subprocess.run(
        ["terraform", "init", "-backend=false"], 
        cwd=WORKSPACE_DIR, 
        capture_output=True, 
        text=True
    )
    if init_res.returncode != 0:
        return {"success": False, "stage": "init", "error": init_res.stderr or init_res.stdout}

    val_res = subprocess.run(
        ["terraform", "validate", "-json"], 
        cwd=WORKSPACE_DIR, 
        capture_output=True, 
        text=True
    )
    
    try:
        val_data = json.loads(val_res.stdout)
        if not val_data.get("valid", False):
            errors = [diag.get("detail", diag.get("summary")) for diag in val_data.get("diagnostics", [])]
            return {"success": False, "stage": "validate", "error": "\n".join(errors)}
    except json.JSONDecodeError:
        if val_res.returncode != 0:
            return {"success": False, "stage": "validate", "error": val_res.stderr or val_res.stdout}

    return {"success": True, "stage": "validate", "output": "Terraform syntax and configuration are valid."}

def run_security_scans() -> Dict[str, Any]:
    """Runs tflint and tfsec security analyzers."""
    _ensure_workspace()
    errors = []

    # Run tflint
    tflint_res = subprocess.run(["tflint", "--format", "json"], cwd=WORKSPACE_DIR, capture_output=True, text=True)
    if tflint_res.returncode != 0 and tflint_res.stdout:
        try:
            tf_json = json.loads(tflint_res.stdout)
            for issue in tf_json.get("issues", []):
                errors.append(f"[TFLint] {issue['message']} in {issue['call']['filename']}:{issue['call']['line']}")
        except json.JSONDecodeError:
            pass

    # Run tfsec
    tfsec_res = subprocess.run(["tfsec", "--format", "json"], cwd=WORKSPACE_DIR, capture_output=True, text=True)
    if tfsec_res.stdout:
        try:
            sec_json = json.loads(tfsec_res.stdout)
            results = sec_json.get("results", [])
            if results:
                for res in results:
                    if res.get("severity") in ["HIGH", "CRITICAL"]:
                        errors.append(f"[TFSec {res['severity']}] {res['description']} (Rule: {res['rule_id']})")
        except json.JSONDecodeError:
            pass

    if errors:
        return {"success": False, "stage": "security", "error": "\n".join(errors)}
    
    return {"success": True, "stage": "security", "output": "No HIGH/CRITICAL security violations found."}

def run_infracost_breakdown() -> Dict[str, Any]:
    """Calculates estimated monthly AWS cost using Infracost."""
    _ensure_workspace()
    
    res = subprocess.run(
        ["infracost", "breakdown", "--path", WORKSPACE_DIR, "--format", "json"],
        cwd=WORKSPACE_DIR,
        capture_output=True,
        text=True
    )
    
    if res.returncode != 0:
        return {"total_monthly_cost": "N/A", "currency": "USD", "error": res.stderr}

    try:
        cost_data = json.loads(res.stdout)
        total_cost = cost_data.get("totalMonthlyCost", "0.00")
        currency = cost_data.get("currency", "USD")
        return {
            "total_monthly_cost": f"${float(total_cost):,.2f}",
            "currency": currency,
            "raw_summary": cost_data.get("summary", {})
        }
    except Exception as e:
        return {"total_monthly_cost": "N/A", "error": str(e)}