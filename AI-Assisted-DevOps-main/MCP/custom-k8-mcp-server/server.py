import logging
import sys
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from mcp.server.fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)

logger = logging.getLogger("k8s-mcp")

# ----------
# MCP Server
# ------------

mcp = FastMCP(
    name="Kubernetes MCP",
    instructions="""
This server provides Kubernetes management capabilities.

Always use these tools instead of generating kubectl commands.
Never generate kubectl commands when a tool exists.
"""
)

# --------
# Kubernetes Authentication
# --------

try:
    config.load_kube_config()

    v1 = client.CoreV1Api()
    apps = client.AppsV1Api()
    batch = client.BatchV1Api()

    logger.info("Connected to Kubernetes cluster")

except Exception as e:
    logger.exception(e)
    sys.exit(1)



@mcp.tool()
def create_namespace(name: str) -> str:
    """Create a Kubernetes namespace."""

    try:
        body = client.V1Namespace(
            metadata=client.V1ObjectMeta(name=name)
        )

        v1.create_namespace(body)

        return f"Namespace '{name}' created successfully."

    except ApiException as e:
        return str(e)
    
# -------------
# PODS
# -------------

@mcp.tool()
def list_namespace_pods(namespace: str = "default") -> str:
    """List all pods inside a namespace."""
    try:
        pods = v1.list_namespaced_pod(namespace)

        if not pods.items:
            return "No pods found."

        result = []

        for pod in pods.items:
            result.append(
                f"{pod.metadata.name} | {pod.status.phase} | Node={pod.spec.node_name}"
            )

        return "\n".join(result)

    except ApiException as e:
        return str(e)


@mcp.tool()
def get_pod_logs(
    pod_name: str,
    namespace: str = "default",
    tail_lines: int = 100,
) -> str:
    """Read pod logs."""

    try:
        return v1.read_namespaced_pod_log(
            pod_name,
            namespace,
            tail_lines=tail_lines,
        )

    except ApiException as e:
        return str(e)


@mcp.tool()
def delete_pod(
    pod_name: str,
    namespace: str = "default",
) -> str:
    """Delete a pod."""

    try:
        v1.delete_namespaced_pod(pod_name, namespace)
        return f"Deleted pod {pod_name}"

    except ApiException as e:
        return str(e)


# -----------
# DEPLOYMENTS
# -----------

@mcp.tool()
def list_deployments(namespace: str = "default") -> str:
    """List deployments."""

    try:

        deployments = apps.list_namespaced_deployment(namespace)

        if not deployments.items:
            return "No deployments found."

        output = []

        for d in deployments.items:

            ready = d.status.ready_replicas or 0
            replicas = d.spec.replicas

            output.append(
                f"{d.metadata.name} | Ready={ready}/{replicas}"
            )

        return "\n".join(output)

    except ApiException as e:
        return str(e)


@mcp.tool()
def restart_deployment(
    deployment_name: str,
    namespace: str = "default",
) -> str:
    """Rolling restart deployment."""

    try:

        from datetime import datetime

        body = {
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "kubectl.kubernetes.io/restartedAt":
                            datetime.utcnow().isoformat()
                        }
                    }
                }
            }
        }

        apps.patch_namespaced_deployment(
            deployment_name,
            namespace,
            body,
        )

        return f"Restart triggered for {deployment_name}"

    except ApiException as e:
        return str(e)


@mcp.tool()
def scale_deployment(
    deployment_name: str,
    replicas: int,
    namespace: str = "default",
) -> str:
    """Scale deployment."""

    try:

        body = {
            "spec": {
                "replicas": replicas
            }
        }

        apps.patch_namespaced_deployment_scale(
            deployment_name,
            namespace,
            body,
        )

        return f"Scaled {deployment_name} to {replicas}"

    except ApiException as e:
        return str(e)


# -----------
# SERVICES (NEW)
# ---------

@mcp.tool()
def list_services(namespace: str = "default") -> str:
    """List Kubernetes Services."""

    try:

        services = v1.list_namespaced_service(namespace)

        if not services.items:
            return "No services."

        return "\n".join(
            f"{s.metadata.name} | {s.spec.type} | {s.spec.cluster_ip}"
            for s in services.items
        )

    except ApiException as e:
        return str(e)


# ---------------
# NODES
# ----------------

@mcp.tool()
def list_nodes() -> str:
    """List Kubernetes nodes."""

    try:

        nodes = v1.list_node()

        return "\n".join(
            f"{n.metadata.name} | {n.status.conditions[-1].type}"
            for n in nodes.items
        )

    except ApiException as e:
        return str(e)


# --------------------
# NAMESPACES
# ---------------

@mcp.tool()
def list_namespaces() -> str:
    """List Kubernetes namespaces."""

    try:

        namespaces = v1.list_namespace()

        return "\n".join(
            ns.metadata.name
            for ns in namespaces.items
        )

    except ApiException as e:
        return str(e)



if __name__ == "__main__":
    logger.info("Starting Kubernetes MCP Server")
    mcp.run()