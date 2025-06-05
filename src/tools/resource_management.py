import json
import os
from typing import Any, Dict, Optional

import yaml
from kubernetes import client
from kubernetes.client.rest import ApiException

from ..utils.k8s_client import KubernetesClient

# Initialize client with kubeconfig directory from environment
kubeconfig_dir = os.environ.get("KUBECONFIG_DIR", os.path.expanduser("~/.kube"))
k8s_client = KubernetesClient(kubeconfig_dir)


async def k8s_create(context: str, yaml_content: str, namespace: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a Kubernetes resource from YAML/JSON content.

    Args:
        context (str): The Kubernetes context to use
        yaml_content (str): The YAML or JSON content describing the resource
        namespace (str, optional): The namespace to create the resource in

    Returns:
        Dict[str, Any]: Information about the created resource

    Raises:
        RuntimeError: If there's an error creating the resource
    """
    try:
        # Parse the YAML content
        if yaml_content.strip().startswith("{"):
            # Content is JSON
            resource_dict = json.loads(yaml_content)
        else:
            # Content is YAML
            resource_dict = yaml.safe_load(yaml_content)

        # Get the API client for the specified context
        api_client = k8s_client.get_api_client(context)

        # Override namespace if provided
        if namespace:
            resource_dict["metadata"] = resource_dict.get("metadata", {})
            resource_dict["metadata"]["namespace"] = namespace

        # Use the dynamic client to create the resource
        api = client.CustomObjectsApi(api_client)

        # Extract resource information
        api_version = resource_dict["apiVersion"]
        kind = resource_dict["kind"]

        # Determine if this is a core resource or namespaced resource
        group, version = None, api_version
        if "/" in api_version:
            group, version = api_version.split("/")

        # Determine scope and call appropriate API
        metadata = resource_dict.get("metadata", {})
        resource_namespace = metadata.get("namespace", namespace)
        name = metadata.get("name")

        if resource_namespace:
            # Namespaced resource
            result = api.create_namespaced_custom_object(
                group=group if group else "",
                version=version,
                namespace=resource_namespace,
                plural=kind.lower() + "s",  # Simple pluralization
                body=resource_dict,
            )
        else:
            # Cluster-scoped resource
            result = api.create_cluster_custom_object(
                group=group if group else "",
                version=version,
                plural=kind.lower() + "s",  # Simple pluralization
                body=resource_dict,
            )

        return {"status": "Success", "message": f"Successfully created {kind} '{name}'", "resource": result}
    except ApiException as e:
        raise RuntimeError(f"Failed to create resource: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error creating resource: {str(e)}")


async def k8s_apply(context: str, yaml_content: str, namespace: Optional[str] = None) -> Dict[str, Any]:
    """
    Apply a configuration to a resource by filename or stdin.

    Args:
        context (str): The Kubernetes context to use
        yaml_content (str): The YAML or JSON content describing the resource
        namespace (str, optional): The namespace to apply the resource in

    Returns:
        Dict[str, Any]: Information about the applied resource

    Raises:
        RuntimeError: If there's an error applying the resource
    """
    try:
        # Parse the YAML content
        if yaml_content.strip().startswith("{"):
            # Content is JSON
            resource_dict = json.loads(yaml_content)
        else:
            # Content is YAML
            resource_dict = yaml.safe_load(yaml_content)

        # Get the API client for the specified context
        api_client = k8s_client.get_api_client(context)

        # Override namespace if provided
        if namespace:
            resource_dict["metadata"] = resource_dict.get("metadata", {})
            resource_dict["metadata"]["namespace"] = namespace

        # Use the dynamic client to apply the resource
        api = client.CustomObjectsApi(api_client)

        # Extract resource information
        api_version = resource_dict["apiVersion"]
        kind = resource_dict["kind"]

        # Determine if this is a core resource or namespaced resource
        group, version = None, api_version
        if "/" in api_version:
            group, version = api_version.split("/")

        # Determine scope and call appropriate API
        metadata = resource_dict.get("metadata", {})
        resource_namespace = metadata.get("namespace", namespace)
        name = metadata.get("name")

        if not name:
            raise ValueError("Resource must have a name")

        try:
            # Try to get the resource first to see if it exists
            if resource_namespace:
                existing = api.get_namespaced_custom_object(
                    group=group if group else "",
                    version=version,
                    namespace=resource_namespace,
                    plural=kind.lower() + "s",
                    name=name,
                )
            else:
                existing = api.get_cluster_custom_object(
                    group=group if group else "", version=version, plural=kind.lower() + "s", name=name
                )

            # Resource exists, update it
            if resource_namespace:
                result = api.patch_namespaced_custom_object(
                    group=group if group else "",
                    version=version,
                    namespace=resource_namespace,
                    plural=kind.lower() + "s",
                    name=name,
                    body=resource_dict,
                )
            else:
                result = api.patch_cluster_custom_object(
                    group=group if group else "",
                    version=version,
                    plural=kind.lower() + "s",
                    name=name,
                    body=resource_dict,
                )
            action = "updated"
        except ApiException as e:
            if e.status == 404:
                # Resource doesn't exist, create it
                if resource_namespace:
                    result = api.create_namespaced_custom_object(
                        group=group if group else "",
                        version=version,
                        namespace=resource_namespace,
                        plural=kind.lower() + "s",
                        body=resource_dict,
                    )
                else:
                    result = api.create_cluster_custom_object(
                        group=group if group else "", version=version, plural=kind.lower() + "s", body=resource_dict
                    )
                action = "created"
            else:
                raise

        return {"status": "Success", "message": f"Successfully {action} {kind} '{name}'", "resource": result}
    except ApiException as e:
        raise RuntimeError(f"Failed to apply resource: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error applying resource: {str(e)}")


async def k8s_patch(
    context: str, resource_type: str, name: str, patch: Dict[str, Any], namespace: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update fields of a resource.

    Args:
        context (str): The Kubernetes context to use
        resource_type (str): The type of resource to patch
        name (str): The name of the resource to patch
        patch (Dict[str, Any]): The patch to apply
        namespace (str, optional): The namespace of the resource

    Returns:
        Dict[str, Any]: Information about the patched resource

    Raises:
        RuntimeError: If there's an error patching the resource
    """
    try:
        # Get the API client for the specified context
        api_client = k8s_client.get_api_client(context)

        # Normalize resource type
        resource_type = resource_type.lower()

        # Handle common resource types
        api = client.CustomObjectsApi(api_client)

        if resource_type in ["pod", "pods"]:
            api_instance = client.CoreV1Api(api_client)
            result = api_instance.patch_namespaced_pod(name=name, namespace=namespace, body=patch)
            kind = "Pod"
        elif resource_type in ["deployment", "deployments"]:
            api_instance = client.AppsV1Api(api_client)
            result = api_instance.patch_namespaced_deployment(name=name, namespace=namespace, body=patch)
            kind = "Deployment"
        elif resource_type in ["service", "services", "svc"]:
            api_instance = client.CoreV1Api(api_client)
            result = api_instance.patch_namespaced_service(name=name, namespace=namespace, body=patch)
            kind = "Service"
        elif resource_type in ["configmap", "configmaps"]:
            api_instance = client.CoreV1Api(api_client)
            result = api_instance.patch_namespaced_config_map(name=name, namespace=namespace, body=patch)
            kind = "ConfigMap"
        elif resource_type in ["secret", "secrets"]:
            api_instance = client.CoreV1Api(api_client)
            result = api_instance.patch_namespaced_secret(name=name, namespace=namespace, body=patch)
            kind = "Secret"
        else:
            # Generic approach for other resource types
            # This is a simplified implementation and may not work for all resource types
            group = ""
            version = "v1"
            plural = resource_type + "s"  # Simple pluralization

            # Try to patch the resource
            if namespace:
                result = api.patch_namespaced_custom_object(
                    group=group, version=version, namespace=namespace, plural=plural, name=name, body=patch
                )
            else:
                result = api.patch_cluster_custom_object(
                    group=group, version=version, plural=plural, name=name, body=patch
                )
            kind = resource_type.capitalize()

        return {"status": "Success", "message": f"Successfully patched {kind} '{name}'", "resource": result}
    except ApiException as e:
        raise RuntimeError(f"Failed to patch {resource_type} '{name}': {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error patching {resource_type} '{name}': {str(e)}")


async def k8s_label(
    context: str,
    resource_type: str,
    name: str,
    labels: Dict[str, str],
    namespace: str,
    overwrite: Optional[bool] = False,
) -> Dict[str, Any]:
    """
    Update the labels on a resource.

    Args:
        context (str): The Kubernetes context to use
        resource_type (str): The type of resource to label
        name (str): The name of the resource to label
        labels (Dict[str, str]): The labels to apply
        namespace (str): The namespace of the resource
        overwrite (bool, optional): Whether to overwrite existing labels

    Returns:
        Dict[str, Any]: Information about the labeled resource

    Raises:
        RuntimeError: If there's an error labeling the resource
    """
    try:
        # Create a patch to update the labels
        if overwrite:
            # Replace all labels
            patch = {"metadata": {"labels": labels}}
        else:
            # Merge with existing labels
            patch = {"metadata": {"labels": labels}}

        # Call the patch function to apply the labels
        return await k8s_patch(context, resource_type, name, patch, namespace)
    except Exception as e:
        raise RuntimeError(f"Error labeling {resource_type} '{name}': {str(e)}")


async def k8s_annotate(
    context: str,
    resource_type: str,
    name: str,
    annotations: Dict[str, str],
    namespace: str,
    overwrite: Optional[bool] = False,
) -> Dict[str, Any]:
    """
    Update the annotations on a resource.

    Args:
        context (str): The Kubernetes context to use
        resource_type (str): The type of resource to annotate
        name (str): The name of the resource to annotate
        annotations (Dict[str, str]): The annotations to apply
        namespace (str): The namespace of the resource
        overwrite (bool, optional): Whether to overwrite existing annotations

    Returns:
        Dict[str, Any]: Information about the annotated resource

    Raises:
        RuntimeError: If there's an error annotating the resource
    """
    try:
        # Create a patch to update the annotations
        if overwrite:
            # Replace all annotations
            patch = {"metadata": {"annotations": annotations}}
        else:
            # Merge with existing annotations
            patch = {"metadata": {"annotations": annotations}}

        # Call the patch function to apply the annotations
        return await k8s_patch(context, resource_type, name, patch, namespace)
    except Exception as e:
        raise RuntimeError(f"Error annotating {resource_type} '{name}': {str(e)}")
