import os
from typing import Any, Dict, List

from kubernetes import client

from ..utils.k8s_client import KubernetesClient

# Initialize client with kubeconfig directory from environment or default
kubeconfig_dir = os.environ.get("KUBECONFIG_DIR", os.path.expanduser("~/.kube"))
k8s_client = KubernetesClient(kubeconfig_dir)


async def list_k8s_apis(context: str) -> Dict[str, Any]:
    """
    List all available APIs in the Kubernetes cluster.

    Args:
        context (str): Name of the Kubernetes context to use

    Returns:
        Dict[str, Any]: Information about available APIs, grouped by category

    Raises:
        RuntimeError: If there's an error accessing the Kubernetes API
    """
    try:
        api_client = k8s_client.get_api_client(context)

        # Initialize API discovery client
        api_discovery = client.ApisApi(api_client)
        api_core = client.CoreApi(api_client)

        # Get API groups
        api_groups = api_discovery.get_api_versions()
        core_versions = api_core.get_api_versions()

        # Format the result
        result = {"core": {"versions": core_versions.versions}, "groups": []}

        # Add API groups information
        for group in api_groups.groups:
            group_info = {
                "name": group.name,
                "preferred_version": group.preferred_version.group_version if group.preferred_version else None,
                "versions": [
                    {"group_version": version.group_version, "version": version.version} for version in group.versions
                ],
            }
            result["groups"].append(group_info)

        # Get API resources for each group
        for group in result["groups"]:
            if group["preferred_version"]:
                try:
                    # Split group/version
                    if "/" in group["preferred_version"]:
                        group_name, version = group["preferred_version"].split("/")

                        # Get resources for this group version
                        resources_list = api_discovery.get_api_resources(group_name, version)

                        # Add resources to the group
                        group["resources"] = [
                            {
                                "name": resource.name,
                                "namespaced": resource.namespaced,
                                "kind": resource.kind,
                                "verbs": resource.verbs,
                                "short_names": resource.short_names if hasattr(resource, "short_names") else [],
                            }
                            for resource in resources_list.resources
                        ]
                except Exception as e:
                    # Skip if we can't get resources for this group
                    group["resources_error"] = str(e)

        # Get core API resources
        try:
            core_resources = api_core.get_api_resources()
            result["core"]["resources"] = [
                {
                    "name": resource.name,
                    "namespaced": resource.namespaced,
                    "kind": resource.kind,
                    "verbs": resource.verbs,
                    "short_names": resource.short_names if hasattr(resource, "short_names") else [],
                }
                for resource in core_resources.resources
            ]
        except Exception as e:
            result["core"]["resources_error"] = str(e)

        return result

    except Exception as e:
        raise RuntimeError(f"Failed to list APIs: {str(e)}")


async def list_k8s_crds(context: str) -> List[Dict[str, Any]]:
    """
    List all Custom Resource Definitions (CRDs) in the Kubernetes cluster.

    Args:
        context (str): Name of the Kubernetes context to use

    Returns:
        List[Dict[str, Any]]: List of available CRDs with their details

    Raises:
        RuntimeError: If there's an error accessing the Kubernetes API
    """
    try:
        api_client = k8s_client.get_api_client(context)

        # Initialize ApiextensionsV1 API client
        api_extensions = client.ApiextensionsV1Api(api_client)

        # Get all CRDs
        crds = api_extensions.list_custom_resource_definition()

        # Format the result
        result = []
        for crd in crds.items:
            crd_info = {
                "name": crd.metadata.name,
                "group": crd.spec.group,
                "scope": crd.spec.scope,  # Cluster or Namespaced
                "names": {
                    "plural": crd.spec.names.plural,
                    "singular": crd.spec.names.singular,
                    "kind": crd.spec.names.kind,
                    "list_kind": crd.spec.names.list_kind if hasattr(crd.spec.names, "list_kind") else None,
                    "short_names": crd.spec.names.short_names if hasattr(crd.spec.names, "short_names") else [],
                },
                "versions": [
                    {"name": version.name, "served": version.served, "storage": version.storage}
                    for version in crd.spec.versions
                ],
                "created": crd.metadata.creation_timestamp.isoformat() if crd.metadata.creation_timestamp else None,
                "api_resource_path": f"{crd.spec.group}/{crd.spec.versions[0].name}/{crd.spec.names.plural}",
            }

            # Add status conditions if available
            if hasattr(crd, "status") and hasattr(crd.status, "conditions"):
                crd_info["conditions"] = [
                    {
                        "type": condition.type,
                        "status": condition.status,
                        "reason": condition.reason,
                        "message": condition.message,
                        "last_transition_time": (
                            condition.last_transition_time.isoformat() if condition.last_transition_time else None
                        ),
                    }
                    for condition in crd.status.conditions
                ]

            result.append(crd_info)

        return result

    except Exception as e:
        raise RuntimeError(f"Failed to list CRDs: {str(e)}")
