from typing import Dict, List, Any, Optional
import os
import base64
from kubernetes import client
from kubernetes.client.rest import ApiException

from ..utils.k8s_client import KubernetesClient

# Initialize client with kubeconfig directory from environment or default
kubeconfig_dir = os.environ.get('KUBECONFIG_DIR', os.path.expanduser('~/.kube'))
k8s_client = KubernetesClient(kubeconfig_dir)


async def k8s_list_secrets(context: str, namespace: Optional[str] = None,
                           label_selector: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List Kubernetes secrets with metadata (values are not exposed for security).

    Args:
        context: The Kubernetes context to use
        namespace: Namespace to list secrets from (all namespaces if not specified)
        label_selector: Label selector to filter secrets (e.g. 'app=myapp')

    Returns:
        List of secret metadata (keys only, no values for security)
    """
    try:
        api_client = k8s_client.get_api_client(context)
        core_v1 = client.CoreV1Api(api_client)

        kwargs = {}
        if label_selector:
            kwargs["label_selector"] = label_selector

        if namespace:
            secrets = core_v1.list_namespaced_secret(namespace=namespace, **kwargs)
        else:
            secrets = core_v1.list_secret_for_all_namespaces(**kwargs)

        return [
            {
                "name": secret.metadata.name,
                "namespace": secret.metadata.namespace,
                "type": secret.type,
                "keys": list(secret.data.keys()) if secret.data else [],
                "labels": secret.metadata.labels or {},
                "created": secret.metadata.creation_timestamp.isoformat() if secret.metadata.creation_timestamp else None
            }
            for secret in secrets.items
        ]
    except Exception as e:
        raise RuntimeError(f"Failed to list secrets: {str(e)}")


async def k8s_get_secret(context: str, name: str, namespace: str,
                         decode: bool = False) -> Dict[str, Any]:
    """
    Get a Kubernetes secret. By default returns only keys for security.
    Set decode=True to include base64-decoded values.

    Args:
        context: The Kubernetes context to use
        name: Name of the secret
        namespace: Namespace of the secret
        decode: Whether to include decoded values (default False for security)

    Returns:
        Dict with secret information
    """
    try:
        api_client = k8s_client.get_api_client(context)
        core_v1 = client.CoreV1Api(api_client)

        secret = core_v1.read_namespaced_secret(name=name, namespace=namespace)

        result = {
            "name": secret.metadata.name,
            "namespace": secret.metadata.namespace,
            "type": secret.type,
            "labels": secret.metadata.labels or {},
            "annotations": secret.metadata.annotations or {},
            "created": secret.metadata.creation_timestamp.isoformat() if secret.metadata.creation_timestamp else None,
        }

        if secret.data:
            if decode:
                result["data"] = {
                    k: base64.b64decode(v).decode("utf-8", errors="replace")
                    for k, v in secret.data.items()
                }
            else:
                result["keys"] = list(secret.data.keys())
                result["note"] = "Values hidden for security. Set decode=True to reveal values."
        else:
            result["data"] = {}

        return result
    except ApiException as e:
        if e.status == 404:
            raise RuntimeError(f"Secret '{name}' not found in namespace '{namespace}'")
        raise RuntimeError(f"Failed to get secret '{name}': {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error getting secret '{name}': {str(e)}")


async def k8s_create_secret(context: str, name: str, namespace: str,
                            data: Dict[str, str],
                            secret_type: str = "Opaque",
                            labels: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Create a Kubernetes secret.

    Args:
        context: The Kubernetes context to use
        name: Name of the secret to create
        namespace: Namespace to create the secret in
        data: Key-value pairs for the secret (values will be base64-encoded)
        secret_type: Type of secret (default: Opaque)
        labels: Optional labels to apply

    Returns:
        Dict with information about the created secret
    """
    try:
        api_client = k8s_client.get_api_client(context)
        core_v1 = client.CoreV1Api(api_client)

        # Base64 encode the values
        encoded_data = {
            k: base64.b64encode(v.encode("utf-8")).decode("utf-8")
            for k, v in data.items()
        }

        metadata = client.V1ObjectMeta(name=name, namespace=namespace)
        if labels:
            metadata.labels = labels

        secret = client.V1Secret(
            api_version="v1",
            kind="Secret",
            metadata=metadata,
            type=secret_type,
            data=encoded_data
        )

        result = core_v1.create_namespaced_secret(namespace=namespace, body=secret)

        return {
            "status": "Success",
            "message": f"Successfully created secret '{name}' in namespace '{namespace}'",
            "secret": {
                "name": result.metadata.name,
                "namespace": result.metadata.namespace,
                "type": result.type,
                "keys": list(result.data.keys()) if result.data else []
            }
        }
    except ApiException as e:
        if e.status == 409:
            raise RuntimeError(f"Secret '{name}' already exists in namespace '{namespace}'")
        raise RuntimeError(f"Failed to create secret '{name}': {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error creating secret '{name}': {str(e)}")


async def k8s_list_configmaps(context: str, namespace: Optional[str] = None,
                               label_selector: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List Kubernetes ConfigMaps.

    Args:
        context: The Kubernetes context to use
        namespace: Namespace to list ConfigMaps from (all namespaces if not specified)
        label_selector: Label selector to filter ConfigMaps

    Returns:
        List of ConfigMap information
    """
    try:
        api_client = k8s_client.get_api_client(context)
        core_v1 = client.CoreV1Api(api_client)

        kwargs = {}
        if label_selector:
            kwargs["label_selector"] = label_selector

        if namespace:
            configmaps = core_v1.list_namespaced_config_map(namespace=namespace, **kwargs)
        else:
            configmaps = core_v1.list_config_map_for_all_namespaces(**kwargs)

        return [
            {
                "name": cm.metadata.name,
                "namespace": cm.metadata.namespace,
                "keys": list(cm.data.keys()) if cm.data else [],
                "labels": cm.metadata.labels or {},
                "created": cm.metadata.creation_timestamp.isoformat() if cm.metadata.creation_timestamp else None
            }
            for cm in configmaps.items
        ]
    except Exception as e:
        raise RuntimeError(f"Failed to list ConfigMaps: {str(e)}")


async def k8s_get_configmap(context: str, name: str, namespace: str) -> Dict[str, Any]:
    """
    Get a Kubernetes ConfigMap with its data.

    Args:
        context: The Kubernetes context to use
        name: Name of the ConfigMap
        namespace: Namespace of the ConfigMap

    Returns:
        Dict with ConfigMap information including data
    """
    try:
        api_client = k8s_client.get_api_client(context)
        core_v1 = client.CoreV1Api(api_client)

        cm = core_v1.read_namespaced_config_map(name=name, namespace=namespace)

        return {
            "name": cm.metadata.name,
            "namespace": cm.metadata.namespace,
            "labels": cm.metadata.labels or {},
            "annotations": cm.metadata.annotations or {},
            "data": cm.data or {},
            "binary_data_keys": list(cm.binary_data.keys()) if cm.binary_data else [],
            "created": cm.metadata.creation_timestamp.isoformat() if cm.metadata.creation_timestamp else None
        }
    except ApiException as e:
        if e.status == 404:
            raise RuntimeError(f"ConfigMap '{name}' not found in namespace '{namespace}'")
        raise RuntimeError(f"Failed to get ConfigMap '{name}': {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error getting ConfigMap '{name}': {str(e)}")


async def k8s_create_configmap(context: str, name: str, namespace: str,
                                data: Dict[str, str],
                                labels: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Create a Kubernetes ConfigMap.

    Args:
        context: The Kubernetes context to use
        name: Name of the ConfigMap to create
        namespace: Namespace to create the ConfigMap in
        data: Key-value pairs for the ConfigMap
        labels: Optional labels to apply

    Returns:
        Dict with information about the created ConfigMap
    """
    try:
        api_client = k8s_client.get_api_client(context)
        core_v1 = client.CoreV1Api(api_client)

        metadata = client.V1ObjectMeta(name=name, namespace=namespace)
        if labels:
            metadata.labels = labels

        configmap = client.V1ConfigMap(
            api_version="v1",
            kind="ConfigMap",
            metadata=metadata,
            data=data
        )

        result = core_v1.create_namespaced_config_map(namespace=namespace, body=configmap)

        return {
            "status": "Success",
            "message": f"Successfully created ConfigMap '{name}' in namespace '{namespace}'",
            "configmap": {
                "name": result.metadata.name,
                "namespace": result.metadata.namespace,
                "keys": list(result.data.keys()) if result.data else []
            }
        }
    except ApiException as e:
        if e.status == 409:
            raise RuntimeError(f"ConfigMap '{name}' already exists in namespace '{namespace}'")
        raise RuntimeError(f"Failed to create ConfigMap '{name}': {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error creating ConfigMap '{name}': {str(e)}")
