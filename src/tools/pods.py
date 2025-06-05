from typing import List, Dict, Any, Optional
import os
from kubernetes import client
from ..utils.k8s_client import KubernetesClient

# Initialize client with kubeconfig directory from environment or default
kubeconfig_dir = os.environ.get('KUBECONFIG_DIR', os.path.expanduser('~/.kube'))
k8s_client = KubernetesClient(kubeconfig_dir)

async def list_k8s_resources(context: str, kind: str, namespace: Optional[str] = None, 
                            group: Optional[str] = None, version: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List Kubernetes resources of a specified kind.
    
    Args:
        context (str): Name of the Kubernetes context to use
        kind (str): Kind of resources to list (e.g. Pod, Deployment, Service)
        namespace (str, optional): Namespace to list resources from. If None, query across all namespaces
        group (str, optional): API Group of resources to list (e.g. apps)
        version (str, optional): API Version of resources to list (e.g. v1)
        
    Returns:
        List[Dict[str, Any]]: A list of resources with name, namespace, status and other relevant info
        
    Raises:
        RuntimeError: If there's an error accessing the Kubernetes API
    """
    try:
        # Auto-assign API groups for common resources if not specified
        if not group:
            if kind.lower() in ['deployment', 'deployments', 'statefulset', 'statefulsets', 'daemonset', 'daemonsets']:
                group = "apps"
            elif kind.lower() in ['ingress', 'ingresses']:
                group = "networking.k8s.io"
            elif kind.lower() in ['job', 'jobs', 'cronjob', 'cronjobs']:
                group = "batch"
                
        api_client = k8s_client.get_api_client(context)
        
        # Determine which API to use based on the resource kind, group and version
        if not group and (kind.lower() in ['pod', 'pods', 'service', 'services', 'namespace', 'namespaces']):
            # Core API resources
            api = client.CoreV1Api(api_client)
            
            if kind.lower() in ['pod', 'pods']:
                if namespace:
                    response = api.list_namespaced_pod(namespace=namespace)
                else:
                    response = api.list_pod_for_all_namespaces()
                    
                return [
                    {
                        "name": pod.metadata.name,
                        "namespace": pod.metadata.namespace,
                        "status": pod.status.phase,
                        "ready": all(container_status.ready for container_status in (pod.status.container_statuses or [])),
                        "containers": [container.name for container in pod.spec.containers],
                        "pod_ip": pod.status.pod_ip,
                        "node": pod.spec.node_name,
                        "created": pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None
                    }
                    for pod in response.items
                ]
                
            elif kind.lower() in ['service', 'services']:
                if namespace:
                    response = api.list_namespaced_service(namespace=namespace)
                else:
                    response = api.list_service_for_all_namespaces()
                    
                return [
                    {
                        "name": svc.metadata.name,
                        "namespace": svc.metadata.namespace,
                        "type": svc.spec.type,
                        "cluster_ip": svc.spec.cluster_ip,
                        "ports": [
                            {
                                "name": port.name,
                                "protocol": port.protocol,
                                "port": port.port,
                                "target_port": port.target_port
                            }
                            for port in svc.spec.ports
                        ] if svc.spec.ports else []
                    }
                    for svc in response.items
                ]
        
        elif group == "apps" and kind.lower() in ['deployment', 'deployments']:
            # Apps API resources
            api = client.AppsV1Api(api_client)
            
            if namespace:
                response = api.list_namespaced_deployment(namespace=namespace)
            else:
                response = api.list_deployment_for_all_namespaces()
                
            return [
                {
                    "name": dep.metadata.name,
                    "namespace": dep.metadata.namespace,
                    "replicas": {
                        "desired": dep.spec.replicas,
                        "ready": dep.status.ready_replicas,
                        "available": dep.status.available_replicas
                    },
                    "created": dep.metadata.creation_timestamp.isoformat() if dep.metadata.creation_timestamp else None
                }
                for dep in response.items
            ]
        
        elif group == "networking.k8s.io" and kind.lower() in ['ingress', 'ingresses']:
            # Networking API resources
            api = client.NetworkingV1Api(api_client)
            
            if namespace:
                response = api.list_namespaced_ingress(namespace=namespace)
            else:
                response = api.list_ingress_for_all_namespaces()
                
            return [
                {
                    "name": ing.metadata.name,
                    "namespace": ing.metadata.namespace,
                    "hosts": [
                        rule.host for rule in ing.spec.rules if rule.host
                    ],
                    "tls": [
                        {"hosts": tls.hosts, "secret_name": tls.secret_name}
                        for tls in ing.spec.tls
                    ] if ing.spec.tls else [],
                    "rules": [
                        {
                            "host": rule.host,
                            "paths": [
                                {
                                    "path": path.path,
                                    "path_type": path.path_type,
                                    "backend": {
                                        "service": {
                                            "name": path.backend.service.name,
                                            "port": path.backend.service.port.number if path.backend.service.port else None
                                        }
                                    } if path.backend.service else None
                                }
                                for path in rule.http.paths
                            ] if rule.http and rule.http.paths else []
                        }
                        for rule in ing.spec.rules
                    ] if ing.spec.rules else []
                }
                for ing in response.items
            ]
        
        else:
            # Generic API for other resource types
            api = client.CustomObjectsApi(api_client)
            version = version or "v1"
            group = group or ""
            
            if namespace:
                response = api.list_namespaced_custom_object(
                    group=group,
                    version=version,
                    namespace=namespace,
                    plural=kind.lower() + "s"  # This is a simplification, might need to be adjusted
                )
            else:
                response = api.list_cluster_custom_object(
                    group=group,
                    version=version,
                    plural=kind.lower() + "s"  # This is a simplification, might need to be adjusted
                )
                
            # For custom objects, return raw data as the structure varies widely
            return response.get("items", [])
    
    except ValueError as e:
        raise RuntimeError(str(e))
    except Exception as e:
        raise RuntimeError(
            f"Failed to list {kind} resources in context '{context}'"
            f"{f' namespace {namespace}' if namespace else ''}: {str(e)}"
        )

async def get_k8s_pod_logs(context: str, namespace: str, pod: str, 
                          previousContainer: bool = False, 
                          sinceDuration: str = None) -> str:
    """
    Get logs for a Kubernetes pod using specific context in a specified namespace.
    
    Args:
        context (str): Name of the Kubernetes context to use
        namespace (str): Name of the namespace where the pod is located
        pod (str): Name of the pod to get logs from
        previousContainer (bool, optional): Return previous terminated container logs, defaults to False
        sinceDuration (str, optional): Only return logs newer than a relative duration like 5s, 2m, or 3h
        
    Returns:
        str: The logs from the specified pod
        
    Raises:
        RuntimeError: If there's an error accessing the Kubernetes API
    """
    try:
        api_client = k8s_client.get_api_client(context)
        core_v1 = client.CoreV1Api(api_client)
        
        # Check if the pod exists
        try:
            pod_obj = core_v1.read_namespaced_pod(name=pod, namespace=namespace)
        except client.rest.ApiException as e:
            if e.status == 404:
                raise RuntimeError(f"Pod '{pod}' not found in namespace '{namespace}'")
            raise
        
        # Determine the container to get logs from
        container = None
        if len(pod_obj.spec.containers) > 1:
            # If multiple containers exist, use the first one and note this in the logs
            container = pod_obj.spec.containers[0].name
        
        # Get the logs
        logs = core_v1.read_namespaced_pod_log(
            name=pod,
            namespace=namespace,
            container=container,
            previous=previousContainer,
            since_seconds=_parse_duration_to_seconds(sinceDuration) if sinceDuration else None
        )
        
        if container and len(pod_obj.spec.containers) > 1:
            container_info = (
                f"Note: Pod has multiple containers, showing logs for container '{container}'. "
                f"Other containers: {', '.join(c.name for c in pod_obj.spec.containers if c.name != container)}\n\n"
            )
            return container_info + logs
            
        return logs
        
    except ValueError as e:
        raise RuntimeError(str(e))
    except Exception as e:
        raise RuntimeError(f"Failed to get pod logs: {str(e)}")

def _parse_duration_to_seconds(duration: str) -> int:
    """
    Parse a duration string like 5s, 2m, 3h to seconds.
    
    Args:
        duration (str): The duration string to parse
        
    Returns:
        int: Duration in seconds
        
    Raises:
        ValueError: If the duration string is invalid
    """
    if not duration:
        return None
        
    # Parse the duration string to seconds
    unit = duration[-1].lower()
    try:
        value = int(duration[:-1])
    except ValueError:
        raise ValueError(f"Invalid duration format: {duration}")
        
    if unit == 's':
        return value
    elif unit == 'm':
        return value * 60
    elif unit == 'h':
        return value * 3600
    elif unit == 'd':
        return value * 86400
    else:
        raise ValueError(f"Invalid duration unit: {unit}") 