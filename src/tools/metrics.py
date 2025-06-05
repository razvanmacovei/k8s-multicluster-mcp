from typing import List, Dict, Any, Optional
import os
from kubernetes import client
from ..utils.k8s_client import KubernetesClient

# Initialize client with kubeconfig directory from environment or default
kubeconfig_dir = os.environ.get("KUBECONFIG_DIR", os.path.expanduser("~/.kube"))
k8s_client = KubernetesClient(kubeconfig_dir)


async def top_k8s_nodes(context: str) -> List[Dict[str, Any]]:
    """
    Display resource usage (CPU/memory) of nodes in a Kubernetes cluster.

    Args:
        context (str): Name of the Kubernetes context to use

    Returns:
        List[Dict[str, Any]]: A list of node resource usage information

    Raises:
        RuntimeError: If there's an error accessing the Kubernetes API
    """
    try:
        api_client = k8s_client.get_api_client(context)

        # Use the metrics API
        metrics_api = client.CustomObjectsApi(api_client)
        nodes_metrics = metrics_api.list_cluster_custom_object(
            group="metrics.k8s.io", version="v1beta1", plural="nodes"
        )

        # Get regular node information for additional context
        core_api = client.CoreV1Api(api_client)
        nodes = core_api.list_node()
        node_info = {node.metadata.name: node for node in nodes.items}

        result = []
        for item in nodes_metrics.get("items", []):
            node_name = item["metadata"]["name"]
            node = node_info.get(node_name)

            # Extract CPU and memory usage
            cpu_usage = item["usage"]["cpu"]
            memory_usage = item["usage"]["memory"]

            # Get capacity if available
            capacity = {}
            if node:
                capacity = {
                    "cpu": node.status.capacity.get("cpu"),
                    "memory": node.status.capacity.get("memory"),
                    "pods": node.status.capacity.get("pods"),
                }

            result.append(
                {
                    "name": node_name,
                    "usage": {"cpu": cpu_usage, "memory": memory_usage},
                    "capacity": capacity,
                    "conditions": (
                        [
                            {"type": condition.type, "status": condition.status, "reason": condition.reason}
                            for condition in node.status.conditions
                        ]
                        if node and node.status.conditions
                        else []
                    ),
                }
            )

        return result

    except Exception as e:
        raise RuntimeError(f"Failed to get node metrics: {str(e)}")


async def top_k8s_pods(context: str, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Display resource usage (CPU/memory) of pods in a Kubernetes cluster.

    Args:
        context (str): Name of the Kubernetes context to use
        namespace (str, optional): Namespace to list pod metrics from. If None, get metrics for all namespaces

    Returns:
        List[Dict[str, Any]]: A list of pod resource usage information

    Raises:
        RuntimeError: If there's an error accessing the Kubernetes API
    """
    try:
        api_client = k8s_client.get_api_client(context)

        # Use the metrics API
        metrics_api = client.CustomObjectsApi(api_client)

        if namespace:
            pods_metrics = metrics_api.list_namespaced_custom_object(
                group="metrics.k8s.io", version="v1beta1", namespace=namespace, plural="pods"
            )
        else:
            pods_metrics = metrics_api.list_cluster_custom_object(
                group="metrics.k8s.io", version="v1beta1", plural="pods"
            )

        result = []
        for pod in pods_metrics.get("items", []):
            pod_name = pod["metadata"]["name"]
            pod_namespace = pod["metadata"]["namespace"]

            containers = []
            for container in pod.get("containers", []):
                containers.append(
                    {
                        "name": container["name"],
                        "usage": {"cpu": container["usage"]["cpu"], "memory": container["usage"]["memory"]},
                    }
                )

            result.append({"name": pod_name, "namespace": pod_namespace, "containers": containers})

        return result

    except Exception as e:
        raise RuntimeError(f"Failed to get pod metrics: {str(e)}")
