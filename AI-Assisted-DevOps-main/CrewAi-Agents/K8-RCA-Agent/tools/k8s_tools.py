import os
import yaml
from kubernetes import client, config
from kubernetes.client import ApiClient
from kubernetes.client.rest import ApiException
from crewai.tools import tool

# --- FIX: Environment Configuration ---
# This allows the app to run both locally and deployed inside a Kubernetes cluster.
try:
    config.load_incluster_config()
except config.ConfigException:
    kubeconfig_path = os.path.expanduser(os.getenv('KUBECONFIG', '~/.kube/config'))
    config.load_kube_config(config_file=kubeconfig_path)

v1 = client.CoreV1Api()

# --- FIX: Smarter Multi-Container & CrashLoop Logs ---
@tool("Get Pod Logs")
def get_pod_logs(pod_name: str, namespace: str = "default") -> str:
    """
    Fetches the last 200 lines of logs from a specific pod.
    Automatically handles multi-container pods (including InitContainers) 
    and recovers logs from previously crashed instances (CrashLoopBackOff).
    """
    try:
        # First, fetch the pod object to discover all container names
        pod = v1.read_namespaced_pod(name=pod_name, namespace=namespace)
        
        all_logs = []
        containers = []
        
        # Gather both init containers and standard containers
        if pod.spec.init_containers:
            containers.extend([c.name for c in pod.spec.init_containers])
        if pod.spec.containers:
            containers.extend([c.name for c in pod.spec.containers])
            
        for container_name in containers:
            all_logs.append(f"\n--- Logs for container: {container_name} ---")
            
            # Helper function to attempt fetching logs safely
            def fetch_logs(previous_flag=False):
                try:
                    return v1.read_namespaced_pod_log(
                        name=pod_name, 
                        namespace=namespace, 
                        container=container_name,
                        tail_lines=200,
                        previous=previous_flag
                    )
                except ApiException:
                    # ApiException is thrown if previous logs don't exist yet
                    return None
            
            # 1. Try getting current logs
            logs = fetch_logs(previous_flag=False)
            
            # 2. If current logs are empty, the pod might be in CrashLoopBackOff. 
            #    Attempt to fetch the previous crashed instance.
            if not logs or logs.strip() == "":
                prev_logs = fetch_logs(previous_flag=True)
                if prev_logs and prev_logs.strip():
                    all_logs.append("[PREVIOUS CRASH LOGS RECOVERED]")
                    all_logs.append(prev_logs)
                else:
                    all_logs.append("Logs are empty or container has not started.")
            else:
                all_logs.append(logs)
                
        return "\n".join(all_logs)
        
    except Exception as e:
        return f"Error fetching logs for pod {pod_name}: {str(e)}"

@tool("Get Pod Events")
def get_pod_events(pod_name: str, namespace: str = "default") -> str:
    """
    Fetches Kubernetes events for a specific pod. 
    Use this to identify scheduling issues, OOMKilled errors, ImagePullBackOff, or node evictions.
    """
    try:
        field_selector = f"involvedObject.name={pod_name},involvedObject.namespace={namespace}"
        events = v1.list_namespaced_event(namespace=namespace, field_selector=field_selector)
        
        if not events.items:
            return "No recent events found for this pod."
            
        event_details = []
        for event in events.items:
            event_details.append(
                f"Type: {event.type} | Reason: {event.reason} | Message: {event.message}"
            )
        return "\n".join(event_details)
    except Exception as e:
        return f"Error fetching events for pod {pod_name}: {str(e)}"

@tool("Get Pod Status")
def get_pod_status(pod_name: str, namespace: str = "default") -> str:
    """
    Fetches the current status, conditions, and restart counts of a specific pod.
    """
    try:
        pod = v1.read_namespaced_pod(name=pod_name, namespace=namespace)
        
        status_info = f"Phase: {pod.status.phase}\nConditions:\n"
        if pod.status.conditions:
            for cond in pod.status.conditions:
                status_info += f" - {cond.type}: {cond.status} ({cond.reason})\n"
                
        if pod.status.container_statuses:
            status_info += "Container Statuses:\n"
            for c in pod.status.container_statuses:
                restarts = c.restart_count
                # Safely extract state type (running, waiting, terminated)
                state = list(c.state.to_dict().keys())[0] if c.state else "unknown"
                status_info += f" - Name: {c.name}, Restarts: {restarts}, State: {state}\n"
                
        return status_info
    except Exception as e:
        return f"Error fetching status for pod {pod_name}: {str(e)}"

@tool("Get Pod YAML")
def get_pod_yaml(pod_name: str, namespace: str = "default") -> str:
    """
    Fetches the complete YAML configuration (manifest) of a specific pod.
    Use this to check resource limits (CPU/Memory), environment variables, 
    image tags, liveness/readiness probes, and volume mounts.
    """
    try:
        pod = v1.read_namespaced_pod(name=pod_name, namespace=namespace)
        
        api_client = ApiClient()
        pod_dict = api_client.sanitize_for_serialization(pod)
        
        if 'metadata' in pod_dict and 'managedFields' in pod_dict['metadata']:
            del pod_dict['metadata']['managedFields']
            
        return yaml.dump(pod_dict)
    except Exception as e:
        return f"Error fetching YAML for pod {pod_name}: {str(e)}"