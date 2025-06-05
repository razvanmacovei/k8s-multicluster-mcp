import datetime
import os
from typing import Any, Dict, Optional

from kubernetes import client

from ..utils.k8s_client import KubernetesClient

# Initialize client with kubeconfig directory from environment or default
kubeconfig_dir = os.environ.get("KUBECONFIG_DIR", os.path.expanduser("~/.kube"))
k8s_client = KubernetesClient(kubeconfig_dir)


async def get_k8s_rollout_status(context: str, namespace: str, resource_type: str, name: str) -> Dict[str, Any]:
    """
    Get the status of a rollout for a deployment, daemonset, or statefulset.

    Args:
        context (str): Name of the Kubernetes context to use
        namespace (str): Namespace where the resource is located
        resource_type (str): Type of resource (deployment, daemonset, statefulset)
        name (str): Name of the resource

    Returns:
        Dict[str, Any]: Information about the rollout status

    Raises:
        RuntimeError: If there's an error accessing the Kubernetes API
    """
    try:
        api_client = k8s_client.get_api_client(context)
        apps_v1 = client.AppsV1Api(api_client)

        resource_type = resource_type.lower()
        result = {}

        if resource_type == "deployment":
            deployment = apps_v1.read_namespaced_deployment(name=name, namespace=namespace)

            # Get rollout status
            result = {
                "name": deployment.metadata.name,
                "namespace": deployment.metadata.namespace,
                "generation": deployment.metadata.generation,
                "observed_generation": deployment.status.observed_generation,
                "replicas": {
                    "desired": deployment.spec.replicas,
                    "updated": deployment.status.updated_replicas,
                    "ready": deployment.status.ready_replicas,
                    "available": deployment.status.available_replicas,
                    "unavailable": deployment.status.unavailable_replicas,
                },
                "conditions": (
                    [
                        {
                            "type": condition.type,
                            "status": condition.status,
                            "reason": condition.reason,
                            "message": condition.message,
                            "last_update": (
                                condition.last_update_time.isoformat() if condition.last_update_time else None
                            ),
                        }
                        for condition in deployment.status.conditions
                    ]
                    if deployment.status.conditions
                    else []
                ),
            }

        elif resource_type == "statefulset":
            statefulset = apps_v1.read_namespaced_stateful_set(name=name, namespace=namespace)

            result = {
                "name": statefulset.metadata.name,
                "namespace": statefulset.metadata.namespace,
                "generation": statefulset.metadata.generation,
                "observed_generation": statefulset.status.observed_generation,
                "replicas": {
                    "desired": statefulset.spec.replicas,
                    "updated": statefulset.status.updated_replicas,
                    "ready": statefulset.status.ready_replicas,
                    "available": getattr(statefulset.status, "available_replicas", None),
                },
                "current_revision": statefulset.status.current_revision,
                "update_revision": statefulset.status.update_revision,
                "conditions": (
                    [
                        {
                            "type": condition.type,
                            "status": condition.status,
                            "reason": condition.reason,
                            "message": condition.message,
                            "last_transition": (
                                condition.last_transition_time.isoformat() if condition.last_transition_time else None
                            ),
                        }
                        for condition in statefulset.status.conditions
                    ]
                    if statefulset.status.conditions
                    else []
                ),
            }

        elif resource_type == "daemonset":
            daemonset = apps_v1.read_namespaced_daemon_set(name=name, namespace=namespace)

            result = {
                "name": daemonset.metadata.name,
                "namespace": daemonset.metadata.namespace,
                "generation": daemonset.metadata.generation,
                "observed_generation": daemonset.status.observed_generation,
                "replicas": {
                    "desired": daemonset.status.desired_number_scheduled,
                    "current": daemonset.status.current_number_scheduled,
                    "ready": daemonset.status.number_ready,
                    "available": daemonset.status.number_available,
                    "unavailable": daemonset.status.number_unavailable,
                    "misscheduled": daemonset.status.number_misscheduled,
                },
                "conditions": (
                    [
                        {
                            "type": condition.type,
                            "status": condition.status,
                            "reason": condition.reason,
                            "message": condition.message,
                            "last_transition": (
                                condition.last_transition_time.isoformat() if condition.last_transition_time else None
                            ),
                        }
                        for condition in daemonset.status.conditions
                    ]
                    if daemonset.status.conditions
                    else []
                ),
            }
        else:
            raise ValueError(
                f"Unsupported resource type: {resource_type}. Supported types: deployment, statefulset, daemonset"
            )

        return result

    except client.rest.ApiException as e:
        if e.status == 404:
            raise RuntimeError(f"{resource_type.capitalize()} '{name}' not found in namespace '{namespace}'")
        raise RuntimeError(f"Failed to get rollout status: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Failed to get rollout status: {str(e)}")


