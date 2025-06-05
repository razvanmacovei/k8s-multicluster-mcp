from typing import Dict, List, Any, Optional, Union
import os
import json
from kubernetes import client
from kubernetes.client.rest import ApiException

from ..utils.k8s_client import KubernetesClient

# Initialize client with kubeconfig directory from environment or default
kubeconfig_dir = os.environ.get('KUBECONFIG_DIR', os.path.expanduser('~/.kube'))
k8s_client = KubernetesClient(kubeconfig_dir)

async def k8s_cordon(context: str, node_name: str) -> Dict[str, Any]:
    """
    Mark a node as unschedulable.
    
    Args:
        context (str): The Kubernetes context to use
        node_name (str): The name of the node to cordon
        
    Returns:
        Dict[str, Any]: Information about the updated node
        
    Raises:
        RuntimeError: If there's an error cordoning the node
    """
    try:
        # Get the API client for the specified context
        api_client = k8s_client.get_api_client(context)
        api_instance = client.CoreV1Api(api_client)
        
        # Get the current node
        node = api_instance.read_node(name=node_name)
        
        # Update the node spec to mark it as unschedulable
        node.spec.unschedulable = True
        
        # Update the node
        result = api_instance.patch_node(name=node_name, body=node)
        
        return {
            "status": "Success",
            "message": f"Successfully cordoned node '{node_name}'",
            "node": {
                "name": result.metadata.name,
                "unschedulable": result.spec.unschedulable
            }
        }
    except ApiException as e:
        raise RuntimeError(f"Failed to cordon node '{node_name}': {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error cordoning node '{node_name}': {str(e)}")

async def k8s_uncordon(context: str, node_name: str) -> Dict[str, Any]:
    """
    Mark a node as schedulable.
    
    Args:
        context (str): The Kubernetes context to use
        node_name (str): The name of the node to uncordon
        
    Returns:
        Dict[str, Any]: Information about the updated node
        
    Raises:
        RuntimeError: If there's an error uncordoning the node
    """
    try:
        # Get the API client for the specified context
        api_client = k8s_client.get_api_client(context)
        api_instance = client.CoreV1Api(api_client)
        
        # Get the current node
        node = api_instance.read_node(name=node_name)
        
        # Update the node spec to mark it as schedulable
        node.spec.unschedulable = False
        
        # Update the node
        result = api_instance.patch_node(name=node_name, body=node)
        
        return {
            "status": "Success",
            "message": f"Successfully uncordoned node '{node_name}'",
            "node": {
                "name": result.metadata.name,
                "unschedulable": result.spec.unschedulable
            }
        }
    except ApiException as e:
        raise RuntimeError(f"Failed to uncordon node '{node_name}': {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error uncordoning node '{node_name}': {str(e)}")

async def k8s_drain(context: str, node_name: str, force: Optional[bool] = False,
                   ignore_daemonsets: Optional[bool] = False, 
                   delete_local_data: Optional[bool] = False,
                   timeout: Optional[int] = None) -> Dict[str, Any]:
    """
    Drain a node in preparation for maintenance.
    
    Args:
        context (str): The Kubernetes context to use
        node_name (str): The name of the node to drain
        force (bool, optional): Force drain even if there are pods not managed by a ReplicationController, Job, or DaemonSet
        ignore_daemonsets (bool, optional): Ignore DaemonSet-managed pods
        delete_local_data (bool, optional): Delete local data when evicting pods
        timeout (int, optional): The length of time to wait before giving up, zero means infinite
        
    Returns:
        Dict[str, Any]: Information about the drain operation
        
    Raises:
        RuntimeError: If there's an error draining the node
    """
    try:
        # Get the API client for the specified context
        api_client = k8s_client.get_api_client(context)
        api_instance = client.CoreV1Api(api_client)
        
        # First, cordon the node (mark it as unschedulable)
        await k8s_cordon(context, node_name)
        
        # Get pods on the node
        field_selector = f"spec.nodeName={node_name}"
        pods = api_instance.list_pod_for_all_namespaces(field_selector=field_selector)
        
        eviction_results = []
        
        # Process each pod
        for pod in pods.items:
            # Skip DaemonSet-managed pods if ignore_daemonsets is True
            if ignore_daemonsets and pod.metadata.owner_references:
                is_daemonset_pod = any(
                    owner.kind == "DaemonSet" for owner in pod.metadata.owner_references
                )
                if is_daemonset_pod:
                    eviction_results.append({
                        "pod": f"{pod.metadata.namespace}/{pod.metadata.name}",
                        "status": "Skipped",
                        "reason": "DaemonSet-managed pod"
                    })
                    continue
            
            # Check if pod has local storage and if we should delete it
            has_local_storage = any(
                volume.empty_dir is not None for volume in (pod.spec.volumes or [])
            )
            if has_local_storage and not delete_local_data:
                if not force:
                    eviction_results.append({
                        "pod": f"{pod.metadata.namespace}/{pod.metadata.name}",
                        "status": "Skipped",
                        "reason": "Has local storage and --delete-local-data not specified"
                    })
                    continue
            
            # Check if pod is managed by a controller
            is_managed = pod.metadata.owner_references and any(
                owner.kind in ["ReplicationController", "Job", "DaemonSet", "StatefulSet", "Deployment"]
                for owner in pod.metadata.owner_references
            )
            if not is_managed and not force:
                eviction_results.append({
                    "pod": f"{pod.metadata.namespace}/{pod.metadata.name}",
                    "status": "Skipped",
                    "reason": "Not managed by a controller and --force not specified"
                })
                continue
            
            # Create an eviction for the pod
            try:
                # Create eviction object
                eviction = client.V1Eviction(
                    metadata=client.V1ObjectMeta(
                        name=pod.metadata.name,
                        namespace=pod.metadata.namespace
                    )
                )
                
                # Evict the pod
                api_instance.create_namespaced_pod_eviction(
                    name=pod.metadata.name,
                    namespace=pod.metadata.namespace,
                    body=eviction
                )
                
                eviction_results.append({
                    "pod": f"{pod.metadata.namespace}/{pod.metadata.name}",
                    "status": "Evicted",
                    "reason": "Successfully evicted"
                })
            except ApiException as e:
                eviction_results.append({
                    "pod": f"{pod.metadata.namespace}/{pod.metadata.name}",
                    "status": "Error",
                    "reason": f"Failed to evict: {str(e)}"
                })
        
        return {
            "status": "Success",
            "message": f"Node '{node_name}' drain operation completed",
            "eviction_results": eviction_results
        }
    except ApiException as e:
        raise RuntimeError(f"Failed to drain node '{node_name}': {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error draining node '{node_name}': {str(e)}")

