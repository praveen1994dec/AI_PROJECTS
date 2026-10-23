import json
import re
from typing import Optional, Dict, Any, List
from kubernetes import client, config
from langchain_core.tools import tool

# Initialize K8s client
try:
    config.load_incluster_config()
except config.ConfigException:
    config.load_kube_config()

v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()


def _get_deployment_owner(pod_name: str, namespace: str) -> Optional[str]:
    """Helper: Traverses OwnerReferences (Pod -> ReplicaSet -> Deployment) to resolve deployment name."""
    try:
        pod = v1.read_namespaced_pod(name=pod_name, namespace=namespace)
        owner_refs = pod.metadata.owner_references or []
        
        for ref in owner_refs:
            if ref.kind == "Deployment":
                return ref.name
            elif ref.kind == "ReplicaSet":
                # Fetch ReplicaSet to find its parent Deployment
                rs = apps_v1.read_namespaced_replica_set(name=ref.name, namespace=namespace)
                rs_owners = rs.metadata.owner_references or []
                for rs_ref in rs_owners:
                    if rs_ref.kind == "Deployment":
                        return rs_ref.name
        return None
    except Exception:
        return None


def _parse_memory_to_bytes(mem_str: str) -> int:
    """Helper: Converts K8s memory strings (e.g., '128Mi', '1Gi') to bytes."""
    units = {
        'Ki': 1024,
        'Mi': 1024**2,
        'Gi': 1024**3,
        'Ti': 1024**4,
        'K': 1000,
        'M': 1000**2,
        'G': 1000**3,
    }
    match = re.match(r'^(\d+)([A-Za-z]+)?$', mem_str.strip())
    if not match:
        raise ValueError(f"Invalid memory string format: {mem_str}")
    value, unit = match.groups()
    return int(value) * units.get(unit, 1)


def _bytes_to_memory_str(num_bytes: int) -> str:
    """Helper: Converts bytes to Kubernetes Mi string."""
    mi_val = int(num_bytes / (1024**2))
    return f"{mi_val}Mi"


@tool
def get_failing_pods(namespace: str = "default") -> str:
    """Scans a Kubernetes namespace and returns a JSON array of failing pods with detected root deployment names."""
    failing_pods = []
    pods = v1.list_namespaced_pod(namespace)

    for pod in pods.items:
        pod_name = pod.metadata.name
        statuses = pod.status.container_statuses or []

        for status in statuses:
            waiting = status.state.waiting
            terminated = status.state.terminated

            reason = None
            if waiting and waiting.reason in ["CrashLoopBackOff", "ImagePullBackOff", "ErrImagePull"]:
                reason = waiting.reason
            elif terminated and terminated.reason in ["OOMKilled", "Error"]:
                reason = terminated.reason

            if reason:
                deployment_name = _get_deployment_owner(pod_name, namespace)
                failing_pods.append({
                    "pod_name": pod_name,
                    "namespace": namespace,
                    "reason": reason,
                    "container": status.name,
                    "deployment_owner": deployment_name or "Not derived / Standalone Pod"
                })

    return json.dumps(failing_pods, indent=2)