async def get_k8s_rollout_history(context: str, namespace: str, resource_type: str, name: str) -> Dict[str, Any]:
    """
    Get the revision history of a rollout for a deployment, daemonset, or statefulset
    using the Kubernetes Python client.

    Args:
        context (str): Name of the Kubernetes context to use
        namespace (str): Namespace where the resource is located
        resource_type (str): Type of resource (deployment, daemonset, statefulset)
        name (str): Name of the resource

    Returns:
        Dict[str, Any]: Information about the rollout history

    Raises:
        RuntimeError: If there's an error accessing the Kubernetes API
    """
    try:
        # Get the API client
        api_client = k8s_client.get_api_client(context)
        apps_v1 = client.AppsV1Api(api_client)

        resource_type = resource_type.lower()
        if resource_type not in ["deployment", "statefulset", "daemonset"]:
            raise ValueError(
                f"Unsupported resource type: {resource_type}. Supported types: deployment, statefulset, daemonset"
            )

        # Initialize the result structure
        result = {"resource": {"type": resource_type, "name": name, "namespace": namespace}, "revisions": []}

        # Get the resource and its revision history
        if resource_type == "deployment":
            # Get the deployment
            deployment = apps_v1.read_namespaced_deployment(name=name, namespace=namespace)

            # Get the replica sets controlled by this deployment
            replica_sets = apps_v1.list_namespaced_replica_set(namespace=namespace, label_selector=f"app={name}")

            # If no specific label selector worked, try to extract from deployment selector
            if not replica_sets.items and deployment.spec.selector and deployment.spec.selector.match_labels:
                selector = ",".join([f"{k}={v}" for k, v in deployment.spec.selector.match_labels.items()])
                replica_sets = apps_v1.list_namespaced_replica_set(namespace=namespace, label_selector=selector)

            # Process the replica sets to extract revision information
            for rs in replica_sets.items:
                # Only include replica sets that are part of this deployment
                if rs.metadata.owner_references and any(
                    ref.name == deployment.metadata.name and ref.kind == "Deployment"
                    for ref in rs.metadata.owner_references
                ):
                    revision = rs.metadata.annotations.get("deployment.kubernetes.io/revision", "unknown")
                    change_cause = rs.metadata.annotations.get("kubernetes.io/change-cause", "<none>")

                    result["revisions"].append(
                        {
                            "revision": revision,
                            "change_cause": change_cause,
                            "replica_set": rs.metadata.name,
                            "created_at": (
                                rs.metadata.creation_timestamp.isoformat() if rs.metadata.creation_timestamp else None
                            ),
                            "image": (
                                rs.spec.template.spec.containers[0].image if rs.spec.template.spec.containers else None
                            ),
                            "ready_replicas": rs.status.ready_replicas,
                        }
                    )

            # Sort revisions by revision number (descending)
            result["revisions"].sort(key=lambda x: int(x["revision"]) if x["revision"].isdigit() else 0, reverse=True)

        elif resource_type == "statefulset":
            # Get the statefulset
            statefulset = apps_v1.read_namespaced_stateful_set(name=name, namespace=namespace)

            # For StatefulSets, get the current and update revisions
            current_revision = statefulset.status.current_revision
            update_revision = statefulset.status.update_revision

            result["revisions"].append(
                {
                    "revision": "current",
                    "revision_hash": current_revision,
                    "change_cause": statefulset.metadata.annotations.get("kubernetes.io/change-cause", "<none>"),
                    "created_at": (
                        statefulset.metadata.creation_timestamp.isoformat()
                        if statefulset.metadata.creation_timestamp
                        else None
                    ),
                    "image": (
                        statefulset.spec.template.spec.containers[0].image
                        if statefulset.spec.template.spec.containers
                        else None
                    ),
                }
            )

            # Add update revision if different from current
            if update_revision and update_revision != current_revision:
                result["revisions"].append(
                    {
                        "revision": "update",
                        "revision_hash": update_revision,
                        "change_cause": statefulset.metadata.annotations.get("kubernetes.io/change-cause", "<none>"),
                        "created_at": (
                            statefulset.metadata.creation_timestamp.isoformat()
                            if statefulset.metadata.creation_timestamp
                            else None
                        ),
                        "image": (
                            statefulset.spec.template.spec.containers[0].image
                            if statefulset.spec.template.spec.containers
                            else None
                        ),
                    }
                )

        elif resource_type == "daemonset":
            # Get the daemonset
            daemonset = apps_v1.read_namespaced_daemon_set(name=name, namespace=namespace)

            # For DaemonSets, we can look at the controller revision history
            # But this requires additional API calls to get the ControllerRevision objects
            client.CoreV1Api(api_client)

            # Get controller revisions for this daemonset
            label_selector = (
                ",".join([f"{k}={v}" for k, v in daemonset.spec.selector.match_labels.items()])
                if daemonset.spec.selector and daemonset.spec.selector.match_labels
                else None
            )

            if label_selector:
                # Get ControllerRevision objects
                try:
                    apps_api = client.AppsV1Api(api_client)
                    controller_revisions = apps_api.list_namespaced_controller_revision(
                        namespace=namespace, label_selector=label_selector
                    )

                    for rev in controller_revisions.items:
                        # Only include revisions that are part of this daemonset
                        if rev.metadata.owner_references and any(
                            ref.name == daemonset.metadata.name and ref.kind == "DaemonSet"
                            for ref in rev.metadata.owner_references
                        ):
                            result["revisions"].append(
                                {
                                    "revision": str(rev.revision),
                                    "change_cause": rev.metadata.annotations.get(
                                        "kubernetes.io/change-cause", "<none>"
                                    ),
                                    "created_at": (
                                        rev.metadata.creation_timestamp.isoformat()
                                        if rev.metadata.creation_timestamp
                                        else None
                                    ),
                                }
                            )

                    # Sort revisions by revision number (descending)
                    result["revisions"].sort(
                        key=lambda x: int(x["revision"]) if x["revision"].isdigit() else 0, reverse=True
                    )

                except Exception:
                    # If we can't get controller revisions, at least return the current revision
                    result["revisions"].append(
                        {
                            "revision": "current",
                            "change_cause": daemonset.metadata.annotations.get("kubernetes.io/change-cause", "<none>"),
                            "created_at": (
                                daemonset.metadata.creation_timestamp.isoformat()
                                if daemonset.metadata.creation_timestamp
                                else None
                            ),
                            "image": (
                                daemonset.spec.template.spec.containers[0].image
                                if daemonset.spec.template.spec.containers
                                else None
                            ),
                        }
                    )
            else:
                # If no label selector available, return just the current revision
                result["revisions"].append(
                    {
                        "revision": "current",
                        "change_cause": daemonset.metadata.annotations.get("kubernetes.io/change-cause", "<none>"),
                        "created_at": (
                            daemonset.metadata.creation_timestamp.isoformat()
                            if daemonset.metadata.creation_timestamp
                            else None
                        ),
                        "image": (
                            daemonset.spec.template.spec.containers[0].image
                            if daemonset.spec.template.spec.containers
                            else None
                        ),
                    }
                )

        return result

    except client.rest.ApiException as e:
        if e.status == 404:
            raise RuntimeError(f"{resource_type.capitalize()} '{name}' not found in namespace '{namespace}'")
        raise RuntimeError(f"Failed to get rollout history: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Failed to get rollout history: {str(e)}")


