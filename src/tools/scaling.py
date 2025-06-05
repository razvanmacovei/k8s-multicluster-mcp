import os
from typing import Any, Dict, Optional

from kubernetes import client

from ..utils.k8s_client import KubernetesClient

# Initialize client with kubeconfig directory from environment or default
kubeconfig_dir = os.environ.get("KUBECONFIG_DIR", os.path.expanduser("~/.kube"))
k8s_client = KubernetesClient(kubeconfig_dir)


async def k8s_scale_resource(
    context: str, namespace: str, resource_type: str, name: str, replicas: int
) -> Dict[str, Any]:
    """
    Scale a deployment, statefulset, or replicaset to the specified number of replicas.

    Args:
        context (str): Name of the Kubernetes context to use
        namespace (str): Namespace where the resource is located
        resource_type (str): Type of resource (deployment, statefulset, replicaset)
        name (str): Name of the resource
        replicas (int): Desired number of replicas

    Returns:
        Dict[str, Any]: Information about the scaled resource

    Raises:
        RuntimeError: If there's an error accessing the Kubernetes API
    """
    try:
        api_client = k8s_client.get_api_client(context)
        apps_v1 = client.AppsV1Api(api_client)

        resource_type = resource_type.lower()

        # Validate replica count
        if replicas < 0:
            raise ValueError("Replica count cannot be negative")

        # Handle different resource types
        if resource_type == "deployment":
            # Check if the deployment exists first
            try:
                deployment = apps_v1.read_namespaced_deployment(name=name, namespace=namespace)
            except client.rest.ApiException as e:
                if e.status == 404:
                    raise RuntimeError(f"Deployment '{name}' not found in namespace '{namespace}'")
                raise

            # Create a deployment scale object
            scale = client.V1Scale(
                api_version="apps/v1",
                kind="Scale",
                metadata=client.V1ObjectMeta(name=name, namespace=namespace),
                spec=client.V1ScaleSpec(replicas=replicas),
            )

            # Apply the scale
            result = apps_v1.patch_namespaced_deployment_scale(name=name, namespace=namespace, body=scale)

            return {
                "resource_type": "deployment",
                "name": result.metadata.name,
                "namespace": result.metadata.namespace,
                "replicas": {"desired": result.spec.replicas, "current": result.status.replicas},
            }

        elif resource_type == "statefulset":
            # Check if the statefulset exists first
            try:
                statefulset = apps_v1.read_namespaced_stateful_set(name=name, namespace=namespace)
            except client.rest.ApiException as e:
                if e.status == 404:
                    raise RuntimeError(f"StatefulSet '{name}' not found in namespace '{namespace}'")
                raise

            # Create a statefulset scale object
            scale = client.V1Scale(
                api_version="apps/v1",
                kind="Scale",
                metadata=client.V1ObjectMeta(name=name, namespace=namespace),
                spec=client.V1ScaleSpec(replicas=replicas),
            )

            # Apply the scale
            result = apps_v1.patch_namespaced_stateful_set_scale(name=name, namespace=namespace, body=scale)

            return {
                "resource_type": "statefulset",
                "name": result.metadata.name,
                "namespace": result.metadata.namespace,
                "replicas": {"desired": result.spec.replicas, "current": result.status.replicas},
            }

        elif resource_type == "replicaset":
            # Check if the replicaset exists first
            try:
                replicaset = apps_v1.read_namespaced_replica_set(name=name, namespace=namespace)
            except client.rest.ApiException as e:
                if e.status == 404:
                    raise RuntimeError(f"ReplicaSet '{name}' not found in namespace '{namespace}'")
                raise

            # Create a replicaset scale object
            scale = client.V1Scale(
                api_version="apps/v1",
                kind="Scale",
                metadata=client.V1ObjectMeta(name=name, namespace=namespace),
                spec=client.V1ScaleSpec(replicas=replicas),
            )

            # Apply the scale
            result = apps_v1.patch_namespaced_replica_set_scale(name=name, namespace=namespace, body=scale)

            return {
                "resource_type": "replicaset",
                "name": result.metadata.name,
                "namespace": result.metadata.namespace,
                "replicas": {"desired": result.spec.replicas, "current": result.status.replicas},
            }
        else:
            raise ValueError(
                f"Unsupported resource type: {resource_type}. Supported types: deployment, statefulset, replicaset"
            )

    except client.rest.ApiException as e:
        raise RuntimeError(f"Failed to scale {resource_type}: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Failed to scale {resource_type}: {str(e)}")


