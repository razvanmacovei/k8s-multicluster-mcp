#!/usr/bin/env python3
"""Multi-Cluster Kubernetes MCP Server.

Provides a standardized MCP (Model Context Protocol) interface to interact
with multiple Kubernetes clusters simultaneously through kubeconfig files.
"""
from typing import Dict, List, Optional
from mcp.server.fastmcp import FastMCP
import os

# Create MCP server
mcp = FastMCP("KubernetesMCP")

# --- Import tool implementations ---

# Core cluster operations
from src.tools.contexts import list_k8s_contexts as contexts_list
from src.tools.namespaces import list_k8s_namespaces as namespaces_list
from src.tools.nodes import list_k8s_nodes as nodes_list
from src.tools.pods import list_k8s_resources as resources_list, get_k8s_pod_logs as pod_logs_get
from src.tools.events import list_k8s_events as events_list
from src.tools.resources import get_k8s_resource as resource_get
from src.tools.describe import describe_k8s_resource as resource_describe
from src.tools.api_discovery import list_k8s_apis as apis_list, list_k8s_crds as crds_list

# Metrics and monitoring
from src.tools.metrics import top_k8s_nodes as nodes_top, top_k8s_pods as pods_top
from src.tools.diagnosis import diagnose_k8s_application as application_diagnose
from src.tools.cluster_health import k8s_cluster_health as cluster_health_check

# Rollout management
from src.tools.rollouts import (
    get_k8s_rollout_status as rollout_status_get,
    get_k8s_rollout_history as rollout_history_get,
    k8s_rollout_undo as rollout_undo,
    k8s_rollout_restart as rollout_restart,
    k8s_rollout_pause as rollout_pause,
    k8s_rollout_resume as rollout_resume,
)

# Scaling
from src.tools.scaling import (
    k8s_scale_resource as resource_scale,
    k8s_autoscale_resource as resource_autoscale,
    k8s_update_resources as resource_update_resources,
)

# Resource CRUD
from src.tools.resource_management import (
    k8s_create,
    k8s_apply,
    k8s_patch,
    k8s_label,
    k8s_annotate,
)
from src.tools.delete_resource import k8s_delete

# Workload management
from src.tools.workload_management import k8s_expose, k8s_run, k8s_set_resources

# Node management
from src.tools.node_management import (
    k8s_cordon,
    k8s_uncordon,
    k8s_drain,
    k8s_taint,
    k8s_untaint,
)

# Pod operations
from src.tools.pod_operations import k8s_exec_command

# Namespace management
from src.tools.namespace_management import k8s_create_namespace, k8s_delete_namespace

# Secrets and ConfigMaps
from src.tools.secret_configmap import (
    k8s_list_secrets,
    k8s_get_secret,
    k8s_create_secret,
    k8s_list_configmaps,
    k8s_get_configmap,
    k8s_create_configmap,
)

# RBAC
from src.tools.rbac import (
    k8s_list_roles,
    k8s_list_clusterroles,
    k8s_list_rolebindings,
    k8s_list_clusterrolebindings,
    k8s_list_service_accounts,
)

# Storage and networking
from src.tools.storage_network import (
    k8s_list_pvcs,
    k8s_list_pvs,
    k8s_list_storage_classes,
    k8s_list_network_policies,
)

# Job management
from src.tools.job_management import k8s_list_jobs, k8s_list_cronjobs


# ========================================================================
# CLUSTER & CONTEXT MANAGEMENT
# ========================================================================

@mcp.tool()
async def k8s_get_contexts():
    """List all available Kubernetes contexts from all kubeconfig files.
    Returns context names that can be used with other tools.
    Supports partial context name matching in all other commands."""
    return await contexts_list()


@mcp.tool()
async def k8s_get_namespaces(context: str):
    """List all namespaces in a Kubernetes cluster.
    Use this to discover available namespaces before querying resources."""
    return await namespaces_list(context)


@mcp.tool()
async def k8s_create_ns(context: str, name: str,
                        labels: Optional[Dict] = None,
                        annotations: Optional[Dict] = None):
    """Create a new Kubernetes namespace.
    Optionally attach labels and annotations at creation time."""
    return await k8s_create_namespace(context, name, labels, annotations)


