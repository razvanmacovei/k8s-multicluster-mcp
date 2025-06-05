from typing import Dict, List, Any, Optional, Union
import os
from kubernetes import client
from kubernetes.client.rest import ApiException

from ..utils.k8s_client import KubernetesClient

# Initialize client with kubeconfig directory from environment or default
kubeconfig_dir = os.environ.get('KUBECONFIG_DIR', os.path.expanduser('~/.kube'))
k8s_client = KubernetesClient(kubeconfig_dir)

async def k8s_expose(context: str, resource_type: str, name: str, port: int, target_port: Optional[int] = None,
                    namespace: Optional[str] = None, protocol: Optional[str] = None,
                    service_name: Optional[str] = None, labels: Optional[Dict[str, str]] = None,
                    selector: Optional[str] = None, type: Optional[str] = None) -> Dict[str, Any]:
    """
    Expose a resource as a new Kubernetes service.
    
    Args:
        context (str): The Kubernetes context to use
        resource_type (str): The type of resource to expose
        name (str): The name of the resource to expose
        port (int): The port that the service should serve on
        target_port (int, optional): The port on the container that the service should direct traffic to
        namespace (str, optional): The namespace of the resource
        protocol (str, optional): The network protocol for the service
        service_name (str, optional): The name for the new service
        labels (Dict[str, str], optional): Labels to apply to the service
        selector (str, optional): Selector (label query) to filter on
        type (str, optional): The type of service to create
        
    Returns:
        Dict[str, Any]: Information about the created service
        
    Raises:
        RuntimeError: If there's an error exposing the resource
    """
    try:
        # Get the API client for the specified context
        api_client = k8s_client.get_api_client(context)
        api_instance = client.CoreV1Api(api_client)
        
        # Set default namespace if not provided
        namespace = namespace or 'default'
        
        # Create service body
        service = client.V1Service()
        service.api_version = "v1"
        service.kind = "Service"
        
        # Set service metadata
        metadata = client.V1ObjectMeta()
        metadata.name = service_name or f"{name}-service"
        if labels:
            metadata.labels = labels
        service.metadata = metadata
        
        # Set service spec
        spec = client.V1ServiceSpec()
        spec.ports = [
            client.V1ServicePort(
                port=port,
                target_port=target_port or port,
                protocol=protocol or "TCP"
            )
        ]
        
        # Set selector
        if selector:
            # Parse selector string into a dict
            selector_parts = selector.split(',')
            selector_dict = {}
            for part in selector_parts:
                if '=' in part:
                    key, value = part.split('=', 1)
                    selector_dict[key.strip()] = value.strip()
            spec.selector = selector_dict
        else:
            # Default selector based on resource name
            spec.selector = {"app": name}
        
        # Set service type if provided
        if type:
            spec.type = type
        
        service.spec = spec
        
        # Create the service
        result = api_instance.create_namespaced_service(namespace=namespace, body=service)
        
        return {
            "status": "Success",
            "message": f"Successfully exposed {resource_type} '{name}' as service '{metadata.name}'",
            "service": {
                "name": result.metadata.name,
                "namespace": result.metadata.namespace,
                "type": result.spec.type,
                "cluster_ip": result.spec.cluster_ip,
                "ports": [
                    {"port": port.port, "target_port": port.target_port, "protocol": port.protocol}
                    for port in result.spec.ports
                ]
            }
        }
    except ApiException as e:
        raise RuntimeError(f"Failed to expose {resource_type} '{name}': {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error exposing {resource_type} '{name}': {str(e)}")

async def k8s_run(context: str, name: str, image: str, namespace: Optional[str] = None,
                 command: Optional[List[str]] = None, env: Optional[Dict[str, str]] = None,
                 labels: Optional[Dict[str, str]] = None, restart: Optional[str] = None) -> Dict[str, Any]:
    """
    Create and run a particular image in a pod.
    
    Args:
        context (str): The Kubernetes context to use
        name (str): The name of the pod
        image (str): The container image to run
        namespace (str, optional): The namespace to run the pod in
        command (List[str], optional): The command to run in the container
        env (Dict[str, str], optional): Environment variables to set in the container
        labels (Dict[str, str], optional): Labels to apply to the pod
        restart (str, optional): The restart policy for the pod
        
    Returns:
        Dict[str, Any]: Information about the created pod
        
    Raises:
        RuntimeError: If there's an error creating the pod
    """
    try:
        # Get the API client for the specified context
        api_client = k8s_client.get_api_client(context)
        api_instance = client.CoreV1Api(api_client)
        
        # Set default namespace if not provided
        namespace = namespace or 'default'
        
        # Create pod body
        pod = client.V1Pod()
        pod.api_version = "v1"
        pod.kind = "Pod"
        
        # Set pod metadata
        metadata = client.V1ObjectMeta()
        metadata.name = name
        if labels:
            metadata.labels = labels
        else:
            metadata.labels = {"app": name}
        pod.metadata = metadata
        
        # Set pod spec
        spec = client.V1PodSpec()
        
        # Create container - ensure it's always initialized
        container = client.V1Container(name=name, image=image)
        
        # Set command if provided
        if command:
            container.command = command
        
        # Set environment variables if provided
        if env:
            env_vars = []
            for key, value in env.items():
                env_vars.append(client.V1EnvVar(name=key, value=value))
            container.env = env_vars
        
        # Add container to pod spec - ensure containers list is not None
        spec.containers = [container]
        
        # Set restart policy if provided
        if restart:
            spec.restart_policy = restart
        
        pod.spec = spec
        
        # Create the pod
        result = api_instance.create_namespaced_pod(namespace=namespace, body=pod)
        
        return {
            "status": "Success",
            "message": f"Successfully created pod '{name}' with image '{image}'",
            "pod": {
                "name": result.metadata.name,
                "namespace": result.metadata.namespace,
                "image": image,
                "status": result.status.phase
            }
        }
    except ApiException as e:
        raise RuntimeError(f"Failed to create pod '{name}': {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error creating pod '{name}': {str(e)}")

