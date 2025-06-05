import os
from typing import List

from ..utils.k8s_client import KubernetesClient

# Initialize client with kubeconfig directory from environment or default
kubeconfig_dir = os.environ.get("KUBECONFIG_DIR", os.path.expanduser("~/.kube"))
k8s_client = KubernetesClient(kubeconfig_dir)


async def list_k8s_contexts() -> List[str]:
    """
    List all available Kubernetes contexts from the kubeconfig files.

    Returns:
        List[str]: A list of available Kubernetes context names

    Raises:
        RuntimeError: If there's an error accessing the kubeconfig files
    """
    try:
        return k8s_client.refresh_contexts()
    except Exception as e:
        raise RuntimeError(f"Failed to list Kubernetes contexts: {str(e)}")
