import os
import streamlit as st
import subprocess
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.errors import GraphRecursionError
from agent.graph import terraform_agent
from tools.terraform_tools import WORKSPACE_DIR


st.set_page_config(page_title="Terraform AI Provisioner", layout="wide")
st.title("🏗️ AWS AI Infrastructure Provisioner")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "generated_files" not in st.session_state:
    st.session_state.generated_files = {}
if "workflow_status" not in st.session_state:
    st.session_state.workflow_status = "idle" # states: idle, generating, review, deploying

def read_workspace_files():
    """Reads all .tf files from the workspace directory."""
    files_dict = {}
    if os.path.exists(WORKSPACE_DIR):
        for filename in os.listdir(WORKSPACE_DIR):
            if filename.endswith(".tf") or filename.endswith(".tfvars"):
                with open(os.path.join(WORKSPACE_DIR, filename), "r") as f:
                    files_dict[filename] = f.read()
    return files_dict

def clean_workspace():
    """Deletes all .tf files to reset state."""
    if os.path.exists(WORKSPACE_DIR):
        for filename in os.listdir(WORKSPACE_DIR):
            if filename.endswith((".tf", ".tfstate", ".tfstate.backup",".tfvars")):
                os.remove(os.path.join(WORKSPACE_DIR, filename))
    st.session_state.generated_files = {}

for msg in st.session_state.chat_history:
    role = "user" if isinstance(msg, HumanMessage) else "assistant"
    # We don't display tool messages in the main chat UI to keep it clean
    if role in ["user", "assistant"] and msg.content:
        st.chat_message(role).write(msg.content)

if prompt := st.chat_input("What infrastructure do you want to deploy?"):
    if st.session_state.workflow_status in ["review", "generating"]:
        st.warning("Please finish or discard the current deployment before starting a new one.")
    else:
        st.session_state.workflow_status = "generating"
        human_msg = HumanMessage(content=prompt)
        st.session_state.chat_history.append(human_msg)
        st.chat_message("user").write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Agent is reasoning, generating, and testing code..."):
                try:
                    config = {"recursion_limit": 20}
                    
                    # Invoke with the config
                    final_state = terraform_agent.invoke(
                        {"messages": st.session_state.chat_history}, 
                        config=config
                    )
                    
                    filtered_messages = [
                        msg for msg in final_state["messages"] 
                        if isinstance(msg, HumanMessage) or (isinstance(msg, AIMessage) and not msg.tool_calls)
                    ]


                    st.session_state.chat_history = filtered_messages
                    
                    # The last message is Claude's final text summary
                    final_response = final_state["messages"][-1].content
                    st.write(final_response)
                    
                    # Read the final validated code from the workspace
                    st.session_state.generated_files = read_workspace_files()
                    st.session_state.workflow_status = "review"
                    st.rerun()
                except Exception as e:
                    st.error(f"Agent Execution Failed: {str(e)}")
                    st.session_state.workflow_status = "idle"

if st.session_state.workflow_status == "review" and st.session_state.generated_files:
    st.divider()
    st.subheader("🔎 Review Generated Infrastructure")
    
    # Display files in tabs
    tabs = st.tabs(list(st.session_state.generated_files.keys()))
    for i, (filename, content) in enumerate(st.session_state.generated_files.items()):
        with tabs[i]:
            st.code(content, language="hcl")
            
    st.divider()
    col1, col2 = st.columns(2)


    with col1:
        if st.button("🚀 Create Repo & Open PR", type="primary", use_container_width=True):
            with st.spinner("Creating repository, pushing pipeline and code, and opening PR..."):
                try:
                    timestamp = datetime.now().strftime('%Y%m%d%H%M')
                    repo_name = f"aws-tf-infrastructure-{timestamp}"
                    branch_name = f"agent-deploy-{timestamp}"
                    

                    workflows_dir = os.path.join(WORKSPACE_DIR, ".github", "workflows")
                    os.makedirs(workflows_dir, exist_ok=True)
         
                    pipeline_yaml = """name: 'Terraform CI/CD'
on:
  pull_request:
    branches: [ main ]
  push:
    branches: [ main ]
env:
  AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
  AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
  AWS_REGION: ${{ secrets.AWS_REGION }}
jobs:
  terraform:
    name: 'Terraform Plan & Apply'
    runs-on: ubuntu-latest
    steps:
    - name: Checkout Repository
      uses: actions/checkout@v4
    - name: Setup Terraform
      uses: hashicorp/setup-terraform@v3
      with:
        terraform_version: "1.5.0"
    - name: Terraform Init
      run: terraform init
    - name: Terraform Plan
      if: github.event_name == 'pull_request'
      run: terraform plan 
    - name: Terraform Apply
      if: github.ref == 'refs/heads/main' && github.event_name == 'push'
      run: terraform apply -auto-approve -input=false
"""
                    with open(os.path.join(workflows_dir, "terraform.yml"), "w") as f:
                        f.write(pipeline_yaml)

                    subprocess.run(["git", "init"], cwd=WORKSPACE_DIR, check=True)
                    subprocess.run(["git", "checkout", "-b", "main"], cwd=WORKSPACE_DIR, check=False)
                    subprocess.run(["git", "add", ".github/"], cwd=WORKSPACE_DIR, check=True)
                    subprocess.run(["git", "commit", "-m", "chore: Add CI/CD pipeline"], cwd=WORKSPACE_DIR, check=True)

                    subprocess.run([
                        "gh", "repo", "create", repo_name, 
                        "--private", 
                        "--source=.", 
                        "--remote=origin",
                        "--push"
                    ], cwd=WORKSPACE_DIR, check=True)
                    

                    subprocess.run(["git", "checkout", "-b", branch_name], cwd=WORKSPACE_DIR, check=True)
                    subprocess.run(["git", "add", "*.tf"], cwd=WORKSPACE_DIR, check=True)
                    subprocess.run(["git", "commit", "-m", "feat: Auto-generated AWS infrastructure"], cwd=WORKSPACE_DIR, check=True)
                    
                    subprocess.run(["git", "push", "-u", "origin", branch_name], cwd=WORKSPACE_DIR, check=True)

                    subprocess.run([
                        "gh", "pr", "create", 
                        "--title", "Deploy: Agent Generated Infrastructure", 
                        "--body", "Automated infrastructure deployment generated by the Terraform AI Agent. Please review the pipeline `terraform plan` output.",
                        "--base", "main",
                        "--head", branch_name
                    ], cwd=WORKSPACE_DIR, check=True)
                    
                    st.success(f"Successfully created repo `{repo_name}` and opened a Pull Request! Your pipeline is now running in GitHub.")
                    st.session_state.workflow_status = "idle"
                    clean_workspace() 
                    
                except subprocess.CalledProcessError as e:
                    st.error(f"GitHub CLI or Git command failed. Error: {e}")
    with col2:
        if st.button("❌ Discard", use_container_width=True):
            clean_workspace()
            st.session_state.workflow_status = "idle"
            st.warning("Workspace cleared. Deployment aborted.")
            st.rerun()