async def k8s_taint(context: str, node_name: str, key: str, value: Optional[str] = None, 
                   effect: str = "NoSchedule") -> Dict[str, Any]:
    """
    Update the taints on one or more nodes.
    
    Args:
        context (str): The Kubernetes context to use
        node_name (str): The name of the node to taint
        key (str): The taint key to add
        value (str, optional): The taint value
        effect (str): The taint effect (NoSchedule, PreferNoSchedule, or NoExecute)
        
    Returns:
        Dict[str, Any]: Information about the updated node
        
    Raises:
        RuntimeError: If there's an error tainting the node
    """
    try:
        # Validate effect value
        valid_effects = ["NoSchedule", "PreferNoSchedule", "NoExecute"]
        if effect not in valid_effects:
            raise ValueError(f"Invalid taint effect: {effect}. Must be one of: {', '.join(valid_effects)}")
        
        # Get the API client for the specified context
        api_client = k8s_client.get_api_client(context)
        api_instance = client.CoreV1Api(api_client)
        
        # Get the current node
        node = api_instance.read_node(name=node_name)
        
        # Create the new taint
        new_taint = client.V1Taint(
            key=key,
            value=value,
            effect=effect
        )
        
        # Add taint to the node
        # First, check if the node already has taints
        if not node.spec.taints:
            node.spec.taints = []
        
        # Check if a taint with the same key and effect already exists
        existing_taint_index = next(
            (i for i, taint in enumerate(node.spec.taints) 
             if taint.key == key and taint.effect == effect),
            None
        )
        
        if existing_taint_index is not None:
            # Update the existing taint
            node.spec.taints[existing_taint_index] = new_taint
        else:
            # Add a new taint
            node.spec.taints.append(new_taint)
        
        # Update the node
        result = api_instance.patch_node(name=node_name, body=node)
        
        # Format taints for response
        taints = [
            {"key": t.key, "value": t.value, "effect": t.effect}
            for t in result.spec.taints or []
        ]
        
        return {
            "status": "Success",
            "message": f"Successfully added taint to node '{node_name}'",
            "node": {
                "name": result.metadata.name,
                "taints": taints
            }
        }
    except ApiException as e:
        raise RuntimeError(f"Failed to taint node '{node_name}': {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error tainting node '{node_name}': {str(e)}")

async def k8s_untaint(context: str, node_name: str, key: str, effect: Optional[str] = None) -> Dict[str, Any]:
    """
    Remove the taints from a node.
    
    Args:
        context (str): The Kubernetes context to use
        node_name (str): The name of the node to untaint
        key (str): The taint key to remove
        effect (str, optional): The taint effect to remove (if not specified, all effects with the given key will be removed)
        
    Returns:
        Dict[str, Any]: Information about the updated node
        
    Raises:
        RuntimeError: If there's an error untainting the node
    """
    try:
        # Get the API client for the specified context
        api_client = k8s_client.get_api_client(context)
        api_instance = client.CoreV1Api(api_client)
        
        # Get the current node
        node = api_instance.read_node(name=node_name)
        
        # If the node has no taints, return early
        if not node.spec.taints:
            return {
                "status": "Success",
                "message": f"Node '{node_name}' does not have any taints",
                "node": {
                    "name": node.metadata.name,
                    "taints": []
                }
            }
        
        # Filter out the taints that should be removed
        if effect:
            # Remove taints with specific key and effect
            node.spec.taints = [
                taint for taint in node.spec.taints
                if not (taint.key == key and taint.effect == effect)
            ]
        else:
            # Remove all taints with the specific key
            node.spec.taints = [
                taint for taint in node.spec.taints
                if taint.key != key
            ]
        
        # Update the node
        result = api_instance.patch_node(name=node_name, body=node)
        
        # Format taints for response
        taints = [
            {"key": t.key, "value": t.value, "effect": t.effect}
            for t in result.spec.taints or []
        ]
        
        return {
            "status": "Success",
            "message": f"Successfully removed taint(s) from node '{node_name}'",
            "node": {
                "name": result.metadata.name,
                "taints": taints
            }
        }
    except ApiException as e:
        raise RuntimeError(f"Failed to untaint node '{node_name}': {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error untainting node '{node_name}': {str(e)}") 