@mcp.tool()
async def k8s_delete_ns(context: str, name: str):
    """Delete a Kubernetes namespace and all resources within it.
    Protected namespaces (default, kube-system, kube-public, kube-node-lease) cannot be deleted."""
    return await k8s_delete_namespace(context, name)


@mcp.tool()
async def k8s_get_nodes(context: str):
    """List all nodes in a Kubernetes cluster with status, roles, capacity, and version info."""
    return await nodes_list(context)


@mcp.tool()
async def k8s_cluster_info(context: str):
    """Get a comprehensive health summary of the entire Kubernetes cluster.
    Checks node status, pod health across all namespaces, deployment availability,
    resource pressure, and recent warning events. Returns an overall health status
    (healthy/degraded/unhealthy) with detailed breakdowns."""
    return await cluster_health_check(context)


# ========================================================================
# RESOURCE DISCOVERY & INSPECTION
# ========================================================================

@mcp.tool()
async def k8s_get_resources(context: str, kind: str, namespace: Optional[str] = None,
                           group: Optional[str] = None, version: Optional[str] = None):
    """List Kubernetes resources of a specified kind (e.g., Pod, Deployment, Service, Ingress).
    Common kinds auto-detect their API group. For custom resources, specify group and version.
    Omit namespace to query across all namespaces."""
    return await resources_list(context, kind, namespace, group, version)


@mcp.tool()
async def k8s_get_resource(context: str, namespace: str, kind: str, name: str,
                          group: Optional[str] = None, version: Optional[str] = None):
    """Get the complete definition of a single Kubernetes resource.
    Returns the full resource spec, status, and metadata as a dictionary."""
    return await resource_get(context, namespace, kind, name, group, version)


@mcp.tool()
async def k8s_get_pod_logs(context: str, namespace: str, pod: str,
                          previousContainer: bool = False,
                          sinceDuration: Optional[str] = None):
    """Get logs from a Kubernetes pod. For multi-container pods, logs from the first container
    are returned by default. Use sinceDuration to filter (e.g., '5m', '1h', '2d').
    Set previousContainer=True to get logs from the previously terminated container."""
    return await pod_logs_get(context, namespace, pod, previousContainer, sinceDuration)


@mcp.tool()
async def k8s_get_events(context: str, namespace: str, limit: int = 100):
    """List Kubernetes events in a namespace, sorted by most recent first.
    Events show scheduling decisions, image pulls, container crashes, and other cluster activity."""
    return await events_list(context, namespace, limit)


@mcp.tool()
async def k8s_describe(context: str, resource_type: str, name: Optional[str] = None,
                      namespace: Optional[str] = None, selector: Optional[str] = None,
                      all_namespaces: bool = False):
    """Show detailed information about a resource, similar to 'kubectl describe'.
    Can describe a single resource by name, or multiple resources using a label selector.
    Set all_namespaces=True to search across all namespaces."""
    return await resource_describe(context, resource_type, name, namespace, selector, all_namespaces)


@mcp.tool()
async def k8s_apis(context: str):
    """List all available API groups and resources in the Kubernetes cluster.
    Useful for discovering what resource types are available, including CRD-based APIs."""
    return await apis_list(context)


@mcp.tool()
async def k8s_crds(context: str):
    """List all Custom Resource Definitions (CRDs) installed in the cluster.
    Shows CRD names, groups, versions, scope, and status conditions."""
    return await crds_list(context)


# ========================================================================
# METRICS & MONITORING
# ========================================================================

@mcp.tool()
async def k8s_top_nodes(context: str):
    """Display CPU and memory usage of all nodes in the cluster.
    Requires metrics-server to be installed. Shows usage alongside capacity."""
    return await nodes_top(context)


@mcp.tool()
async def k8s_top_pods(context: str, namespace: Optional[str] = None):
    """Display CPU and memory usage of pods, broken down by container.
    Requires metrics-server to be installed. Omit namespace for all namespaces."""
    return await pods_top(context, namespace)


