from typing import Dict, List, Any, Optional
import os
from kubernetes import client
from kubernetes.client.rest import ApiException

from ..utils.k8s_client import KubernetesClient

# Initialize client with kubeconfig directory from environment or default
kubeconfig_dir = os.environ.get('KUBECONFIG_DIR', os.path.expanduser('~/.kube'))
k8s_client = KubernetesClient(kubeconfig_dir)


async def k8s_list_roles(context: str, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List RBAC Roles in the cluster.

    Args:
        context: The Kubernetes context to use
        namespace: Namespace to list roles from (all namespaces if not specified)

    Returns:
        List of Role information
    """
    try:
        api_client = k8s_client.get_api_client(context)
        rbac_v1 = client.RbacAuthorizationV1Api(api_client)

        if namespace:
            roles = rbac_v1.list_namespaced_role(namespace=namespace)
        else:
            roles = rbac_v1.list_role_for_all_namespaces()

        return [
            {
                "name": role.metadata.name,
                "namespace": role.metadata.namespace,
                "rules": [
                    {
                        "api_groups": rule.api_groups or [],
                        "resources": rule.resources or [],
                        "verbs": rule.verbs or [],
                        "resource_names": rule.resource_names or []
                    }
                    for rule in (role.rules or [])
                ],
                "created": role.metadata.creation_timestamp.isoformat() if role.metadata.creation_timestamp else None
            }
            for role in roles.items
        ]
    except Exception as e:
        raise RuntimeError(f"Failed to list roles: {str(e)}")


async def k8s_list_clusterroles(context: str) -> List[Dict[str, Any]]:
    """
    List RBAC ClusterRoles in the cluster.

    Args:
        context: The Kubernetes context to use

    Returns:
        List of ClusterRole information
    """
    try:
        api_client = k8s_client.get_api_client(context)
        rbac_v1 = client.RbacAuthorizationV1Api(api_client)

        roles = rbac_v1.list_cluster_role()

        return [
            {
                "name": role.metadata.name,
                "labels": role.metadata.labels or {},
                "rules_count": len(role.rules) if role.rules else 0,
                "rules": [
                    {
                        "api_groups": rule.api_groups or [],
                        "resources": rule.resources or [],
                        "verbs": rule.verbs or [],
                    }
                    for rule in (role.rules or [])[:10]  # Limit to first 10 rules for readability
                ],
                "aggregation_rule": bool(role.aggregation_rule),
                "created": role.metadata.creation_timestamp.isoformat() if role.metadata.creation_timestamp else None
            }
            for role in roles.items
        ]
    except Exception as e:
        raise RuntimeError(f"Failed to list cluster roles: {str(e)}")


async def k8s_list_rolebindings(context: str, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List RBAC RoleBindings in the cluster.

    Args:
        context: The Kubernetes context to use
        namespace: Namespace to list role bindings from (all namespaces if not specified)

    Returns:
        List of RoleBinding information
    """
    try:
        api_client = k8s_client.get_api_client(context)
        rbac_v1 = client.RbacAuthorizationV1Api(api_client)

        if namespace:
            bindings = rbac_v1.list_namespaced_role_binding(namespace=namespace)
        else:
            bindings = rbac_v1.list_role_binding_for_all_namespaces()

        return [
            {
                "name": binding.metadata.name,
                "namespace": binding.metadata.namespace,
                "role": {
                    "kind": binding.role_ref.kind,
                    "name": binding.role_ref.name,
                    "api_group": binding.role_ref.api_group
                },
                "subjects": [
                    {
                        "kind": subject.kind,
                        "name": subject.name,
                        "namespace": subject.namespace,
                        "api_group": subject.api_group
                    }
                    for subject in (binding.subjects or [])
                ],
                "created": binding.metadata.creation_timestamp.isoformat() if binding.metadata.creation_timestamp else None
            }
            for binding in bindings.items
        ]
    except Exception as e:
        raise RuntimeError(f"Failed to list role bindings: {str(e)}")


async def k8s_list_clusterrolebindings(context: str) -> List[Dict[str, Any]]:
    """
    List RBAC ClusterRoleBindings in the cluster.

    Args:
        context: The Kubernetes context to use

    Returns:
        List of ClusterRoleBinding information
    """
    try:
        api_client = k8s_client.get_api_client(context)
        rbac_v1 = client.RbacAuthorizationV1Api(api_client)

        bindings = rbac_v1.list_cluster_role_binding()

        return [
            {
                "name": binding.metadata.name,
                "role": {
                    "kind": binding.role_ref.kind,
                    "name": binding.role_ref.name,
                    "api_group": binding.role_ref.api_group
                },
                "subjects": [
                    {
                        "kind": subject.kind,
                        "name": subject.name,
                        "namespace": subject.namespace,
                    }
                    for subject in (binding.subjects or [])
                ],
                "created": binding.metadata.creation_timestamp.isoformat() if binding.metadata.creation_timestamp else None
            }
            for binding in bindings.items
        ]
    except Exception as e:
        raise RuntimeError(f"Failed to list cluster role bindings: {str(e)}")


async def k8s_list_service_accounts(context: str, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List Kubernetes ServiceAccounts.

    Args:
        context: The Kubernetes context to use
        namespace: Namespace to list service accounts from (all namespaces if not specified)

    Returns:
        List of ServiceAccount information
    """
    try:
        api_client = k8s_client.get_api_client(context)
        core_v1 = client.CoreV1Api(api_client)

        if namespace:
            sa_list = core_v1.list_namespaced_service_account(namespace=namespace)
        else:
            sa_list = core_v1.list_service_account_for_all_namespaces()

        return [
            {
                "name": sa.metadata.name,
                "namespace": sa.metadata.namespace,
                "secrets": [s.name for s in (sa.secrets or [])],
                "labels": sa.metadata.labels or {},
                "created": sa.metadata.creation_timestamp.isoformat() if sa.metadata.creation_timestamp else None
            }
            for sa in sa_list.items
        ]
    except Exception as e:
        raise RuntimeError(f"Failed to list service accounts: {str(e)}")
