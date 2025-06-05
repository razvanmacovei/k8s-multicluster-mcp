import os
import re
from typing import Any, Dict, Optional

from kubernetes import client

from ..utils.k8s_client import KubernetesClient

# Initialize client with kubeconfig directory from environment or default
kubeconfig_dir = os.environ.get("KUBECONFIG_DIR", os.path.expanduser("~/.kube"))
k8s_client = KubernetesClient(kubeconfig_dir)


async def diagnose_k8s_application(
    context: str, namespace: str, app_name: str, resource_type: Optional[str] = "deployment"
) -> Dict[str, Any]:
    """
    Diagnose issues with a Kubernetes application by checking resource status, events, and logs.

    Args:
        context (str): Name of the Kubernetes context to use
        namespace (str): Namespace where the application is located
        app_name (str): Name of the application/deployment/statefulset
        resource_type (str, optional): Type of resource to diagnose (deployment, statefulset, etc.)

    Returns:
        Dict[str, Any]: Diagnostic information about the application

    Raises:
        RuntimeError: If there's an error accessing the Kubernetes API
    """
    try:
        api_client = k8s_client.get_api_client(context)
        core_v1 = client.CoreV1Api(api_client)
        apps_v1 = client.AppsV1Api(api_client)

        resource_type = resource_type.lower()
        result = {
            "application": app_name,
            "namespace": namespace,
            "resource_type": resource_type,
            "status": {},
            "issues": [],
            "pods": [],
            "events": [],
        }

        # 1. Check resource status based on type
        try:
            if resource_type == "deployment":
                resource = apps_v1.read_namespaced_deployment(name=app_name, namespace=namespace)

                result["status"] = {
                    "replicas": {
                        "desired": resource.spec.replicas,
                        "ready": resource.status.ready_replicas or 0,
                        "available": resource.status.available_replicas or 0,
                        "unavailable": resource.status.unavailable_replicas or 0,
                    },
                    "conditions": [
                        {
                            "type": condition.type,
                            "status": condition.status,
                            "reason": condition.reason,
                            "message": condition.message,
                        }
                        for condition in resource.status.conditions or []
                    ],
                }

                # Check for deployment health
                if resource.status.unavailable_replicas:
                    result["issues"].append(
                        {
                            "severity": "warning",
                            "issue": f"Deployment has {resource.status.unavailable_replicas} unavailable replicas",
                        }
                    )

                if resource.status.ready_replicas != resource.spec.replicas:
                    result["issues"].append(
                        {
                            "severity": "warning",
                            "issue": (
                                f"Deployment has {resource.status.ready_replicas or 0}/"
                                f"{resource.spec.replicas} ready replicas"
                            ),
                        }
                    )

                # Get pod selector
                pod_selector = resource.spec.selector.match_labels

            elif resource_type == "statefulset":
                resource = apps_v1.read_namespaced_stateful_set(name=app_name, namespace=namespace)

                result["status"] = {
                    "replicas": {
                        "desired": resource.spec.replicas,
                        "ready": resource.status.ready_replicas or 0,
                        "current": resource.status.current_replicas or 0,
                        "updated": resource.status.updated_replicas or 0,
                    }
                }

                # Check for statefulset health
                if resource.status.ready_replicas != resource.spec.replicas:
                    result["issues"].append(
                        {
                            "severity": "warning",
                            "issue": f"StatefulSet has {resource.status.ready_replicas or 0}/{resource.spec.replicas} ready replicas",
                        }
                    )

                # Get pod selector
                pod_selector = resource.spec.selector.match_labels

            elif resource_type == "service":
                resource = core_v1.read_namespaced_service(name=app_name, namespace=namespace)

                result["status"] = {
                    "type": resource.spec.type,
                    "cluster_ip": resource.spec.cluster_ip,
                    "ports": [
                        {
                            "name": port.name,
                            "port": port.port,
                            "target_port": port.target_port,
                            "protocol": port.protocol,
                        }
                        for port in resource.spec.ports or []
                    ],
                }

                # Get pod selector
                pod_selector = resource.spec.selector

            else:
                # For other resource types, try to get pods by label selector
                pod_selector = {"app": app_name}
                result["status"] = {"message": f"Using default label selector for {resource_type}: {pod_selector}"}

        except client.rest.ApiException as e:
            if e.status == 404:
                result["issues"].append(
                    {
                        "severity": "error",
                        "issue": f"{resource_type.capitalize()} '{app_name}' not found in namespace '{namespace}'",
                    }
                )
                return result
            else:
                raise

        # 2. Get pods associated with the application using selector
        selector_str = ",".join([f"{k}={v}" for k, v in pod_selector.items()])
        pods = core_v1.list_namespaced_pod(namespace=namespace, label_selector=selector_str)

        if not pods.items:
            result["issues"].append(
                {
                    "severity": "warning",
                    "issue": f"No pods found for {resource_type}/{app_name} with selector {selector_str}",
                }
            )

        # 3. Check pod status and look for common issues
        for pod in pods.items:
            pod_status = {
                "name": pod.metadata.name,
                "phase": pod.status.phase,
                "node": pod.spec.node_name,
                "restart_count": sum(container.restart_count for container in (pod.status.container_statuses or [])),
                "ready": all(container.ready for container in (pod.status.container_statuses or [])),
                "containers": [],
            }

            # Check container status
            for container in pod.status.container_statuses or []:
                container_status = {
                    "name": container.name,
                    "ready": container.ready,
                    "restart_count": container.restart_count,
                    "image": container.image,
                    "state": "unknown",
                }

                # Determine container state
                if container.state.running:
                    container_status["state"] = "running"
                elif container.state.waiting:
                    container_status["state"] = "waiting"
                    container_status["reason"] = container.state.waiting.reason
                    container_status["message"] = container.state.waiting.message

                    # Check for common issues
                    if container.state.waiting.reason == "CrashLoopBackOff":
                        result["issues"].append(
                            {
                                "severity": "error",
                                "issue": f"Container {container.name} in pod {pod.metadata.name} is in CrashLoopBackOff state",
                                "message": container.state.waiting.message,
                            }
                        )
                    elif container.state.waiting.reason == "ImagePullBackOff":
                        result["issues"].append(
                            {
                                "severity": "error",
                                "issue": f"Container {container.name} in pod {pod.metadata.name} cannot pull image",
                                "message": container.state.waiting.message,
                            }
                        )
                    elif container.state.waiting.reason == "ErrImagePull":
                        result["issues"].append(
                            {
                                "severity": "error",
                                "issue": f"Container {container.name} in pod {pod.metadata.name} has image pull error",
                                "message": container.state.waiting.message,
                            }
                        )
                elif container.state.terminated:
                    container_status["state"] = "terminated"
                    container_status["reason"] = container.state.terminated.reason
                    container_status["exit_code"] = container.state.terminated.exit_code

                    # Check for OOMKilled
                    if container.state.terminated.reason == "OOMKilled":
                        result["issues"].append(
                            {
                                "severity": "error",
                                "issue": f"Container {container.name} in pod {pod.metadata.name} was terminated due to OOM (Out of Memory)",
                                "recommendation": "Consider increasing memory limits for this container",
                            }
                        )
                    # Check for other termination issues
                    elif container.state.terminated.exit_code != 0:
                        result["issues"].append(
                            {
                                "severity": "error",
                                "issue": f"Container {container.name} in pod {pod.metadata.name} terminated with exit code {container.state.terminated.exit_code}",
                                "reason": container.state.terminated.reason,
                            }
                        )

                # Check for high restart count
                if container.restart_count > 5:
                    result["issues"].append(
                        {
                            "severity": "warning",
                            "issue": f"Container {container.name} in pod {pod.metadata.name} has restarted {container.restart_count} times",
                            "recommendation": "Check logs for errors",
                        }
                    )

                pod_status["containers"].append(container_status)

            # Add pod status to result
            result["pods"].append(pod_status)

        # 4. Get recent events related to the application
        events = core_v1.list_namespaced_event(namespace=namespace, field_selector=f"involvedObject.name={app_name}")

        # Add additional pod events
        for pod in pods.items:
            pod_events = core_v1.list_namespaced_event(
                namespace=namespace, field_selector=f"involvedObject.name={pod.metadata.name}"
            )
            events.items.extend(pod_events.items)

        # Sort events by last timestamp
        sorted_events = sorted(
            events.items, key=lambda e: e.last_timestamp if e.last_timestamp else e.event_time, reverse=True
        )

        # Extract key event information
        for event in sorted_events[:10]:  # Limit to 10 most recent events
            event_info = {
                "type": event.type,
                "reason": event.reason,
                "message": event.message,
                "count": event.count,
                "object": f"{event.involved_object.kind}/{event.involved_object.name}",
                "timestamp": (
                    event.last_timestamp.isoformat()
                    if event.last_timestamp
                    else (event.event_time.isoformat() if event.event_time else None)
                ),
            }

            # Flag warning/error events
            if event.type == "Warning":
                if any(error_reason in event.reason for error_reason in ["Failed", "Error", "BackOff"]):
                    result["issues"].append(
                        {
                            "severity": "error",
                            "issue": f"Event: {event.reason} for {event.involved_object.kind}/{event.involved_object.name}",
                            "message": event.message,
                        }
                    )

            result["events"].append(event_info)

        # 5. Check logs for the first problematic pod if issues were found
        problematic_pods = [pod for pod in result["pods"] if not pod["ready"] or pod["restart_count"] > 0]

        if problematic_pods and len(result["issues"]) > 0:
            target_pod = problematic_pods[0]

            # Try to get logs for the first container in the problematic pod
            if target_pod["containers"]:
                target_container = target_pod["containers"][0]["name"]

                try:
                    logs = core_v1.read_namespaced_pod_log(
                        name=target_pod["name"],
                        namespace=namespace,
                        container=target_container,
                        tail_lines=50,  # Get last 50 lines
                    )

                    # Look for common error patterns in logs
                    oom_pattern = re.compile(r"(Out of memory|Killed|oom-kill)")
                    permission_pattern = re.compile(r"(permission denied|unauthorized|forbidden)", re.IGNORECASE)
                    connection_pattern = re.compile(
                        r"(connection refused|cannot connect|connect failed)", re.IGNORECASE
                    )

                    if oom_pattern.search(logs):
                        result["issues"].append(
                            {
                                "severity": "error",
                                "issue": f"Out of Memory issue detected in logs for container {target_container}",
                                "recommendation": "Increase memory limits and/or optimize application memory usage",
                            }
                        )

                    if permission_pattern.search(logs):
                        result["issues"].append(
                            {
                                "severity": "error",
                                "issue": f"Permission or authorization issue detected in logs for container {target_container}",
                                "recommendation": "Check RBAC permissions or service account settings",
                            }
                        )

                    if connection_pattern.search(logs):
                        result["issues"].append(
                            {
                                "severity": "warning",
                                "issue": f"Connection issue detected in logs for container {target_container}",
                                "recommendation": "Check network policies, service connectivity, or firewall rules",
                            }
                        )

                    # Add logs to result
                    result["log_sample"] = {
                        "pod": target_pod["name"],
                        "container": target_container,
                        "content": logs[-2000:] if len(logs) > 2000 else logs,  # Limit log size
                    }

                except Exception as log_error:
                    result["log_error"] = str(log_error)

        # 6. Add general recommendations based on issues found
        if any(issue["severity"] == "error" for issue in result["issues"]):
            result["status"]["health"] = "unhealthy"
        elif any(issue["severity"] == "warning" for issue in result["issues"]):
            result["status"]["health"] = "degraded"
        else:
            result["status"]["health"] = "healthy"

        return result

    except Exception as e:
        raise RuntimeError(f"Failed to diagnose application: {str(e)}")