@mcp.tool()
async def k8s_diagnose_application(context: str, namespace: str, app_name: str,
                                   resource_type: str = "deployment"):
    """Diagnose issues with a Kubernetes application by checking resource status, pod health,
    events, and container logs. Automatically detects common problems like CrashLoopBackOff,
    OOMKilled, ImagePullBackOff, permission errors, and connection issues.
    Returns a structured report with issues, severity, and recommendations."""
    return await application_diagnose(context, namespace, app_name, resource_type)


# ========================================================================
# ROLLOUT MANAGEMENT
# ========================================================================

@mcp.tool()
async def k8s_rollout_status(context: str, namespace: str, resource_type: str, name: str):
    """Get the rollout status of a deployment, daemonset, or statefulset.
    Shows replica counts, conditions, and whether the rollout is complete."""
    return await rollout_status_get(context, namespace, resource_type, name)


@mcp.tool()
async def k8s_rollout_history(context: str, namespace: str, resource_type: str, name: str):
    """Get the revision history of a deployment, daemonset, or statefulset.
    Shows past revisions that can be used with rollout_undo."""
    return await rollout_history_get(context, namespace, resource_type, name)


@mcp.tool()
async def k8s_rollout_undo(context: str, namespace: str, resource_type: str, name: str,
                           to_revision: Optional[int] = None):
    """Roll back a deployment, daemonset, or statefulset to a previous revision.
    Omit to_revision to roll back to the immediately previous revision,
    or specify a revision number from rollout_history."""
    return await rollout_undo(context, namespace, resource_type, name, to_revision)


@mcp.tool()
async def k8s_rollout_restart(context: str, namespace: str, resource_type: str, name: str):
    """Trigger a rolling restart of a deployment, daemonset, or statefulset.
    All pods will be recreated in a rolling fashion."""
    return await rollout_restart(context, namespace, resource_type, name)


@mcp.tool()
async def k8s_rollout_pause(context: str, namespace: str, resource_type: str, name: str):
    """Pause an in-progress rollout for a deployment, daemonset, or statefulset.
    Useful for canary-style deployments where you want to inspect before continuing."""
    return await rollout_pause(context, namespace, resource_type, name)


@mcp.tool()
async def k8s_rollout_resume(context: str, namespace: str, resource_type: str, name: str):
    """Resume a previously paused rollout for a deployment, daemonset, or statefulset."""
    return await rollout_resume(context, namespace, resource_type, name)


# ========================================================================
# SCALING
# ========================================================================

@mcp.tool()
async def k8s_scale_resource(context: str, namespace: str, resource_type: str,
                             name: str, replicas: int):
    """Scale a deployment, statefulset, or replicaset to the specified number of replicas.
    Set replicas=0 to scale down completely."""
    return await resource_scale(context, namespace, resource_type, name, replicas)


@mcp.tool()
async def k8s_autoscale_resource(context: str, namespace: str, resource_type: str, name: str,
                                min_replicas: int, max_replicas: int, cpu_percent: int = 80):
    """Configure a Horizontal Pod Autoscaler (HPA) for a deployment, statefulset, or replicaset.
    Creates or updates an HPA that scales between min and max replicas based on CPU utilization."""
    return await resource_autoscale(context, namespace, resource_type, name,
                                    min_replicas, max_replicas, cpu_percent)


@mcp.tool()
async def k8s_update_resources(context: str, namespace: str, resource_type: str, name: str,
                              container: str, memory_request: Optional[str] = None,
                              memory_limit: Optional[str] = None,
                              cpu_request: Optional[str] = None,
                              cpu_limit: Optional[str] = None):
    """Update CPU/memory requests and limits for a specific container in a deployment,
    statefulset, or daemonset. Values use Kubernetes notation (e.g., '128Mi', '500m', '1Gi', '2')."""
    return await resource_update_resources(context, namespace, resource_type, name, container,
                                           memory_request, memory_limit, cpu_request, cpu_limit)


# ========================================================================
# RESOURCE CREATION, MODIFICATION & DELETION
# ========================================================================

@mcp.tool()
async def k8s_create_resource(context: str, yaml_content: str, namespace: Optional[str] = None):
    """Create a Kubernetes resource from YAML or JSON content.
    The content must include apiVersion, kind, and metadata.
    Optionally override the namespace."""
    return await k8s_create(context, yaml_content, namespace)


