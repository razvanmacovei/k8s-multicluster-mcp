import os
from typing import Any, Dict, List

from kubernetes import client

from ..utils.k8s_client import KubernetesClient

# Initialize client with kubeconfig directory from environment or default
kubeconfig_dir = os.environ.get("KUBECONFIG_DIR", os.path.expanduser("~/.kube"))
k8s_client = KubernetesClient(kubeconfig_dir)


async def list_k8s_namespaces(context: str) -> List[str]:
    """
    List all namespaces in a specified Kubernetes context.

    Args:
        context (str): Name of the Kubernetes context to use

    Returns:
        List[str]: A list of namespace names

    Raises:
        RuntimeError: If there's an error accessing the Kubernetes API
    """
    try:
        # KubernetesClient.get_api_client now handles partial context matching
        api_client = k8s_client.get_api_client(context)
        core_v1 = client.CoreV1Api(api_client)
        namespaces = core_v1.list_namespace()
        return [ns.metadata.name for ns in namespaces.items]
    except ValueError as e:
        raise RuntimeError(str(e))
    except Exception as e:
        raise RuntimeError(f"Failed to list namespaces in context '{context}': {str(e)}")