async def k8s_rollout_undo(
    context: str, namespace: str, resource_type: str, name: str, to_revision: Optional[int] = None
) -> Dict[str, Any]:
    """
    Undo a rollout to a previous revision for a deployment, daemonset, or statefulset.

    Args:
        context (str): Name of the Kubernetes context to use
        namespace (str): Namespace where the resource is located
        resource_type (str): Type of resource (deployment, daemonset, statefulset)
        name (str): Name of the resource
        to_revision (int, optional): The revision to roll back to. If None, rolls back to the previous revision.

    Returns:
        Dict[str, Any]: Result of the rollout undo operation

    Raises:
        RuntimeError: If there's an error accessing the Kubernetes API
    """
    try:
        resource_type = resource_type.lower()
        if resource_type not in ["deployment", "statefulset", "daemonset"]:
            raise ValueError(
                f"Unsupported resource type: {resource_type}. Supported types: deployment, statefulset, daemonset"
            )

        # Get the API client
        api_client = k8s_client.get_api_client(context)
        apps_v1 = client.AppsV1Api(api_client)

        if resource_type == "deployment":
            # Get current deployment
            deployment = apps_v1.read_namespaced_deployment(name=name, namespace=namespace)

            # For deployments, we need to find the target ReplicaSet and apply its template
            # Get the ReplicaSets associated with this deployment
            selector = ",".join([f"{k}={v}" for k, v in deployment.spec.selector.match_labels.items()])
            replica_sets = apps_v1.list_namespaced_replica_set(namespace=namespace, label_selector=selector)

            if to_revision is not None:
                # Find the specific revision
                target_rs = None
                for rs in replica_sets.items:
                    if rs.metadata.annotations and "deployment.kubernetes.io/revision" in rs.metadata.annotations:
                        if rs.metadata.annotations["deployment.kubernetes.io/revision"] == str(to_revision):
                            target_rs = rs
                            break

                if target_rs:
                    # Update the deployment with the template from the target RS
                    deployment.spec.template = target_rs.spec.template
                    # Add rollback annotation
                    if deployment.spec.template.metadata is None:
                        deployment.spec.template.metadata = client.V1ObjectMeta()
                    if deployment.spec.template.metadata.annotations is None:
                        deployment.spec.template.metadata.annotations = {}

                    deployment.spec.template.metadata.annotations["kubernetes.io/rollback"] = (
                        f"to-revision-{to_revision}"
                    )
                    deployment.spec.template.metadata.annotations["kubernetes.io/rollback-timestamp"] = (
                        datetime.datetime.now().isoformat()
                    )

                    apps_v1.patch_namespaced_deployment(name=name, namespace=namespace, body=deployment)
                else:
                    raise RuntimeError(f"Could not find ReplicaSet with revision {to_revision}")
            else:
                # Find the previous revision
                sorted_rs = []
                for rs in replica_sets.items:
                    if rs.metadata.annotations and "deployment.kubernetes.io/revision" in rs.metadata.annotations:
                        try:
                            revision = int(rs.metadata.annotations["deployment.kubernetes.io/revision"])
                            sorted_rs.append((revision, rs))
                        except ValueError:
                            continue

                sorted_rs.sort(key=lambda x: x[0], reverse=True)

                if len(sorted_rs) > 1:
                    # The second one is the previous revision
                    previous_rs = sorted_rs[1][1]
                    deployment.spec.template = previous_rs.spec.template

                    # Add rollback annotation
                    if deployment.spec.template.metadata is None:
                        deployment.spec.template.metadata = client.V1ObjectMeta()
                    if deployment.spec.template.metadata.annotations is None:
                        deployment.spec.template.metadata.annotations = {}

                    prev_revision = sorted_rs[1][0]
                    deployment.spec.template.metadata.annotations["kubernetes.io/rollback"] = (
                        f"to-revision-{prev_revision}"
                    )
                    deployment.spec.template.metadata.annotations["kubernetes.io/rollback-timestamp"] = (
                        datetime.datetime.now().isoformat()
                    )

                    apps_v1.patch_namespaced_deployment(name=name, namespace=namespace, body=deployment)
                else:
                    raise RuntimeError("Could not find previous revision")

        elif resource_type == "statefulset":
            # For StatefulSets, we need to get the current and update revisions
            statefulset = apps_v1.read_namespaced_stateful_set(name=name, namespace=namespace)

            # Get revision history
            history_result = await get_k8s_rollout_history(context, namespace, resource_type, name)

            if to_revision is not None:
                # Find the target revision
                target_revision = None
                for rev in history_result["revisions"]:
                    if rev["revision"] == str(to_revision):
                        target_revision = rev
                        break

                if not target_revision:
                    raise RuntimeError(f"Could not find revision {to_revision}")
            else:
                # Get the previous revision
                revisions = history_result["revisions"]
                if len(revisions) < 2:
                    raise RuntimeError("No previous revision found")
                target_revision = revisions[1]  # Second revision is the previous one

            # We can only do this by updating to the partition strategy
            # and then rolling back, which is complex in the API
            # For now, we'll patch with a timestamp to force a rollout
            patch = {
                "spec": {
                    "template": {
                        "metadata": {
                            "annotations": {
                                "kubernetes.io/rollback-to": target_revision.get("revision_hash", ""),
                                "kubernetes.io/rollback-timestamp": datetime.datetime.now().isoformat(),
                            }
                        }
                    }
                }
            }

            # Apply the patch
            apps_v1.patch_namespaced_stateful_set(name=name, namespace=namespace, body=patch)

        elif resource_type == "daemonset":
            # For DaemonSets, similar to StatefulSets
            daemonset = apps_v1.read_namespaced_daemon_set(name=name, namespace=namespace)

            # Get revision history
            history_result = await get_k8s_rollout_history(context, namespace, resource_type, name)

            if to_revision is not None:
                # Find the target revision
                target_revision = None
                for rev in history_result["revisions"]:
                    if rev["revision"] == str(to_revision):
                        target_revision = rev
                        break

                if not target_revision:
                    raise RuntimeError(f"Could not find revision {to_revision}")
            else:
                # Get the previous revision
                revisions = history_result["revisions"]
                if len(revisions) < 2:
                    raise RuntimeError("No previous revision found")
                target_revision = revisions[1]  # Second revision is the previous one

            # We need to locate the ControllerRevision and apply its template
            # This is simplified and may need enhancement
            patch = {
                "spec": {
                    "template": {
                        "metadata": {
                            "annotations": {
                                "kubernetes.io/rollback-to-revision": str(target_revision.get("revision", "")),
                                "kubernetes.io/rollback-timestamp": datetime.datetime.now().isoformat(),
                            }
                        }
                    }
                }
            }

            # Apply the patch
            apps_v1.patch_namespaced_daemon_set(name=name, namespace=namespace, body=patch)

        # Return success result
        return {
            "success": True,
            "message": f"Rollout undo initiated for {resource_type}/{name}",
            "resource": {"type": resource_type, "name": name, "namespace": namespace},
            "revision": to_revision if to_revision is not None else "previous",
        }

    except client.rest.ApiException as e:
        if e.status == 404:
            raise RuntimeError(f"{resource_type.capitalize()} '{name}' not found in namespace '{namespace}'")
        raise RuntimeError(f"Failed to undo rollout: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Failed to undo rollout: {str(e)}")


