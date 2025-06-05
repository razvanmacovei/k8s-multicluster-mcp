#!/usr/bin/env python3
import os

from mcp.server.fastmcp import FastMCP

# Create MCP server
mcp = FastMCP("KubernetesMCP")

from .tools.api_discovery import list_k8s_apis as apis_list
from .tools.api_discovery import list_k8s_crds as crds_list
from .tools.contexts import list_k8s_contexts as contexts_list
from .tools.describe import describe_k8s_resource as resource_describe
from .tools.diagnosis import diagnose_k8s_application as application_diagnose
from .tools.events import list_k8s_events as events_list
from .tools.metrics import top_k8s_nodes as nodes_top
from .tools.metrics import top_k8s_pods as pods_top
from .tools.namespaces import list_k8s_namespaces as namespaces_list
from .tools.node_management import k8s_cordon, k8s_drain, k8s_taint, k8s_uncordon, k8s_untaint
from .tools.nodes import list_k8s_nodes as nodes_list
from .tools.pod_operations import k8s_exec_command
from .tools.pods import get_k8s_pod_logs as pod_logs_get
from .tools.pods import list_k8s_resources as resources_list

# Import new tools
from .tools.resource_management import k8s_annotate, k8s_apply, k8s_create, k8s_label, k8s_patch
from .tools.resources import get_k8s_resource as resource_get
from .tools.rollouts import get_k8s_rollout_history as rollout_history_get
from .tools.rollouts import get_k8s_rollout_status as rollout_status_get
from .tools.rollouts import k8s_rollout_pause as rollout_pause
from .tools.rollouts import k8s_rollout_restart as rollout_restart
from .tools.rollouts import k8s_rollout_resume as rollout_resume
from .tools.rollouts import k8s_rollout_undo as rollout_undo
from .tools.scaling import k8s_autoscale_resource as resource_autoscale
from .tools.scaling import k8s_scale_resource as resource_scale
from .tools.scaling import k8s_update_resources as resource_update_resources
from .tools.workload_management import k8s_expose, k8s_set_resources


# Register tools using decorators
@mcp.tool()
async def k8s_get_contexts():
    """List all available Kubernetes contexts from the kubeconfig files."""
    return await contexts_list()


@mcp.tool()
async def k8s_get_namespaces(context: str):
    """List all namespaces in a specified Kubernetes context."""
    return await namespaces_list(context)


@mcp.tool()
async def k8s_get_nodes(context: str):
    """List all nodes in a Kubernetes cluster."""
    return await nodes_list(context)


@mcp.tool()
async def k8s_get_resources(context: str, kind: str, namespace: str = None, group: str = None, version: str = None):
    """List Kubernetes resources of a specified kind."""
    return await resources_list(context, kind, namespace, group, version)


@mcp.tool()
async def k8s_get_pod_logs(
    context: str, namespace: str, pod: str, previousContainer: bool = False, sinceDuration: str = None
):
    """Get logs for a Kubernetes pod."""
    return await pod_logs_get(context, namespace, pod, previousContainer, sinceDuration)


@mcp.tool()
async def k8s_get_events(context: str, namespace: str, limit: int = 100):
    """List Kubernetes events using specific context in a specified namespace."""
    return await events_list(context, namespace, limit)


@mcp.tool()
async def k8s_get_resource(context: str, namespace: str, kind: str, name: str, group: str = None, version: str = None):
    """Get Kubernetes resource completely."""
    return await resource_get(context, namespace, kind, name, group, version)


@mcp.tool()
async def k8s_top_nodes(context: str):
    """Display resource usage (CPU/memory) of nodes in a Kubernetes cluster."""
    return await nodes_top(context)


@mcp.tool()
async def k8s_top_pods(context: str, namespace: str = None):
    """Display resource usage (CPU/memory) of pods in a Kubernetes cluster."""
    return await pods_top(context, namespace)