@tool
def get_pod_diagnostics(pod_name: str, namespace: str = "default") -> str:
    """Fetches diagnostic details for a pod, including active/previous logs (tail_lines=200), sorted warning events, and specs."""
    try:
        pod = v1.read_namespaced_pod(name=pod_name, namespace=namespace)
    except Exception as e:
        return json.dumps({"error": f"Failed to retrieve pod: {str(e)}"})

    # 1. Fetch Current & Previous Logs (tail_lines=200)
    current_logs = ""
    previous_logs = ""
    try:
        current_logs = v1.read_namespaced_pod_log(name=pod_name, namespace=namespace, tail_lines=200)
    except Exception as e:
        current_logs = f"Notice: Could not fetch active logs ({str(e)})"

    try:
        previous_logs = v1.read_namespaced_pod_log(name=pod_name, namespace=namespace, tail_lines=200, previous=True)
    except Exception:
        previous_logs = "No previous container execution logs available."

    # 2. Fetch and Sort Events (Newest First by last_timestamp)
    events_raw = v1.list_namespaced_event(namespace, field_selector=f"involvedObject.name={pod_name}")
    sorted_events = sorted(
        events_raw.items,
        key=lambda x: (x.last_timestamp or x.event_time or x.metadata.creation_timestamp),
        reverse=True
    )

    formatted_events = [
        {
            "timestamp": str(e.last_timestamp or e.event_time or e.metadata.creation_timestamp),
            "type": e.type,
            "reason": e.reason,
            "message": e.message
        }
        for e in sorted_events[:15] # Top 15 newest events
    ]

    # 3. Extract Specs & Parent Deployment
    container_spec = pod.spec.containers[0]
    deployment_owner = _get_deployment_owner(pod_name, namespace)

    diagnostics = {
        "pod_name": pod_name,
        "namespace": namespace,
        "deployment_owner": deployment_owner,
        "container_name": container_spec.name,
        "current_image": container_spec.image,
        "image_pull_secrets": [s.name for s in (pod.spec.image_pull_secrets or [])],
        "resources_spec": container_spec.resources.to_dict() if container_spec.resources else {},
        "events_newest_first": formatted_events,
        "current_logs": current_logs,
        "previous_logs_prior_to_crash": previous_logs
    }

    return json.dumps(diagnostics, indent=2)


@tool
def restart_pod(pod_name: str, namespace: str = "default") -> str:
    """Deletes a pod to force its controller to recreate a fresh instance."""
    try:
        v1.delete_namespaced_pod(name=pod_name, namespace=namespace)
        return json.dumps({
            "status": "success",
            "message": f"Deleted pod '{pod_name}' in namespace '{namespace}' to trigger recreation."
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@tool
def update_container_image(
    deployment_name: str, 
    container_name: str, 
    target_image: str, 
    namespace: str = "default"
) -> str:
    """Updates the container image tag on a Deployment. Requires explicit target_image (never arbitrary fallbacks)."""
    if not target_image or target_image.strip() in ["nginx:latest", "latest"]:
        return json.dumps({
            "status": "rejected",
            "message": "Refused to apply default or unverified image. Please specify the explicit validated target image."
        })

    body = {
        "spec": {
            "template": {
                "spec": {
                    "containers": [{"name": container_name, "image": target_image}]
                }
            }
        }
    }
    try:
        apps_v1.patch_namespaced_deployment(deployment_name, namespace, body)
        return json.dumps({
            "status": "success",
            "message": f"Successfully updated deployment '{deployment_name}' container '{container_name}' image to '{target_image}'."
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@tool
def increase_container_memory(
    deployment_name: str, 
    container_name: str, 
    namespace: str = "default",
    suggested_memory_limit: Optional[str] = None
) -> str:
    """Calculates and applies a scaled memory limit bump based on current limits or explicit suggested limits."""
    try:
        dep = apps_v1.read_namespaced_deployment(name=deployment_name, namespace=namespace)
        containers = dep.spec.template.spec.containers
        target_container = next((c for c in containers if c.name == container_name), containers[0])

        current_resources = target_container.resources.to_dict() if target_container.resources else {}
        limits = current_resources.get("limits") or {}
        current_mem_str = limits.get("memory", "128Mi")

        # Determine target memory limit
        if suggested_memory_limit:
            new_mem_str = suggested_memory_limit
        else:
            # Safely scale current memory by 1.5x or minimum 256Mi
            current_bytes = _parse_memory_to_bytes(current_mem_str)
            scaled_bytes = int(current_bytes * 1.5)
            min_bytes = _parse_memory_to_bytes("256Mi")
            new_mem_str = _bytes_to_memory_str(max(scaled_bytes, min_bytes))

        body = {
            "spec": {
                "template": {
                    "spec": {
                        "containers": [{
                            "name": target_container.name,
                            "resources": {
                                "limits": {"memory": new_mem_str},
                                "requests": {"memory": new_mem_str}
                            }
                        }]
                    }
                }
            }
        }
        
        apps_v1.patch_namespaced_deployment(deployment_name, namespace, body)
        return json.dumps({
            "status": "success",
            "previous_memory_limit": current_mem_str,
            "new_memory_limit": new_mem_str,
            "message": f"Successfully updated deployment '{deployment_name}' memory limit from {current_mem_str} to {new_mem_str}."
        })

    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})