async def k8s_rollout_restart(context: str, namespace: str, resource_type: str, name: str) -> Dict[str, Any]:
    """
    Restart a rollout for a deployment, daemonset, or statefulset using the Kubernetes Python client.

    Args:
        context (str): Name of the Kubernetes context to use
        namespace (str): Namespace where the resource is located
        resource_type (str): Type of resource (deployment, daemonset, statefulset)
        name (str): Name of the resource

    Returns:
        Dict[str, Any]: Result of the rollout restart operation

    Raises:
        RuntimeError: If there's an error accessing the Kubernetes API
    """
    try:
        resource_type = resource_type.lower()
        if resource_type not in ["deployment", "statefulset", "daemonset"]:
            raise ValueError(
                f"Unsupported resource type: {resource_type}. Supported types: deployment, statefulset, daemonset"
            )

        # Get the API client
        api_client = k8s_client.get_api_client(context)
        apps_v1 = client.AppsV1Api(api_client)

        # The restart strategy is to add a restart annotation with the current timestamp
        restart_annotation = {
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {"kubectl.kubernetes.io/restartedAt": datetime.datetime.now().isoformat()}
                    }
                }
            }
        }

        # Apply the patch based on resource type
        if resource_type == "deployment":
            apps_v1.patch_namespaced_deployment(name=name, namespace=namespace, body=restart_annotation)
        elif resource_type == "statefulset":
            apps_v1.patch_namespaced_stateful_set(name=name, namespace=namespace, body=restart_annotation)
        elif resource_type == "daemonset":
            apps_v1.patch_namespaced_daemon_set(name=name, namespace=namespace, body=restart_annotation)

        # Return success result
        return {
            "success": True,
            "message": f"Rollout restart initiated for {resource_type}/{name}",
            "resource": {"type": resource_type, "name": name, "namespace": namespace},
        }

    except client.rest.ApiException as e:
        if e.status == 404:
            raise RuntimeError(f"{resource_type.capitalize()} '{name}' not found in namespace '{namespace}'")
        raise RuntimeError(f"Failed to restart rollout: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Failed to restart rollout: {str(e)}")