@mcp.tool()
async def k8s_rollout_status(context: str, namespace: str, resource_type: str, name: str):
    """Get the status of a rollout for a deployment, daemonset, or statefulset."""
    return await rollout_status_get(context, namespace, resource_type, name)


@mcp.tool()
async def k8s_rollout_history(context: str, namespace: str, resource_type: str, name: str):
    """Get the revision history of a rollout for a deployment, daemonset, or statefulset."""
    return await rollout_history_get(context, namespace, resource_type, name)


@mcp.tool()
async def k8s_rollout_undo(context: str, namespace: str, resource_type: str, name: str, to_revision: int = None):
    """Undo a rollout to a previous revision for a deployment, daemonset, or statefulset."""
    return await rollout_undo(context, namespace, resource_type, name, to_revision)


@mcp.tool()
async def k8s_rollout_restart(context: str, namespace: str, resource_type: str, name: str):
    """Restart a rollout for a deployment, daemonset, or statefulset."""
    return await rollout_restart(context, namespace, resource_type, name)


@mcp.tool()
async def k8s_rollout_pause(context: str, namespace: str, resource_type: str, name: str):
    """Pause a rollout for a deployment, daemonset, or statefulset."""
    return await rollout_pause(context, namespace, resource_type, name)


@mcp.tool()
async def k8s_rollout_resume(context: str, namespace: str, resource_type: str, name: str):
    """Resume a rollout for a deployment, daemonset, or statefulset."""
    return await rollout_resume(context, namespace, resource_type, name)


@mcp.tool()
async def k8s_scale_resource(context: str, namespace: str, resource_type: str, name: str, replicas: int):
    """Scale a deployment, statefulset, or replicaset to the specified number of replicas."""
    return await resource_scale(context, namespace, resource_type, name, replicas)


@mcp.tool()
async def k8s_autoscale_resource(
    context: str,
    namespace: str,
    resource_type: str,
    name: str,
    min_replicas: int,
    max_replicas: int,
    cpu_percent: int = 80,
):
    """Configure a Horizontal Pod Autoscaler (HPA) for a deployment, statefulset, or replicaset."""
    return await resource_autoscale(context, namespace, resource_type, name, min_replicas, max_replicas, cpu_percent)


@mcp.tool()
async def k8s_update_resources(
    context: str,
    namespace: str,
    resource_type: str,
    name: str,
    container: str,
    memory_request: str = None,
    memory_limit: str = None,
    cpu_request: str = None,
    cpu_limit: str = None,
):
    """Update resource requests and limits for a container in a deployment, statefulset, or daemonset."""
    return await resource_update_resources(
        context, namespace, resource_type, name, container, memory_request, memory_limit, cpu_request, cpu_limit
    )


@mcp.tool()
async def k8s_diagnose_application(context: str, namespace: str, app_name: str, resource_type: str = "deployment"):
    """Diagnose issues with a Kubernetes application by checking resource status, events, and logs."""
    return await application_diagnose(context, namespace, app_name, resource_type)


@mcp.tool()
async def k8s_apis(context: str):
    """List all available APIs in the Kubernetes cluster."""
    return await apis_list(context)


@mcp.tool()
async def k8s_crds(context: str):
    """List all Custom Resource Definitions (CRDs) in the Kubernetes cluster."""
    return await crds_list(context)


@mcp.tool()
async def k8s_describe(
    context: str,
    resource_type: str,
    name: str = None,
    namespace: str = None,
    selector: str = None,
    all_namespaces: bool = False,
):
    """Show detailed information about a specific resource or group of resources."""
    return await resource_describe(context, resource_type, name, namespace, selector, all_namespaces)


# Register new tools
@mcp.tool()
async def k8s_create_resource(context: str, yaml_content: str, namespace: str = None):
    """Create a Kubernetes resource from YAML/JSON content."""
    return await k8s_create(context, yaml_content, namespace)


@mcp.tool()
async def k8s_apply_resource(context: str, yaml_content: str, namespace: str = None):
    """Apply a configuration to a resource by filename or stdin."""
    return await k8s_apply(context, yaml_content, namespace)


