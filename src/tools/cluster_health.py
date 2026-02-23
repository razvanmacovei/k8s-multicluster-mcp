from typing import Dict, Any, List, Optional
import os
from kubernetes import client
from kubernetes.client.rest import ApiException

from ..utils.k8s_client import KubernetesClient

# Initialize client with kubeconfig directory from environment or default
kubeconfig_dir = os.environ.get('KUBECONFIG_DIR', os.path.expanduser('~/.kube'))
k8s_client = KubernetesClient(kubeconfig_dir)


async def k8s_cluster_health(context: str) -> Dict[str, Any]:
    """
    Get a comprehensive health summary of the Kubernetes cluster.
    Checks node status, pod health, resource pressure, and recent warning events.

    Args:
        context: The Kubernetes context to use

    Returns:
        Dict with cluster health summary including nodes, pods, and issues
    """
    try:
        api_client = k8s_client.get_api_client(context)
        core_v1 = client.CoreV1Api(api_client)
        apps_v1 = client.AppsV1Api(api_client)

        result = {
            "context": context,
            "health": "healthy",
            "nodes": {"total": 0, "ready": 0, "not_ready": 0, "issues": []},
            "pods": {"total": 0, "running": 0, "pending": 0, "failed": 0, "crashloop": 0, "issues": []},
            "deployments": {"total": 0, "available": 0, "unavailable": 0, "issues": []},
            "warnings": [],
        }

        # 1. Check node health
        nodes = core_v1.list_node()
        result["nodes"]["total"] = len(nodes.items)

        for node in nodes.items:
            is_ready = False
            for condition in node.status.conditions:
                if condition.type == "Ready":
                    if condition.status == "True":
                        is_ready = True
                        result["nodes"]["ready"] += 1
                    else:
                        result["nodes"]["not_ready"] += 1
                        result["nodes"]["issues"].append({
                            "node": node.metadata.name,
                            "issue": f"Node not ready: {condition.reason or 'unknown reason'}",
                            "message": condition.message
                        })
                elif condition.type in ["MemoryPressure", "DiskPressure", "PIDPressure"] and condition.status == "True":
                    result["nodes"]["issues"].append({
                        "node": node.metadata.name,
                        "issue": f"{condition.type} detected",
                        "message": condition.message
                    })

            if node.spec.unschedulable:
                result["nodes"]["issues"].append({
                    "node": node.metadata.name,
                    "issue": "Node is cordoned (unschedulable)"
                })

        # 2. Check pod health across all namespaces
        pods = core_v1.list_pod_for_all_namespaces()
        result["pods"]["total"] = len(pods.items)

        for pod in pods.items:
            phase = pod.status.phase
            if phase == "Running":
                result["pods"]["running"] += 1

                # Check for CrashLoopBackOff in running pods
                for cs in (pod.status.container_statuses or []):
                    if cs.state and cs.state.waiting and cs.state.waiting.reason == "CrashLoopBackOff":
                        result["pods"]["crashloop"] += 1
                        result["pods"]["issues"].append({
                            "pod": f"{pod.metadata.namespace}/{pod.metadata.name}",
                            "issue": f"Container '{cs.name}' in CrashLoopBackOff",
                            "restarts": cs.restart_count
                        })
                    elif cs.restart_count > 10:
                        result["pods"]["issues"].append({
                            "pod": f"{pod.metadata.namespace}/{pod.metadata.name}",
                            "issue": f"Container '{cs.name}' has {cs.restart_count} restarts",
                        })

            elif phase == "Pending":
                result["pods"]["pending"] += 1
                result["pods"]["issues"].append({
                    "pod": f"{pod.metadata.namespace}/{pod.metadata.name}",
                    "issue": "Pod is pending",
                })
            elif phase == "Failed":
                result["pods"]["failed"] += 1
                result["pods"]["issues"].append({
                    "pod": f"{pod.metadata.namespace}/{pod.metadata.name}",
                    "issue": f"Pod failed: {pod.status.reason or 'unknown reason'}",
                })

        # Limit pod issues to top 20
        if len(result["pods"]["issues"]) > 20:
            total_issues = len(result["pods"]["issues"])
            result["pods"]["issues"] = result["pods"]["issues"][:20]
            result["pods"]["issues"].append({
                "note": f"... and {total_issues - 20} more issues (showing top 20)"
            })

        # 3. Check deployment health
        deployments = apps_v1.list_deployment_for_all_namespaces()
        result["deployments"]["total"] = len(deployments.items)

        for dep in deployments.items:
            desired = dep.spec.replicas or 0
            available = dep.status.available_replicas or 0
            unavailable = dep.status.unavailable_replicas or 0

            if available >= desired:
                result["deployments"]["available"] += 1
            else:
                result["deployments"]["unavailable"] += 1
                result["deployments"]["issues"].append({
                    "deployment": f"{dep.metadata.namespace}/{dep.metadata.name}",
                    "issue": f"{available}/{desired} replicas available",
                    "unavailable": unavailable
                })

        # Limit deployment issues to top 15
        if len(result["deployments"]["issues"]) > 15:
            total_issues = len(result["deployments"]["issues"])
            result["deployments"]["issues"] = result["deployments"]["issues"][:15]
            result["deployments"]["issues"].append({
                "note": f"... and {total_issues - 15} more issues (showing top 15)"
            })

        # 4. Get recent warning events (last 20)
        try:
            events = core_v1.list_event_for_all_namespaces(
                field_selector="type=Warning",
                limit=20
            )

            for event in events.items:
                timestamp = None
                if event.last_timestamp:
                    timestamp = event.last_timestamp.isoformat()
                elif event.event_time:
                    timestamp = event.event_time.isoformat()

                result["warnings"].append({
                    "timestamp": timestamp,
                    "reason": event.reason,
                    "message": event.message,
                    "object": f"{event.involved_object.kind}/{event.involved_object.namespace or ''}/{event.involved_object.name}",
                    "count": event.count
                })
        except Exception:
            pass  # Events are supplementary, don't fail the whole check

        # 5. Determine overall health
        has_critical = (
            result["nodes"]["not_ready"] > 0
            or result["pods"]["failed"] > 0
            or result["pods"]["crashloop"] > 0
        )
        has_warnings = (
            result["pods"]["pending"] > 0
            or result["deployments"]["unavailable"] > 0
            or len(result["nodes"]["issues"]) > 0
        )

        if has_critical:
            result["health"] = "unhealthy"
        elif has_warnings:
            result["health"] = "degraded"
        else:
            result["health"] = "healthy"

        # Summary line
        result["summary"] = (
            f"Cluster: {result['health'].upper()} | "
            f"Nodes: {result['nodes']['ready']}/{result['nodes']['total']} ready | "
            f"Pods: {result['pods']['running']}/{result['pods']['total']} running | "
            f"Deployments: {result['deployments']['available']}/{result['deployments']['total']} available"
        )

        return result

    except Exception as e:
        raise RuntimeError(f"Failed to get cluster health: {str(e)}")
