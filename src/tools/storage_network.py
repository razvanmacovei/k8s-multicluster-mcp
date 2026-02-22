from typing import Dict, List, Any, Optional
import os
from kubernetes import client
from kubernetes.client.rest import ApiException

from ..utils.k8s_client import KubernetesClient

# Initialize client with kubeconfig directory from environment or default
kubeconfig_dir = os.environ.get('KUBECONFIG_DIR', os.path.expanduser('~/.kube'))
k8s_client = KubernetesClient(kubeconfig_dir)


async def k8s_list_pvcs(context: str, namespace: Optional[str] = None,
                        label_selector: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List PersistentVolumeClaims in the cluster.

    Args:
        context: The Kubernetes context to use
        namespace: Namespace to list PVCs from (all namespaces if not specified)
        label_selector: Label selector to filter PVCs

    Returns:
        List of PVC information
    """
    try:
        api_client = k8s_client.get_api_client(context)
        core_v1 = client.CoreV1Api(api_client)

        kwargs = {}
        if label_selector:
            kwargs["label_selector"] = label_selector

        if namespace:
            pvcs = core_v1.list_namespaced_persistent_volume_claim(namespace=namespace, **kwargs)
        else:
            pvcs = core_v1.list_persistent_volume_claim_for_all_namespaces(**kwargs)

        return [
            {
                "name": pvc.metadata.name,
                "namespace": pvc.metadata.namespace,
                "status": pvc.status.phase,
                "volume": pvc.spec.volume_name,
                "capacity": pvc.status.capacity.get("storage") if pvc.status.capacity else None,
                "access_modes": pvc.spec.access_modes,
                "storage_class": pvc.spec.storage_class_name,
                "created": pvc.metadata.creation_timestamp.isoformat() if pvc.metadata.creation_timestamp else None
            }
            for pvc in pvcs.items
        ]
    except Exception as e:
        raise RuntimeError(f"Failed to list PVCs: {str(e)}")


async def k8s_list_pvs(context: str) -> List[Dict[str, Any]]:
    """
    List PersistentVolumes in the cluster.

    Args:
        context: The Kubernetes context to use

    Returns:
        List of PV information
    """
    try:
        api_client = k8s_client.get_api_client(context)
        core_v1 = client.CoreV1Api(api_client)

        pvs = core_v1.list_persistent_volume()

        return [
            {
                "name": pv.metadata.name,
                "status": pv.status.phase,
                "capacity": pv.spec.capacity.get("storage") if pv.spec.capacity else None,
                "access_modes": pv.spec.access_modes,
                "reclaim_policy": pv.spec.persistent_volume_reclaim_policy,
                "storage_class": pv.spec.storage_class_name,
                "claim": f"{pv.spec.claim_ref.namespace}/{pv.spec.claim_ref.name}" if pv.spec.claim_ref else None,
                "created": pv.metadata.creation_timestamp.isoformat() if pv.metadata.creation_timestamp else None
            }
            for pv in pvs.items
        ]
    except Exception as e:
        raise RuntimeError(f"Failed to list PVs: {str(e)}")


async def k8s_list_storage_classes(context: str) -> List[Dict[str, Any]]:
    """
    List StorageClasses in the cluster.

    Args:
        context: The Kubernetes context to use

    Returns:
        List of StorageClass information
    """
    try:
        api_client = k8s_client.get_api_client(context)
        storage_v1 = client.StorageV1Api(api_client)

        scs = storage_v1.list_storage_class()

        return [
            {
                "name": sc.metadata.name,
                "provisioner": sc.provisioner,
                "reclaim_policy": sc.reclaim_policy,
                "volume_binding_mode": sc.volume_binding_mode,
                "allow_volume_expansion": sc.allow_volume_expansion,
                "is_default": any(
                    sc.metadata.annotations.get(ann) == "true"
                    for ann in [
                        "storageclass.kubernetes.io/is-default-class",
                        "storageclass.beta.kubernetes.io/is-default-class"
                    ]
                ) if sc.metadata.annotations else False,
                "parameters": sc.parameters or {},
                "created": sc.metadata.creation_timestamp.isoformat() if sc.metadata.creation_timestamp else None
            }
            for sc in scs.items
        ]
    except Exception as e:
        raise RuntimeError(f"Failed to list storage classes: {str(e)}")


async def k8s_list_network_policies(context: str, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List NetworkPolicies in the cluster.

    Args:
        context: The Kubernetes context to use
        namespace: Namespace to list network policies from (all namespaces if not specified)

    Returns:
        List of NetworkPolicy information
    """
    try:
        api_client = k8s_client.get_api_client(context)
        networking_v1 = client.NetworkingV1Api(api_client)

        if namespace:
            policies = networking_v1.list_namespaced_network_policy(namespace=namespace)
        else:
            policies = networking_v1.list_network_policy_for_all_namespaces()

        return [
            {
                "name": policy.metadata.name,
                "namespace": policy.metadata.namespace,
                "pod_selector": policy.spec.pod_selector.match_labels if policy.spec.pod_selector and policy.spec.pod_selector.match_labels else {},
                "policy_types": policy.spec.policy_types or [],
                "ingress_rules_count": len(policy.spec.ingress) if policy.spec.ingress else 0,
                "egress_rules_count": len(policy.spec.egress) if policy.spec.egress else 0,
                "labels": policy.metadata.labels or {},
                "created": policy.metadata.creation_timestamp.isoformat() if policy.metadata.creation_timestamp else None
            }
            for policy in policies.items
        ]
    except Exception as e:
        raise RuntimeError(f"Failed to list network policies: {str(e)}")