@mcp.tool()
async def k8s_patch_resource(context: str, resource_type: str, name: str, patch, namespace: str = None):
    """Update fields of a resource."""
    return await k8s_patch(context, resource_type, name, patch, namespace)


@mcp.tool()
async def k8s_label_resource(
    context: str, resource_type: str, name: str, labels, namespace: str = None, overwrite: bool = False
):
    """Update the labels on a resource."""
    return await k8s_label(context, resource_type, name, labels, namespace, overwrite)


@mcp.tool()
async def k8s_annotate_resource(
    context: str, resource_type: str, name: str, annotations, namespace: str = None, overwrite: bool = False
):
    """Update the annotations on a resource."""
    return await k8s_annotate(context, resource_type, name, annotations, namespace, overwrite)


@mcp.tool()
async def k8s_expose_resource(
    context: str,
    resource_type: str,
    name: str,
    port: int,
    target_port: int = None,
    namespace: str = None,
    protocol: str = None,
    service_name: str = None,
    labels=None,
    selector: str = None,
    type: str = None,
):
    """Expose a resource as a new Kubernetes service."""
    return await k8s_expose(
        context, resource_type, name, port, target_port, namespace, protocol, service_name, labels, selector, type
    )


@mcp.tool()
async def k8s_set_resources_for_container(
    context: str,
    resource_type: str,
    resource_name: str,
    namespace: str = None,
    containers=None,
    limits=None,
    requests=None,
):
    """Set resource limits and requests for containers."""
    return await k8s_set_resources(context, resource_type, resource_name, namespace, containers, limits, requests)


@mcp.tool()
async def k8s_cordon_node(context: str, node_name: str):
    """Mark a node as unschedulable."""
    return await k8s_cordon(context, node_name)


@mcp.tool()
async def k8s_uncordon_node(context: str, node_name: str):
    """Mark a node as schedulable."""
    return await k8s_uncordon(context, node_name)


@mcp.tool()
async def k8s_drain_node(
    context: str,
    node_name: str,
    force: bool = False,
    ignore_daemonsets: bool = False,
    delete_local_data: bool = False,
    timeout: int = None,
):
    """Drain a node in preparation for maintenance."""
    return await k8s_drain(context, node_name, force, ignore_daemonsets, delete_local_data, timeout)


@mcp.tool()
async def k8s_taint_node(context: str, node_name: str, key: str, value: str = None, effect: str = "NoSchedule"):
    """Update the taints on one or more nodes."""
    return await k8s_taint(context, node_name, key, value, effect)


@mcp.tool()
async def k8s_untaint_node(context: str, node_name: str, key: str, effect: str = None):
    """Remove the taints from a node."""
    return await k8s_untaint(context, node_name, key, effect)


@mcp.tool()
async def k8s_pod_exec(
    context: str,
    pod_name: str,
    command: str,
    container: str = None,
    namespace: str = None,
    stdin: bool = False,
    tty: bool = False,
    timeout: int = None,
):
    """Execute a command in a container."""
    return await k8s_exec_command(context, pod_name, command, container, namespace, stdin, tty, timeout)


def main():
    """Main entry point for the k8s-multicluster-mcp server."""
    # Set kubeconfig directory from environment variable if provided
    kubeconfig_dir = os.environ.get("KUBECONFIG_DIR")
    if kubeconfig_dir:
        # Check if the path is a file instead of a directory
        if os.path.isfile(kubeconfig_dir):
            # Use the parent directory if pointing to a file
            kubeconfig_dir = os.path.dirname(kubeconfig_dir)
            os.environ["KUBECONFIG_DIR"] = kubeconfig_dir
        print(f"Using kubeconfig directory: {kubeconfig_dir}")

    # FastMCP appears to only support stdio transport
    print("Starting Kubernetes MCP server with stdio transport...")
    # Run with stdio transport by default
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