async def k8s_set_resources(context: str, resource_type: str, resource_name: str,
                           namespace: Optional[str] = None, containers: Optional[List[str]] = None,
                           limits: Optional[Dict[str, str]] = None, 
                           requests: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Set resource limits and requests for containers.
    
    Args:
        context (str): The Kubernetes context to use
        resource_type (str): The type of resource to update
        resource_name (str): The name of the resource to update
        namespace (str, optional): The namespace of the resource
        containers (List[str], optional): Specific containers to update (all by default)
        limits (Dict[str, str], optional): Resource limits to set (e.g., {"cpu": "100m", "memory": "128Mi"})
        requests (Dict[str, str], optional): Resource requests to set (e.g., {"cpu": "10m", "memory": "64Mi"})
        
    Returns:
        Dict[str, Any]: Information about the updated resource
        
    Raises:
        RuntimeError: If there's an error updating the resource
    """
    try:
        # Get the API client for the specified context
        api_client = k8s_client.get_api_client(context)
        
        # Set default namespace if not provided
        namespace = namespace or 'default'
        
        # Normalize resource_type
        resource_type = resource_type.lower()
        
        # Create the resource requirements
        requirements = {}
        if limits:
            requirements["limits"] = limits
        if requests:
            requirements["requests"] = requests
        
        # If no resource requirements specified, raise an error
        if not requirements:
            raise ValueError("No resource limits or requests specified")
        
        # Ensure containers is a list, not None
        containers = containers or []
        
        # Handle different resource types
        if resource_type in ['deployment', 'deployments']:
            api_instance = client.AppsV1Api(api_client)
            
            # Get the current deployment
            deployment = api_instance.read_namespaced_deployment(name=resource_name, namespace=namespace)
            
            # Verify that containers exist in the spec
            if not deployment.spec.template.spec.containers:
                raise ValueError("No containers found in deployment specification")
                
            # Apply resource requirements to specified containers or all if none specified
            for container in deployment.spec.template.spec.containers:
                if not containers or container.name in containers:
                    if not container.resources:
                        container.resources = client.V1ResourceRequirements()
                    
                    if limits:
                        container.resources.limits = limits
                    if requests:
                        container.resources.requests = requests
            
            # Update the deployment
            result = api_instance.patch_namespaced_deployment(
                name=resource_name,
                namespace=namespace,
                body=deployment
            )
            
            return {
                "status": "Success",
                "message": f"Successfully updated resources for deployment '{resource_name}'",
                "updated_containers": [
                    c.name for c in result.spec.template.spec.containers 
                    if not containers or c.name in containers
                ]
            }
        
        elif resource_type in ['statefulset', 'statefulsets']:
            api_instance = client.AppsV1Api(api_client)
            
            # Get the current statefulset
            statefulset = api_instance.read_namespaced_stateful_set(name=resource_name, namespace=namespace)
            
            # Verify that containers exist in the spec
            if not statefulset.spec.template.spec.containers:
                raise ValueError("No containers found in statefulset specification")
                
            # Apply resource requirements to specified containers or all if none specified
            for container in statefulset.spec.template.spec.containers:
                if not containers or container.name in containers:
                    if not container.resources:
                        container.resources = client.V1ResourceRequirements()
                    
                    if limits:
                        container.resources.limits = limits
                    if requests:
                        container.resources.requests = requests
            
            # Update the statefulset
            result = api_instance.patch_namespaced_stateful_set(
                name=resource_name,
                namespace=namespace,
                body=statefulset
            )
            
            return {
                "status": "Success",
                "message": f"Successfully updated resources for statefulset '{resource_name}'",
                "updated_containers": [
                    c.name for c in result.spec.template.spec.containers 
                    if not containers or c.name in containers
                ]
            }
        
        elif resource_type in ['daemonset', 'daemonsets']:
            api_instance = client.AppsV1Api(api_client)
            
            # Get the current daemonset
            daemonset = api_instance.read_namespaced_daemon_set(name=resource_name, namespace=namespace)
            
            # Verify that containers exist in the spec
            if not daemonset.spec.template.spec.containers:
                raise ValueError("No containers found in daemonset specification")
                
            # Apply resource requirements to specified containers or all if none specified
            for container in daemonset.spec.template.spec.containers:
                if not containers or container.name in containers:
                    if not container.resources:
                        container.resources = client.V1ResourceRequirements()
                    
                    if limits:
                        container.resources.limits = limits
                    if requests:
                        container.resources.requests = requests
            
            # Update the daemonset
            result = api_instance.patch_namespaced_daemon_set(
                name=resource_name,
                namespace=namespace,
                body=daemonset
            )
            
            return {
                "status": "Success",
                "message": f"Successfully updated resources for daemonset '{resource_name}'",
                "updated_containers": [
                    c.name for c in result.spec.template.spec.containers 
                    if not containers or c.name in containers
                ]
            }
            
        else:
            raise ValueError(f"Resource type '{resource_type}' not supported for resource updates")
            
    except ApiException as e:
        raise RuntimeError(f"Failed to update resources for {resource_type} '{resource_name}': {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error updating resources for {resource_type} '{resource_name}': {str(e)}") 