@mcp.tool()
async def k8s_apply_resource(context: str, yaml_content: str, namespace: Optional[str] = None):
    """Apply a configuration to a resource (create if it doesn't exist, update if it does).
    Similar to 'kubectl apply'. The content must include apiVersion, kind, and metadata with name."""
    return await k8s_apply(context, yaml_content, namespace)


@mcp.tool()
async def k8s_delete_resource(context: str, resource_type: str, name: str,
                              namespace: Optional[str] = None,
                              grace_period: Optional[int] = None,
                              force: bool = False):
    """Delete a Kubernetes resource. Supports all common resource types
    (pod, deployment, service, configmap, secret, statefulset, daemonset, job, cronjob,
    ingress, pvc, pv, namespace, serviceaccount, networkpolicy, hpa).
    Set force=True for immediate deletion (grace_period=0)."""
    return await k8s_delete(context, resource_type, name, namespace, grace_period, force)


@mcp.tool()
async def k8s_patch_resource(context: str, resource_type: str, name: str,
                            patch: dict, namespace: Optional[str] = None):
    """Update specific fields of a resource using a strategic merge patch.
    Supports pod, deployment, service, configmap, secret, and custom resources."""
    return await k8s_patch(context, resource_type, name, patch, namespace)


@mcp.tool()
async def k8s_label_resource(context: str, resource_type: str, name: str,
                            labels: dict, namespace: Optional[str] = None,
                            overwrite: bool = False):
    """Add or update labels on a Kubernetes resource.
    Labels are key-value pairs used for organizing and selecting resources."""
    return await k8s_label(context, resource_type, name, labels, namespace, overwrite)


@mcp.tool()
async def k8s_annotate_resource(context: str, resource_type: str, name: str,
                               annotations: dict, namespace: Optional[str] = None,
                               overwrite: bool = False):
    """Add or update annotations on a Kubernetes resource.
    Annotations store non-identifying metadata for tools and libraries."""
    return await k8s_annotate(context, resource_type, name, annotations, namespace, overwrite)


# ========================================================================
# WORKLOAD MANAGEMENT
# ========================================================================

@mcp.tool()
async def k8s_expose_resource(context: str, resource_type: str, name: str, port: int,
                             target_port: Optional[int] = None,
                             namespace: Optional[str] = None,
                             protocol: Optional[str] = None,
                             service_name: Optional[str] = None,
                             labels: Optional[dict] = None,
                             selector: Optional[str] = None,
                             type: Optional[str] = None):
    """Expose a deployment or pod as a new Kubernetes Service.
    Creates a Service that routes traffic to the target resource.
    Specify type='LoadBalancer' for external access or type='NodePort' for node-level access."""
    return await k8s_expose(context, resource_type, name, port, target_port, namespace,
                           protocol, service_name, labels, selector, type)


@mcp.tool()
async def k8s_run_pod(context: str, name: str, image: str,
                     namespace: Optional[str] = None,
                     command: Optional[List[str]] = None,
                     env: Optional[Dict[str, str]] = None,
                     labels: Optional[Dict[str, str]] = None,
                     restart: Optional[str] = None):
    """Create and run a pod with the specified container image.
    Useful for running one-off tasks, debugging, or testing.
    Set restart='Never' for one-shot jobs."""
    return await k8s_run(context, name, image, namespace, command, env, labels, restart)


@mcp.tool()
async def k8s_set_resources_for_container(context: str, resource_type: str, resource_name: str,
                                         namespace: Optional[str] = None,
                                         containers: Optional[list] = None,
                                         limits: Optional[dict] = None,
                                         requests: Optional[dict] = None):
    """Set resource limits and requests for containers in a deployment, statefulset, or daemonset.
    Example: limits={'cpu': '500m', 'memory': '256Mi'}, requests={'cpu': '100m', 'memory': '128Mi'}."""
    return await k8s_set_resources(context, resource_type, resource_name, namespace,
                                  containers, limits, requests)


# ========================================================================
# NODE MANAGEMENT
# ========================================================================

@mcp.tool()
async def k8s_cordon_node(context: str, node_name: str):
    """Mark a node as unschedulable. Existing pods continue running
    but no new pods will be scheduled on this node."""
    return await k8s_cordon(context, node_name)