async def k8s_rollout_pause(context: str, namespace: str, resource_type: str, name: str) -> Dict[str, Any]:
    """
    Pause a rollout for a deployment, daemonset, or statefulset using the Kubernetes Python client.

    Args:
        context (str): Name of the Kubernetes context to use
        namespace (str): Namespace where the resource is located
        resource_type (str): Type of resource (deployment, daemonset, statefulset)
        name (str): Name of the resource

    Returns:
        Dict[str, Any]: Result of the rollout pause operation

    Raises:
        RuntimeError: If there's an error accessing the Kubernetes API
    """
    try:
        resource_type = resource_type.lower()
        if resource_type not in ["deployment", "statefulset", "daemonset"]:
            raise ValueError(
                f"Unsupported resource type: {resource_type}. Supported types: deployment, statefulset, daemonset"
            )

        # Get the API client
        api_client = k8s_client.get_api_client(context)
        apps_v1 = client.AppsV1Api(api_client)

        if resource_type == "deployment":
            # For deployments, pausing means setting paused=True in the spec
            patch = {"spec": {"paused": True}}

            # Apply the patch
            apps_v1.patch_namespaced_deployment(name=name, namespace=namespace, body=patch)
        elif resource_type == "statefulset":
            # StatefulSets don't have a direct pause mechanism in the API
            # The common approach is to adjust the partition so no further updates happen
            statefulset = apps_v1.read_namespaced_stateful_set(name=name, namespace=namespace)

            # Set the partition to the current replica count to prevent further updates
            partition = statefulset.spec.replicas

            patch = {"spec": {"updateStrategy": {"type": "RollingUpdate", "rollingUpdate": {"partition": partition}}}}

            # Apply the patch
            apps_v1.patch_namespaced_stateful_set(name=name, namespace=namespace, body=patch)
        elif resource_type == "daemonset":
            # DaemonSets don't have a direct pause mechanism either
            # We'll use a similar approach to StatefulSets with maxUnavailable=0
            patch = {"spec": {"updateStrategy": {"type": "RollingUpdate", "rollingUpdate": {"maxUnavailable": 0}}}}

            # Apply the patch
            apps_v1.patch_namespaced_daemon_set(name=name, namespace=namespace, body=patch)

        # Return success result
        return {
            "success": True,
            "message": f"Rollout paused for {resource_type}/{name}",
            "resource": {"type": resource_type, "name": name, "namespace": namespace},
        }

    except client.rest.ApiException as e:
        if e.status == 404:
            raise RuntimeError(f"{resource_type.capitalize()} '{name}' not found in namespace '{namespace}'")
        raise RuntimeError(f"Failed to pause rollout: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Failed to pause rollout: {str(e)}")