async def k8s_autoscale_resource(
    context: str,
    namespace: str,
    resource_type: str,
    name: str,
    min_replicas: int,
    max_replicas: int,
    cpu_percent: Optional[int] = 80,
) -> Dict[str, Any]:
    """
    Configure a Horizontal Pod Autoscaler (HPA) for a deployment, statefulset, or replicaset.

    Args:
        context (str): Name of the Kubernetes context to use
        namespace (str): Namespace where the resource is located
        resource_type (str): Type of resource (deployment, statefulset, replicaset)
        name (str): Name of the resource
        min_replicas (int): Minimum number of replicas
        max_replicas (int): Maximum number of replicas
        cpu_percent (int, optional): Target CPU utilization percentage. Defaults to 80.

    Returns:
        Dict[str, Any]: Information about the created or updated HPA

    Raises:
        RuntimeError: If there's an error accessing the Kubernetes API
    """
    try:
        api_client = k8s_client.get_api_client(context)
        autoscaling_v1 = client.AutoscalingV1Api(api_client)

        resource_type = resource_type.lower()

        # Validate min and max replicas
        if min_replicas < 1:
            raise ValueError("Minimum replicas cannot be less than 1")
        if max_replicas < min_replicas:
            raise ValueError("Maximum replicas cannot be less than minimum replicas")
        if cpu_percent is not None and (cpu_percent < 1 or cpu_percent > 100):
            raise ValueError("CPU target percentage must be between 1 and 100")

        # Map resource type to API version and kind
        api_version = "apps/v1"
        kind = resource_type.capitalize()

        # Create an HPA object
        hpa_metadata = client.V1ObjectMeta(name=name, namespace=namespace)

        # Create target reference based on resource type
        target_ref = client.V1CrossVersionObjectReference(api_version=api_version, kind=kind, name=name)

        # Create HPA spec
        hpa_spec = client.V1HorizontalPodAutoscalerSpec(
            min_replicas=min_replicas,
            max_replicas=max_replicas,
            target_cpu_utilization_percentage=cpu_percent,
            scale_target_ref=target_ref,
        )

        # Create the full HPA object
        hpa = client.V1HorizontalPodAutoscaler(
            api_version="autoscaling/v1", kind="HorizontalPodAutoscaler", metadata=hpa_metadata, spec=hpa_spec
        )

        # Try to update an existing HPA first
        try:
            # Check if HPA already exists
            existing_hpa = autoscaling_v1.read_namespaced_horizontal_pod_autoscaler(name=name, namespace=namespace)

            # Update existing HPA
            result = autoscaling_v1.replace_namespaced_horizontal_pod_autoscaler(
                name=name, namespace=namespace, body=hpa
            )
            update_type = "updated"

        except client.rest.ApiException as e:
            if e.status == 404:
                # Create new HPA if it doesn't exist
                result = autoscaling_v1.create_namespaced_horizontal_pod_autoscaler(namespace=namespace, body=hpa)
                update_type = "created"
            else:
                raise

        # Format the response
        return {
            "action": update_type,
            "name": result.metadata.name,
            "namespace": result.metadata.namespace,
            "target": {
                "kind": result.spec.scale_target_ref.kind,
                "name": result.spec.scale_target_ref.name,
                "api_version": result.spec.scale_target_ref.api_version,
            },
            "min_replicas": result.spec.min_replicas,
            "max_replicas": result.spec.max_replicas,
            "current_replicas": result.status.current_replicas,
            "target_cpu_percentage": result.spec.target_cpu_utilization_percentage,
        }

    except client.rest.ApiException as e:
        raise RuntimeError(f"Failed to configure autoscaler: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Failed to configure autoscaler: {str(e)}")


