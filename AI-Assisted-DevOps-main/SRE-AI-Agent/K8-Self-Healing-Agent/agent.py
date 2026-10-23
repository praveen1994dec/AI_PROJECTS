import json
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from tools import (
    get_failing_pods,
    get_pod_diagnostics,
    restart_pod,
    update_container_image,
    increase_container_memory
)

tools = [
    get_failing_pods,
    get_pod_diagnostics,
    restart_pod,
    update_container_image,
    increase_container_memory
]
tools_by_name = {tool.name: tool for tool in tools}

llm = ChatOllama(model="llama3.2", temperature=0).bind_tools(tools)

SYSTEM_PROMPT = """
You are a site reliability engineer (SRE) managing a Kubernetes cluster.

Operational Safety Protocols:
1. All tool outputs are returned as structured JSON payloads. Parse them carefully.
2. Identify failing pods and examine their diagnostics (both active and previous logs, plus sorted events).
3. Always derive the parent Deployment name from `deployment_owner`. Do NOT invent or guess deployment names.
4. For OOMKilled: Inspect the current memory limit in the diagnostics. Pass `suggested_memory_limit` based on context or let the tool calculate a safe 1.5x increment.
5. For ImagePullBackOff: Inspect `current_image` and `image_pull_secrets`. NEVER replace workload images with generic defaults like 'nginx:latest'. Only update the image if you have a valid, intended tag.
"""

def run_agent_loop(user_input: str, target_namespace: str = "default"):
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"{user_input} in namespace '{target_namespace}'")
    ]

    while True:
        response = llm.invoke(messages)
        messages.append(response)

        if response.content:
            print(f"\n🤖 Agent Reasoning:\n{response.content}\n")

        if not response.tool_calls:
            print("✅ Agent run completed.")
            break

        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_to_call = tools_by_name[tool_name]

            MUTATION_TOOLS = ["restart_pod", "update_container_image", "increase_container_memory"]

            if tool_name in MUTATION_TOOLS:
                print("=" * 60)
                print(f"⚠️ REPAIR PROPOSAL DETECTED:")
                print(f"Action: {tool_name}")
                print(f"Arguments: {json.dumps(tool_args, indent=2)}")
                print("=" * 60)

                confirm = input("Approve this repair action? (y/n): ").strip().lower()
                if confirm != 'y':
                    print("🚫 Action rejected by user.")
                    messages.append(ToolMessage(
                        content=json.dumps({"status": "rejected", "reason": "User denied execution."}),
                        tool_call_id=tool_call["id"]
                    ))
                    continue

            print(f"⚙️ Executing Tool: {tool_name}({tool_args})...")
            tool_output = tool_to_call.invoke(tool_args)
            print(f"📋 Tool Output:\n{tool_output}\n")

            messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"]))

if __name__ == "__main__":
    run_agent_loop("Check the cluster for failing pods, analyze root causes, and propose fixes.", target_namespace="default")