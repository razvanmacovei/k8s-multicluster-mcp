"""Kubernetes resource kind to plural name mapping.

Handles proper pluralization of Kubernetes resource kinds,
including irregular plurals that simple 's' suffix won't handle.
"""

# Mapping of lowercase singular kind to plural form
# Covers all built-in Kubernetes resource types
PLURAL_MAP = {
    # Core API (v1)
    "pod": "pods",
    "service": "services",
    "namespace": "namespaces",
    "node": "nodes",
    "configmap": "configmaps",
    "secret": "secrets",
    "serviceaccount": "serviceaccounts",
    "persistentvolume": "persistentvolumes",
    "persistentvolumeclaim": "persistentvolumeclaims",
    "event": "events",
    "endpoint": "endpoints",
    "endpoints": "endpoints",
    "resourcequota": "resourcequotas",
    "limitrange": "limitranges",
    "replicationcontroller": "replicationcontrollers",
    "componentstatus": "componentstatuses",
    # Apps API (apps/v1)
    "deployment": "deployments",
    "statefulset": "statefulsets",
    "daemonset": "daemonsets",
    "replicaset": "replicasets",
    "controllerrevision": "controllerrevisions",
    # Batch API (batch/v1)
    "job": "jobs",
    "cronjob": "cronjobs",
    # Networking API (networking.k8s.io/v1)
    "ingress": "ingresses",
    "ingressclass": "ingressclasses",
    "networkpolicy": "networkpolicies",
    # RBAC API (rbac.authorization.k8s.io/v1)
    "role": "roles",
    "clusterrole": "clusterroles",
    "rolebinding": "rolebindings",
    "clusterrolebinding": "clusterrolebindings",
    # Storage API (storage.k8s.io/v1)
    "storageclass": "storageclasses",
    "volumeattachment": "volumeattachments",
    "csidriver": "csidrivers",
    "csinode": "csinodes",
    # Autoscaling API
    "horizontalpodautoscaler": "horizontalpodautoscalers",
    # Policy API
    "poddisruptionbudget": "poddisruptionbudgets",
    "podsecuritypolicy": "podsecuritypolicies",
    # Certificates API
    "certificatesigningrequest": "certificatesigningrequests",
    # API Extensions
    "customresourcedefinition": "customresourcedefinitions",
    # Admission
    "mutatingwebhookconfiguration": "mutatingwebhookconfigurations",
    "validatingwebhookconfiguration": "validatingwebhookconfigurations",
}


def pluralize_kind(kind: str) -> str:
    """Convert a Kubernetes resource kind to its plural form.

    Uses a known mapping for built-in types and falls back to
    common English pluralization rules for unknown types.

    Args:
        kind: The resource kind (e.g., 'Deployment', 'Ingress', 'Pod')

    Returns:
        The plural form of the kind in lowercase (e.g., 'deployments', 'ingresses', 'pods')
    """
    lower = kind.lower()

    # Strip trailing 's' if someone passes a plural already
    if lower in PLURAL_MAP.values():
        return lower

    # Check direct mapping
    if lower in PLURAL_MAP:
        return PLURAL_MAP[lower]

    # Fallback: common English pluralization rules
    if lower.endswith("s") or lower.endswith("x") or lower.endswith("z"):
        return lower + "es"
    elif lower.endswith("ch") or lower.endswith("sh"):
        return lower + "es"
    elif lower.endswith("y") and lower[-2] not in "aeiou":
        return lower[:-1] + "ies"
    else:
        return lower + "s"