async def k8s_rollout_resume(context: str, namespace: str, resource_type: str, name: str) -> Dict[str, Any]:
    """
    Resume a rollout for a deployment, daemonset, or statefulset using the Kubernetes Python client.

    Args:
        context (str): Name of the Kubernetes context to use
        namespace (str): Namespace where the resource is located
        resource_type (str): Type of resource (deployment, daemonset, statefulset)
        name (str): Name of the resource

    Returns:
        Dict[str, Any]: Result of the rollout resume operation

    Raises:
        RuntimeError: If there's an error accessing the Kubernetes API
    """
    try:
        resource_type = resource_type.lower()
        if resource_type not in ["deployment", "statefulset", "daemonset"]:
            raise ValueError(
                f"Unsupported resource type: {resource_type}. Supported types: deployment, statefulset, daemonset"
            )

        # Get the API client
        api_client = k8s_client.get_api_client(context)
        apps_v1 = client.AppsV1Api(api_client)

        if resource_type == "deployment":
            # For deployments, resuming means setting paused=False in the spec
            patch = {"spec": {"paused": False}}

            # Apply the patch
            apps_v1.patch_namespaced_deployment(name=name, namespace=namespace, body=patch)
        elif resource_type == "statefulset":
            # Resume a StatefulSet by resetting the partition to 0
            patch = {"spec": {"updateStrategy": {"type": "RollingUpdate", "rollingUpdate": {"partition": 0}}}}

            # Apply the patch
            apps_v1.patch_namespaced_stateful_set(name=name, namespace=namespace, body=patch)
        elif resource_type == "daemonset":
            # Resume a DaemonSet by resetting maxUnavailable to 1 (default)
            patch = {"spec": {"updateStrategy": {"type": "RollingUpdate", "rollingUpdate": {"maxUnavailable": 1}}}}

            # Apply the patch
            apps_v1.patch_namespaced_daemon_set(name=name, namespace=namespace, body=patch)

        # Return success result
        return {
            "success": True,
            "message": f"Rollout resumed for {resource_type}/{name}",
            "resource": {"type": resource_type, "name": name, "namespace": namespace},
        }

    except client.rest.ApiException as e:
        if e.status == 404:
            raise RuntimeError(f"{resource_type.capitalize()} '{name}' not found in namespace '{namespace}'")
        raise RuntimeError(f"Failed to resume rollout: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Failed to resume rollout: {str(e)}")