@mcp.tool()
async def k8s_uncordon_node(context: str, node_name: str):
    """Mark a previously cordoned node as schedulable again.
    New pods can be scheduled on this node after uncordoning."""
    return await k8s_uncordon(context, node_name)


@mcp.tool()
async def k8s_drain_node(context: str, node_name: str, force: bool = False,
                        ignore_daemonsets: bool = False, delete_local_data: bool = False,
                        timeout: Optional[int] = None):
    """Drain a node by evicting all pods, preparing it for maintenance.
    Automatically cordons the node first. Set ignore_daemonsets=True to skip DaemonSet pods.
    Set force=True to evict pods not managed by a controller."""
    return await k8s_drain(context, node_name, force, ignore_daemonsets, delete_local_data, timeout)


@mcp.tool()
async def k8s_taint_node(context: str, node_name: str, key: str,
                        value: Optional[str] = None, effect: str = "NoSchedule"):
    """Add a taint to a node. Taints prevent pods without matching tolerations from being scheduled.
    Effects: NoSchedule (hard), PreferNoSchedule (soft), NoExecute (evict existing pods too)."""
    return await k8s_taint(context, node_name, key, value, effect)


@mcp.tool()
async def k8s_untaint_node(context: str, node_name: str, key: str,
                          effect: Optional[str] = None):
    """Remove a taint from a node. Omit effect to remove all taints with the given key."""
    return await k8s_untaint(context, node_name, key, effect)


# ========================================================================
# POD OPERATIONS
# ========================================================================

@mcp.tool()
async def k8s_pod_exec(context: str, pod_name: str, command: str,
                      container: Optional[str] = None,
                      namespace: Optional[str] = None,
                      stdin: bool = False, tty: bool = False,
                      timeout: Optional[int] = None):
    """Execute a command inside a running container. Supports quoted arguments
    (e.g., 'ls -la "/my dir"'). Specify container for multi-container pods.
    Defaults to the 'default' namespace if not specified."""
    return await k8s_exec_command(context, pod_name, command, container, namespace,
                                  stdin, tty, timeout)


# ========================================================================
# SECRETS & CONFIGMAPS
# ========================================================================

@mcp.tool()
async def k8s_list_secret(context: str, namespace: Optional[str] = None,
                          label_selector: Optional[str] = None):
    """List Kubernetes Secrets with metadata (keys only, values hidden for security).
    Use label_selector to filter (e.g., 'app=myapp'). Omit namespace for all namespaces."""
    return await k8s_list_secrets(context, namespace, label_selector)


@mcp.tool()
async def k8s_get_secret_detail(context: str, name: str, namespace: str,
                                decode: bool = False):
    """Get a Kubernetes Secret. By default shows only key names for security.
    Set decode=True to include the actual decoded values.
    Use with caution - decoded secrets may contain sensitive credentials."""
    return await k8s_get_secret(context, name, namespace, decode)


@mcp.tool()
async def k8s_create_secret_resource(context: str, name: str, namespace: str,
                                     data: Dict[str, str],
                                     secret_type: str = "Opaque",
                                     labels: Optional[Dict[str, str]] = None):
    """Create a new Kubernetes Secret. Values in data will be automatically base64-encoded.
    Common types: Opaque (default), kubernetes.io/tls, kubernetes.io/dockerconfigjson."""
    return await k8s_create_secret(context, name, namespace, data, secret_type, labels)


@mcp.tool()
async def k8s_list_configmap(context: str, namespace: Optional[str] = None,
                             label_selector: Optional[str] = None):
    """List Kubernetes ConfigMaps with their key names.
    Use label_selector to filter. Omit namespace for all namespaces."""
    return await k8s_list_configmaps(context, namespace, label_selector)


@mcp.tool()
async def k8s_get_configmap_detail(context: str, name: str, namespace: str):
    """Get a Kubernetes ConfigMap with its full data contents."""
    return await k8s_get_configmap(context, name, namespace)


@mcp.tool()
async def k8s_create_configmap_resource(context: str, name: str, namespace: str,
                                        data: Dict[str, str],
                                        labels: Optional[Dict[str, str]] = None):
    """Create a new Kubernetes ConfigMap with the specified key-value data pairs."""
    return await k8s_create_configmap(context, name, namespace, data, labels)


