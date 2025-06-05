from typing import Dict, Any, Optional
import os
from kubernetes import client
from ..utils.k8s_client import KubernetesClient

# Initialize client with kubeconfig directory from environment or default
kubeconfig_dir = os.environ.get("KUBECONFIG_DIR", os.path.expanduser("~/.kube"))
k8s_client = KubernetesClient(kubeconfig_dir)


async def get_k8s_resource(
    context: str, namespace: str, kind: str, name: str, group: Optional[str] = None, version: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get Kubernetes resource completely.

    Args:
        context (str): Name of the Kubernetes context to use
        namespace (str): Namespace to get resource from
        kind (str): Kind of resource to get
        name (str): Name of the resource to get
        group (str, optional): API Group of the resource to get
        version (str, optional): API Version of the resource to get

    Returns:
        Dict[str, Any]: The complete resource definition

    Raises:
        RuntimeError: If there's an error accessing the Kubernetes API
    """
    try:
        api_client = k8s_client.get_api_client(context)

        # Set default group for common resource types if not provided
        if not group:
            if kind.lower() in [
                "deployment",
                "deployments",
                "statefulset",
                "statefulsets",
                "daemonset",
                "daemonsets",
                "replicaset",
                "replicasets",
            ]:
                group = "apps"
            elif kind.lower() in ["ingress", "ingresses"]:
                group = "networking.k8s.io"
            elif kind.lower() in ["job", "jobs", "cronjob", "cronjobs"]:
                group = "batch"

        # Determine which API to use based on the resource kind, group and version
        if not group and kind.lower() in [
            "pod",
            "pods",
            "service",
            "services",
            "secret",
            "secrets",
            "configmap",
            "configmaps",
            "namespace",
            "namespaces",
        ]:
            # Core API resources
            api = client.CoreV1Api(api_client)

            try:
                if kind.lower() in ["pod", "pods"]:
                    return api.read_namespaced_pod(name=name, namespace=namespace).to_dict()
                elif kind.lower() in ["service", "services"]:
                    return api.read_namespaced_service(name=name, namespace=namespace).to_dict()
                elif kind.lower() in ["secret", "secrets"]:
                    return api.read_namespaced_secret(name=name, namespace=namespace).to_dict()
                elif kind.lower() in ["configmap", "configmaps"]:
                    return api.read_namespaced_config_map(name=name, namespace=namespace).to_dict()
                elif kind.lower() in ["namespace", "namespaces"]:
                    return api.read_namespace(name=name).to_dict()
            except client.rest.ApiException as e:
                if e.status == 404:
                    raise RuntimeError(f"{kind} '{name}' not found in namespace '{namespace}'")
                raise

        elif group == "apps" and kind.lower() in [
            "deployment",
            "deployments",
            "statefulset",
            "statefulsets",
            "daemonset",
            "daemonsets",
            "replicaset",
            "replicasets",
        ]:
            # Apps API resources
            api = client.AppsV1Api(api_client)

            try:
                if kind.lower() in ["deployment", "deployments"]:
                    return api.read_namespaced_deployment(name=name, namespace=namespace).to_dict()
                elif kind.lower() in ["statefulset", "statefulsets"]:
                    return api.read_namespaced_stateful_set(name=name, namespace=namespace).to_dict()
                elif kind.lower() in ["daemonset", "daemonsets"]:
                    return api.read_namespaced_daemon_set(name=name, namespace=namespace).to_dict()
                elif kind.lower() in ["replicaset", "replicasets"]:
                    return api.read_namespaced_replica_set(name=name, namespace=namespace).to_dict()
            except client.rest.ApiException as e:
                if e.status == 404:
                    raise RuntimeError(f"{kind} '{name}' not found in namespace '{namespace}'")
                raise

        elif group == "networking.k8s.io" and kind.lower() in ["ingress", "ingresses"]:
            # Networking API resources
            api = client.NetworkingV1Api(api_client)

            try:
                return api.read_namespaced_ingress(name=name, namespace=namespace).to_dict()
            except client.rest.ApiException as e:
                if e.status == 404:
                    raise RuntimeError(f"{kind} '{name}' not found in namespace '{namespace}'")
                raise

        elif group == "batch" and kind.lower() in ["job", "jobs", "cronjob", "cronjobs"]:
            # Batch API resources
            api = client.BatchV1Api(api_client)

            try:
                if kind.lower() in ["job", "jobs"]:
                    return api.read_namespaced_job(name=name, namespace=namespace).to_dict()
                elif kind.lower() in ["cronjob", "cronjobs"]:
                    return api.read_namespaced_cron_job(name=name, namespace=namespace).to_dict()
            except client.rest.ApiException as e:
                if e.status == 404:
                    raise RuntimeError(f"{kind} '{name}' not found in namespace '{namespace}'")
                raise

        else:
            # Generic API for other resource types
            api = client.CustomObjectsApi(api_client)
            version = version or "v1"
            group = group or ""

            try:
                return api.get_namespaced_custom_object(
                    group=group, version=version, namespace=namespace, plural=kind.lower() + "s", name=name
                )
            except client.rest.ApiException as e:
                if e.status == 404:
                    raise RuntimeError(f"{kind} '{name}' not found in namespace '{namespace}'")
                raise

    except ValueError as e:
        raise RuntimeError(str(e))
    except Exception as e:
        raise RuntimeError(f"Failed to get {kind} '{name}' in context '{context}', namespace '{namespace}': {str(e)}")