async def k8s_update_resources(
    context: str,
    namespace: str,
    resource_type: str,
    name: str,
    container: str,
    memory_request: Optional[str] = None,
    memory_limit: Optional[str] = None,
    cpu_request: Optional[str] = None,
    cpu_limit: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update resource requests and limits for a container in a deployment, statefulset, or daemonset.

    Args:
        context (str): Name of the Kubernetes context to use
        namespace (str): Namespace where the resource is located
        resource_type (str): Type of resource (deployment, statefulset, daemonset)
        name (str): Name of the resource
        container (str): Name of the container to update
        memory_request (str, optional): Memory request (e.g. "64Mi", "128Mi", "1Gi")
        memory_limit (str, optional): Memory limit (e.g. "128Mi", "256Mi", "2Gi")
        cpu_request (str, optional): CPU request (e.g. "100m", "0.5", "1")
        cpu_limit (str, optional): CPU limit (e.g. "200m", "1", "2")

    Returns:
        Dict[str, Any]: Information about the updated resource

    Raises:
        RuntimeError: If there's an error accessing the Kubernetes API
    """
    try:
        api_client = k8s_client.get_api_client(context)
        apps_v1 = client.AppsV1Api(api_client)

        resource_type = resource_type.lower()

        # Validate at least one resource parameter is provided
        if not any([memory_request, memory_limit, cpu_request, cpu_limit]):
            raise ValueError("At least one resource limit or request must be specified")

        # Get the current resource based on type
        if resource_type == "deployment":
            current_resource = apps_v1.read_namespaced_deployment(name=name, namespace=namespace)
        elif resource_type == "statefulset":
            current_resource = apps_v1.read_namespaced_stateful_set(name=name, namespace=namespace)
        elif resource_type == "daemonset":
            current_resource = apps_v1.read_namespaced_daemon_set(name=name, namespace=namespace)
        else:
            raise ValueError(
                f"Unsupported resource type: {resource_type}. Supported types: deployment, statefulset, daemonset"
            )

        # Find the specified container and update its resources
        container_found = False
        for c in current_resource.spec.template.spec.containers:
            if c.name == container:
                container_found = True

                # Create resources object if it doesn't exist
                if not hasattr(c, "resources") or c.resources is None:
                    c.resources = client.V1ResourceRequirements(requests={}, limits={})

                # Update resource requests
                if not hasattr(c.resources, "requests") or c.resources.requests is None:
                    c.resources.requests = {}

                if memory_request:
                    c.resources.requests["memory"] = memory_request
                if cpu_request:
                    c.resources.requests["cpu"] = cpu_request

                # Update resource limits
                if not hasattr(c.resources, "limits") or c.resources.limits is None:
                    c.resources.limits = {}

                if memory_limit:
                    c.resources.limits["memory"] = memory_limit
                if cpu_limit:
                    c.resources.limits["cpu"] = cpu_limit

                break

        if not container_found:
            raise ValueError(f"Container '{container}' not found in {resource_type} '{name}'")

        # Update the resource with the modified container
        if resource_type == "deployment":
            result = apps_v1.patch_namespaced_deployment(name=name, namespace=namespace, body=current_resource)
        elif resource_type == "statefulset":
            result = apps_v1.patch_namespaced_stateful_set(name=name, namespace=namespace, body=current_resource)
        elif resource_type == "daemonset":
            result = apps_v1.patch_namespaced_daemon_set(name=name, namespace=namespace, body=current_resource)

        # Return information about the updated resource
        return {
            "resource_type": resource_type,
            "name": result.metadata.name,
            "namespace": result.metadata.namespace,
            "container": container,
            "resources": {
                "requests": {"memory": memory_request or "unchanged", "cpu": cpu_request or "unchanged"},
                "limits": {"memory": memory_limit or "unchanged", "cpu": cpu_limit or "unchanged"},
            },
            "message": f"Resource {resource_type}/{name} container {container} updated with new resource constraints",
        }

    except client.rest.ApiException as e:
        if e.status == 404:
            raise RuntimeError(f"{resource_type.capitalize()} '{name}' not found in namespace '{namespace}'")
        raise RuntimeError(f"Failed to update resources: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Failed to update resources: {str(e)}")