# ========================================================================
# RBAC (Role-Based Access Control)
# ========================================================================

@mcp.tool()
async def k8s_get_roles(context: str, namespace: Optional[str] = None):
    """List RBAC Roles with their permission rules.
    Roles grant permissions within a specific namespace.
    Omit namespace to list roles across all namespaces."""
    return await k8s_list_roles(context, namespace)


@mcp.tool()
async def k8s_get_clusterroles(context: str):
    """List RBAC ClusterRoles with their permission rules.
    ClusterRoles grant cluster-wide permissions or can be bound per-namespace."""
    return await k8s_list_clusterroles(context)


@mcp.tool()
async def k8s_get_rolebindings(context: str, namespace: Optional[str] = None):
    """List RBAC RoleBindings showing which subjects (users, groups, service accounts)
    are bound to which roles. Omit namespace for all namespaces."""
    return await k8s_list_rolebindings(context, namespace)


@mcp.tool()
async def k8s_get_clusterrolebindings(context: str):
    """List RBAC ClusterRoleBindings showing cluster-wide role assignments."""
    return await k8s_list_clusterrolebindings(context)


@mcp.tool()
async def k8s_get_service_accounts(context: str, namespace: Optional[str] = None):
    """List Kubernetes ServiceAccounts. ServiceAccounts provide pod-level identity
    for RBAC authorization. Omit namespace for all namespaces."""
    return await k8s_list_service_accounts(context, namespace)


# ========================================================================
# STORAGE
# ========================================================================

@mcp.tool()
async def k8s_get_pvcs(context: str, namespace: Optional[str] = None,
                      label_selector: Optional[str] = None):
    """List PersistentVolumeClaims (PVCs) with status, capacity, access modes,
    and storage class. Omit namespace for all namespaces."""
    return await k8s_list_pvcs(context, namespace, label_selector)


@mcp.tool()
async def k8s_get_pvs(context: str):
    """List PersistentVolumes (PVs) in the cluster with capacity, access modes,
    reclaim policy, and bound claim information."""
    return await k8s_list_pvs(context)


@mcp.tool()
async def k8s_get_storage_classes(context: str):
    """List StorageClasses in the cluster with provisioner, reclaim policy,
    volume binding mode, and whether each is the default class."""
    return await k8s_list_storage_classes(context)


# ========================================================================
# NETWORKING
# ========================================================================

@mcp.tool()
async def k8s_get_network_policies(context: str, namespace: Optional[str] = None):
    """List NetworkPolicies that control pod-to-pod and pod-to-external traffic.
    Shows pod selectors, policy types (Ingress/Egress), and rule counts."""
    return await k8s_list_network_policies(context, namespace)


# ========================================================================
# JOB MANAGEMENT
# ========================================================================

@mcp.tool()
async def k8s_get_jobs(context: str, namespace: Optional[str] = None,
                      label_selector: Optional[str] = None):
    """List Kubernetes Jobs with completion status, active/succeeded/failed counts,
    and timing information. Omit namespace for all namespaces."""
    return await k8s_list_jobs(context, namespace, label_selector)


@mcp.tool()
async def k8s_get_cronjobs(context: str, namespace: Optional[str] = None,
                           label_selector: Optional[str] = None):
    """List Kubernetes CronJobs with schedule, suspension status, active jobs,
    and last schedule/success times. Omit namespace for all namespaces."""
    return await k8s_list_cronjobs(context, namespace, label_selector)


# ========================================================================
# ENTRY POINT
# ========================================================================

if __name__ == "__main__":
    # Set kubeconfig directory from environment variable if provided
    kubeconfig_dir = os.environ.get("KUBECONFIG_DIR")
    if kubeconfig_dir:
        # Check if the path is a file instead of a directory
        if os.path.isfile(kubeconfig_dir):
            # Use the parent directory if pointing to a file
            kubeconfig_dir = os.path.dirname(kubeconfig_dir)
            os.environ["KUBECONFIG_DIR"] = kubeconfig_dir
        print(f"Using kubeconfig directory: {kubeconfig_dir}")

    print("Starting Kubernetes MCP server with stdio transport...")
    mcp.run(transport="stdio")