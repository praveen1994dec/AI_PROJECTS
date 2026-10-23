import json
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode

from agent.state import AgentState
from tools.terraform_tools import (
    write_terraform_files,
    run_terraform_fmt_and_validate,
    run_security_scans,
    run_infracost_breakdown,
    read_remote_state # <-- Import the new tool here
)

@tool
def check_existing_infrastructure(bucket: str, key: str, region: str) -> str:
    """Reads the existing Terraform state from an AWS S3 backend.
    Call this FIRST when the user asks to modify or add to existing infrastructure.
    
    Args:
        bucket: The S3 bucket name storing the state.
        key: The path/key to the state file (e.g., 'vpc/terraform.tfstate').
        region: The AWS region of the S3 bucket.
    """
    return read_remote_state(bucket, key, region)

@tool
def write_code(files_dict: dict) -> str:
    """Writes the generated HCL code to standard Terraform files in the workspace.
    Argument 'files_dict' should be a dictionary mapping filenames (e.g. 'main.tf') to string content.
    """
    return write_terraform_files(files_dict)

@tool
def validate_code() -> str:
    """Runs terraform fmt, init, and validate. Use this after writing code. 
    If it returns errors, you MUST rewrite the code to fix them."""
    res = run_terraform_fmt_and_validate()
    return json.dumps(res)

@tool
def scan_security() -> str:
    """Runs tfsec and tflint. Run this ONLY if validate_code succeeds."""
    res = run_security_scans()
    return json.dumps(res)

@tool
def estimate_cost() -> str:
    """Runs Infracost to estimate cloud spend. Run this after security scans pass."""
    res = run_infracost_breakdown()
    return json.dumps(res)

agent_tools = [check_existing_infrastructure, write_code, validate_code, scan_security, estimate_cost]
tool_node = ToolNode(agent_tools)

SYSTEM_PROMPT = """You are an expert AWS Terraform AI Agent.
Your objective is to generate production-ready, secure AWS HCL code based on user requests.

Your strict workflow:
1. STATE CHECK: If the user is modifying or adding to existing infrastructure, use `check_existing_infrastructure` FIRST to understand what is currently deployed. If the user didn't provide S3 bucket details, ask them for it.
2. GENERATION: Generate the HCL code based on the user's request.
   - CRITICAL RULE FOR EXISTING INFRASTRUCTURE: NEVER write `resource` blocks for infrastructure that already exists (discovered in Step 1). You MUST use Terraform `data` blocks (e.g., `data "aws_vpc"`, `data "aws_subnet"`) to reference existing resources by their IDs or tags.
   - ONLY write `resource` blocks for the brand NEW infrastructure being requested.
   - You MUST include an S3 `backend.tf` block so the GitHub Actions pipeline syncs with the remote state. 
   - Use `write_code` to save all files.
3. VALIDATION: Use `validate_code` to check for syntax errors. If it fails, rewrite the code and test again.
4. SECURITY: Once VALIDATION checks pass, use `scan_security` to check for misconfigurations. Fix any HIGH/CRITICAL issues.
5. COST: Once all checks pass, use `estimate_cost` to get the pricing.
6. ERROR HANDLING: If you attempt to fix validation or security errors 2 times and they STILL fail, you MUST STOP calling tools. Return a final summary to the user explaining what the persistent error is so the human can fix it manually. Do NOT keep retrying in an endless loop.
7. SUMMARY: Return a final text summary indicating success, cost, and architecture. Do NOT output raw Terraform code in your final message.
"""

def call_model(state: AgentState) -> dict:
    """Calls Claude 3.5 Sonnet with the current state and tools."""
    llm = ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0)
    llm_with_tools = llm.bind_tools(agent_tools)
    
    messages = state["messages"]
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        
    response = llm_with_tools.invoke(messages)
    
    return {"messages": [response]}