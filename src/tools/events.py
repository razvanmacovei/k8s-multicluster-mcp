from typing import List, Dict, Any, Optional
import os
from kubernetes import client
from ..utils.k8s_client import KubernetesClient

# Initialize client with kubeconfig directory from environment or default
kubeconfig_dir = os.environ.get('KUBECONFIG_DIR', os.path.expanduser('~/.kube'))
k8s_client = KubernetesClient(kubeconfig_dir)

async def list_k8s_events(context: str, namespace: str, limit: Optional[int] = 100) -> List[Dict[str, Any]]:
    """
    List Kubernetes events using specific context in a specified namespace.
    
    Args:
        context (str): Name of the Kubernetes context to use
        namespace (str): Name of the namespace to list events from
        limit (int, optional): Maximum number of events to list. Defaults to 100.
        
    Returns:
        List[Dict[str, Any]]: A list of events with timestamp, reason, message, and source
        
    Raises:
        RuntimeError: If there's an error accessing the Kubernetes API
    """
    try:
        api_client = k8s_client.get_api_client(context)
        core_v1 = client.CoreV1Api(api_client)
        
        # Get events for the specified namespace
        events = core_v1.list_namespaced_event(namespace=namespace)
        
        # Sort by last timestamp (most recent first)
        sorted_events = sorted(
            events.items,
            key=lambda event: event.last_timestamp if event.last_timestamp else event.event_time if event.event_time else event.metadata.creation_timestamp,
            reverse=True
        )
        
        # Apply limit
        if limit and limit > 0:
            sorted_events = sorted_events[:limit]
        
        # Format the events
        result = []
        for event in sorted_events:
            # Get timestamp (might be in different fields depending on Kubernetes version)
            timestamp = None
            if event.last_timestamp:
                timestamp = event.last_timestamp.isoformat()
            elif event.event_time:
                timestamp = event.event_time.isoformat()
            elif event.metadata.creation_timestamp:
                timestamp = event.metadata.creation_timestamp.isoformat()
            
            # Build event object
            event_obj = {
                "timestamp": timestamp,
                "type": event.type,
                "reason": event.reason,
                "message": event.message,
                "count": event.count,
                "source": {
                    "component": event.source.component if event.source else None,
                    "host": event.source.host if event.source else None
                },
                "involved_object": {
                    "kind": event.involved_object.kind,
                    "namespace": event.involved_object.namespace,
                    "name": event.involved_object.name
                }
            }
            
            result.append(event_obj)
        
        return result
        
    except ValueError as e:
        raise RuntimeError(str(e))
    except Exception as e:
        raise RuntimeError(f"Failed to list events in context '{context}', namespace '{namespace}': {str(e)}") 