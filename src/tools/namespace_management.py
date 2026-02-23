from typing import Dict, Any, Optional
import os
from kubernetes import client
from kubernetes.client.rest import ApiException

from ..utils.k8s_client import KubernetesClient

# Initialize client with kubeconfig directory from environment or default
kubeconfig_dir = os.environ.get('KUBECONFIG_DIR', os.path.expanduser('~/.kube'))
k8s_client = KubernetesClient(kubeconfig_dir)


async def k8s_create_namespace(context: str, name: str,
                                labels: Optional[Dict] = None,
                                annotations: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Create a new Kubernetes namespace.

    Args:
        context: The Kubernetes context to use
        name: The name of the namespace to create
        labels: Optional labels to apply to the namespace
        annotations: Optional annotations to apply to the namespace

    Returns:
        Dict with information about the created namespace

    Raises:
        RuntimeError: If there's an error creating the namespace
    """
    try:
        api_client = k8s_client.get_api_client(context)
        core_v1 = client.CoreV1Api(api_client)

        metadata = client.V1ObjectMeta(name=name)
        if labels:
            metadata.labels = labels
        if annotations:
            metadata.annotations = annotations

        namespace = client.V1Namespace(
            api_version="v1",
            kind="Namespace",
            metadata=metadata
        )

        result = core_v1.create_namespace(body=namespace)

        return {
            "status": "Success",
            "message": f"Successfully created namespace '{name}'",
            "namespace": {
                "name": result.metadata.name,
                "labels": result.metadata.labels,
                "status": result.status.phase,
                "created": result.metadata.creation_timestamp.isoformat() if result.metadata.creation_timestamp else None
            }
        }
    except ApiException as e:
        if e.status == 409:
            raise RuntimeError(f"Namespace '{name}' already exists")
        raise RuntimeError(f"Failed to create namespace '{name}': {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error creating namespace '{name}': {str(e)}")


async def k8s_delete_namespace(context: str, name: str) -> Dict[str, Any]:
    """
    Delete a Kubernetes namespace and all resources within it.

    Args:
        context: The Kubernetes context to use
        name: The name of the namespace to delete

    Returns:
        Dict with status information about the deletion

    Raises:
        RuntimeError: If there's an error deleting the namespace
    """
    try:
        api_client = k8s_client.get_api_client(context)
        core_v1 = client.CoreV1Api(api_client)

        # Safety check: prevent deleting system namespaces
        protected = {"default", "kube-system", "kube-public", "kube-node-lease"}
        if name in protected:
            raise RuntimeError(
                f"Cannot delete protected namespace '{name}'. "
                f"Protected namespaces: {', '.join(sorted(protected))}"
            )

        core_v1.delete_namespace(name=name)

        return {
            "status": "Success",
            "message": f"Namespace '{name}' deletion initiated (may take time to fully terminate)"
        }
    except ApiException as e:
        if e.status == 404:
            raise RuntimeError(f"Namespace '{name}' not found")
        raise RuntimeError(f"Failed to delete namespace '{name}': {str(e)}")
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Error deleting namespace '{name}': {str(e)}")
