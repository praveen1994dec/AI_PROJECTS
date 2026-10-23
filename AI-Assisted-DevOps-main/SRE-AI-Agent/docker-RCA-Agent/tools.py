"""
tools.py
Diagnostic tools powered by the Python Docker SDK.
"""

import json
import docker
from langchain_core.tools import tool

# Initialize Docker Client SDK
try:
    docker_client = docker.from_env()
except Exception as e:
    docker_client = None

@tool
def list_containers(all_containers: bool = True) -> str:
    """List Docker containers with their IDs, Names, Status, Image, and Ports.
    Set all_containers=True to include stopped/crashed containers.
    """
    if not docker_client:
        return "Error: Docker daemon is not running or accessible."
    try:
        containers = docker_client.containers.list(all=all_containers)
        if not containers:
            return "No containers found."
        
        result = []
        for c in containers:
            ports = ", ".join([f"{k}->{v}" for k, v in (c.ports or {}).items() if v])
            result.append({
                "id": c.short_id,
                "name": c.name,
                "status": c.status,
                "image": c.image.tags[0] if c.image.tags else c.image.short_id,
                "ports": ports or "None"
            })
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error listing containers: {str(e)}"


@tool
def get_logs(container_name: str, tail_lines: int = 50) -> str:
    """Get the last N lines of logs (stdout & stderr) from a specific container."""
    if not docker_client:
        return "Error: Docker daemon is not running or accessible."
    try:
        container = docker_client.containers.get(container_name)
        logs = container.logs(tail=tail_lines, timestamps=True).decode("utf-8", errors="replace")
        return logs if logs else "Logs are empty."
    except docker.errors.NotFound:
        return f"Error: Container '{container_name}' not found."
    except Exception as e:
        return f"Error getting logs: {str(e)}"


@tool
def inspect_container_state(container_name: str) -> str:
    """Inspect critical execution state (Exit code, OOMKilled, Health, RestartCount, Mounts, Env vars).
    Use this to perform Root Cause Analysis (RCA) on why a container crashed or failed to start.
    """
    if not docker_client:
        return "Error: Docker daemon is not running or accessible."
    try:
        container = docker_client.containers.get(container_name)
        state = container.attrs.get("State", {})
        config = container.attrs.get("Config", {})
        host_config = container.attrs.get("HostConfig", {})
        
        rca_data = {
            "Name": container.name,
            "Status": state.get("Status"),
            "Running": state.get("Running"),
            "ExitCode": state.get("ExitCode"),
            "OOMKilled": state.get("OOMKilled"),
            "Error": state.get("Error"),
            "RestartCount": container.attrs.get("RestartCount"),
            "Health": state.get("Health", {}).get("Status", "No Healthcheck Configured"),
            "Env": config.get("Env", []),
            "RestartPolicy": host_config.get("RestartPolicy", {}).get("Name"),
            "Mounts": [m.get("Destination") for m in container.attrs.get("Mounts", [])]
        }
        return json.dumps(rca_data, indent=2)
    except docker.errors.NotFound:
        return f"Error: Container '{container_name}' not found."
    except Exception as e:
        return f"Error inspecting container: {str(e)}"


@tool
def check_docker_stats(container_name: str) -> str:
    """Get a single snapshot of container resource usage (CPU, Memory limit, Memory usage)."""
    if not docker_client:
        return "Error: Docker daemon is not running or accessible."
    try:
        container = docker_client.containers.get(container_name)
        stats = container.stats(stream=False)
        
        mem_usage = stats.get("memory_stats", {}).get("usage", 0) / (1024 * 1024)
        mem_limit = stats.get("memory_stats", {}).get("limit", 0) / (1024 * 1024)
        
        return json.dumps({
            "MemoryUsageMB": round(mem_usage, 2),
            "MemoryLimitMB": round(mem_limit, 2),
            "CpuTotalUsage": stats.get("cpu_stats", {}).get("cpu_usage", {}).get("total_usage")
        }, indent=2)
    except Exception as e:
        return f"Error getting stats: {str(e)}"


# Export list of tools for easy importing
ALL_TOOLS = [
    list_containers,
    get_logs,
    inspect_container_state,
    check_docker_stats
]