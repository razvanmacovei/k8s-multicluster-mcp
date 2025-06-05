from typing import List, Dict, Any
import os
from kubernetes import client
from ..utils.k8s_client import KubernetesClient

# Initialize client with kubeconfig directory from environment or default
kubeconfig_dir = os.environ.get('KUBECONFIG_DIR', os.path.expanduser('~/.kube'))
k8s_client = KubernetesClient(kubeconfig_dir)

async def list_k8s_nodes(context: str) -> List[Dict[str, Any]]:
    """
    List all nodes in a Kubernetes cluster.
    
    Args:
        context (str): Name of the Kubernetes context to use
        
    Returns:
        List[Dict[str, Any]]: A list of node information with name, status, 
                             roles, version, and resource usage
        
    Raises:
        RuntimeError: If there's an error accessing the Kubernetes API
    """
    try:
        api_client = k8s_client.get_api_client(context)
        core_v1 = client.CoreV1Api(api_client)
        
        nodes = core_v1.list_node()
        
        result = []
        for node in nodes.items:
            # Extract roles from labels
            roles = []
            for label_key, label_value in node.metadata.labels.items():
                if label_key.startswith('node-role.kubernetes.io/') and label_value == 'true':
                    roles.append(label_key.replace('node-role.kubernetes.io/', ''))
            
            # Determine node status
            node_status = "Unknown"
            for condition in node.status.conditions:
                if condition.type == "Ready":
                    node_status = "Ready" if condition.status == "True" else "NotReady"
                    break
            
            # Extract resource capacity and allocatable resources
            capacity = {
                "cpu": node.status.capacity.get('cpu'),
                "memory": node.status.capacity.get('memory'),
                "pods": node.status.capacity.get('pods')
            }
            
            allocatable = {
                "cpu": node.status.allocatable.get('cpu'),
                "memory": node.status.allocatable.get('memory'),
                "pods": node.status.allocatable.get('pods')
            }
            
            # Get kubelet version
            kubelet_version = node.status.node_info.kubelet_version if node.status.node_info else None
            
            # Add node to result
            result.append({
                "name": node.metadata.name,
                "status": node_status,
                "roles": roles if roles else ["<none>"],
                "kubelet_version": kubelet_version,
                "internal_ip": next(
                    (addr.address for addr in node.status.addresses if addr.type == "InternalIP"), 
                    None
                ),
                "external_ip": next(
                    (addr.address for addr in node.status.addresses if addr.type == "ExternalIP"), 
                    None
                ),
                "os": getattr(node.status.node_info, 'os', None) if node.status.node_info else None,
                "architecture": node.status.node_info.architecture if node.status.node_info else None,
                "capacity": capacity,
                "allocatable": allocatable,
                "created": node.metadata.creation_timestamp.isoformat() if node.metadata.creation_timestamp else None,
            })
        
        return result
        
    except ValueError as e:
        raise RuntimeError(str(e))
    except Exception as e:
        raise RuntimeError(f"Failed to list nodes in context '{context}': {str(e)}") 