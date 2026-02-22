from typing import Dict, Any, Optional
import os
from kubernetes import client
from kubernetes.client.rest import ApiException

from ..utils.k8s_client import KubernetesClient
from ..utils.pluralize import pluralize_kind

# Initialize client with kubeconfig directory from environment or default
kubeconfig_dir = os.environ.get('KUBECONFIG_DIR', os.path.expanduser('~/.kube'))
k8s_client = KubernetesClient(kubeconfig_dir)


async def k8s_delete(context: str, resource_type: str, name: str,
                     namespace: Optional[str] = None,
                     grace_period: Optional[int] = None,
                     force: bool = False) -> Dict[str, Any]:
    """
    Delete a Kubernetes resource.

    Args:
        context: The Kubernetes context to use
        resource_type: The type of resource to delete (e.g., pod, deployment, service)
        name: The name of the resource to delete
        namespace: The namespace of the resource (not required for cluster-scoped resources)
        grace_period: Period in seconds to wait before force deletion (0 = immediate)
        force: If True, immediately delete the resource (sets grace period to 0)

    Returns:
        Dict with status information about the deletion

    Raises:
        RuntimeError: If there's an error deleting the resource
    """
    try:
        api_client = k8s_client.get_api_client(context)
        resource_type_lower = resource_type.lower()

        # Build delete options
        delete_options = client.V1DeleteOptions()
        if force:
            delete_options.grace_period_seconds = 0
        elif grace_period is not None:
            delete_options.grace_period_seconds = grace_period

        # Handle well-known resource types with typed APIs
        if resource_type_lower in ['pod', 'pods']:
            api = client.CoreV1Api(api_client)
            api.delete_namespaced_pod(name=name, namespace=namespace or 'default', body=delete_options)
            kind = "Pod"

        elif resource_type_lower in ['deployment', 'deployments']:
            api = client.AppsV1Api(api_client)
            api.delete_namespaced_deployment(name=name, namespace=namespace or 'default', body=delete_options)
            kind = "Deployment"

        elif resource_type_lower in ['service', 'services', 'svc']:
            api = client.CoreV1Api(api_client)
            api.delete_namespaced_service(name=name, namespace=namespace or 'default', body=delete_options)
            kind = "Service"

        elif resource_type_lower in ['configmap', 'configmaps', 'cm']:
            api = client.CoreV1Api(api_client)
            api.delete_namespaced_config_map(name=name, namespace=namespace or 'default', body=delete_options)
            kind = "ConfigMap"

        elif resource_type_lower in ['secret', 'secrets']:
            api = client.CoreV1Api(api_client)
            api.delete_namespaced_secret(name=name, namespace=namespace or 'default', body=delete_options)
            kind = "Secret"

        elif resource_type_lower in ['statefulset', 'statefulsets']:
            api = client.AppsV1Api(api_client)
            api.delete_namespaced_stateful_set(name=name, namespace=namespace or 'default', body=delete_options)
            kind = "StatefulSet"

        elif resource_type_lower in ['daemonset', 'daemonsets']:
            api = client.AppsV1Api(api_client)
            api.delete_namespaced_daemon_set(name=name, namespace=namespace or 'default', body=delete_options)
            kind = "DaemonSet"

        elif resource_type_lower in ['replicaset', 'replicasets']:
            api = client.AppsV1Api(api_client)
            api.delete_namespaced_replica_set(name=name, namespace=namespace or 'default', body=delete_options)
            kind = "ReplicaSet"

        elif resource_type_lower in ['job', 'jobs']:
            api = client.BatchV1Api(api_client)
            api.delete_namespaced_job(name=name, namespace=namespace or 'default', body=delete_options,
                                     propagation_policy='Background')
            kind = "Job"

        elif resource_type_lower in ['cronjob', 'cronjobs']:
            api = client.BatchV1Api(api_client)
            api.delete_namespaced_cron_job(name=name, namespace=namespace or 'default', body=delete_options)
            kind = "CronJob"

        elif resource_type_lower in ['ingress', 'ingresses']:
            api = client.NetworkingV1Api(api_client)
            api.delete_namespaced_ingress(name=name, namespace=namespace or 'default', body=delete_options)
            kind = "Ingress"

        elif resource_type_lower in ['pvc', 'persistentvolumeclaim', 'persistentvolumeclaims']:
            api = client.CoreV1Api(api_client)
            api.delete_namespaced_persistent_volume_claim(name=name, namespace=namespace or 'default',
                                                          body=delete_options)
            kind = "PersistentVolumeClaim"

        elif resource_type_lower in ['pv', 'persistentvolume', 'persistentvolumes']:
            api = client.CoreV1Api(api_client)
            api.delete_persistent_volume(name=name, body=delete_options)
            kind = "PersistentVolume"

        elif resource_type_lower in ['namespace', 'namespaces', 'ns']:
            api = client.CoreV1Api(api_client)
            api.delete_namespace(name=name, body=delete_options)
            kind = "Namespace"

        elif resource_type_lower in ['serviceaccount', 'serviceaccounts', 'sa']:
            api = client.CoreV1Api(api_client)
            api.delete_namespaced_service_account(name=name, namespace=namespace or 'default',
                                                   body=delete_options)
            kind = "ServiceAccount"

        elif resource_type_lower in ['networkpolicy', 'networkpolicies', 'netpol']:
            api = client.NetworkingV1Api(api_client)
            api.delete_namespaced_network_policy(name=name, namespace=namespace or 'default',
                                                  body=delete_options)
            kind = "NetworkPolicy"

        elif resource_type_lower in ['hpa', 'horizontalpodautoscaler', 'horizontalpodautoscalers']:
            api = client.AutoscalingV1Api(api_client)
            api.delete_namespaced_horizontal_pod_autoscaler(name=name, namespace=namespace or 'default',
                                                             body=delete_options)
            kind = "HorizontalPodAutoscaler"

        else:
            # Generic approach via CustomObjectsApi
            api = client.CustomObjectsApi(api_client)
            plural = pluralize_kind(resource_type)
            if namespace:
                api.delete_namespaced_custom_object(
                    group="", version="v1", namespace=namespace,
                    plural=plural, name=name, body=delete_options
                )
            else:
                api.delete_cluster_custom_object(
                    group="", version="v1",
                    plural=plural, name=name, body=delete_options
                )
            kind = resource_type.capitalize()

        return {
            "status": "Success",
            "message": f"Successfully deleted {kind} '{name}'"
            + (f" in namespace '{namespace}'" if namespace else "")
        }

    except ApiException as e:
        if e.status == 404:
            raise RuntimeError(
                f"{resource_type.capitalize()} '{name}' not found"
                + (f" in namespace '{namespace}'" if namespace else "")
            )
        raise RuntimeError(f"Failed to delete {resource_type} '{name}': {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error deleting {resource_type} '{name}': {str(e)}")
