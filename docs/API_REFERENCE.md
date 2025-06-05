# API Reference

Complete reference for all MCP tools provided by k8s-multicluster-mcp.

## Context Management

### k8s_get_contexts
List all available Kubernetes contexts from the kubeconfig files.

**Parameters:** None

**Returns:** List of context names with their cluster information

**Example:**
```json
{
  "contexts": [
    {
      "name": "prod-aws-us-east-1",
      "cluster": "eks-prod",
      "user": "eks-user"
    }
  ]
}
```

## Cluster Information

### k8s_get_namespaces
List all namespaces in a specified Kubernetes context.

**Parameters:**
- `context` (string, required): Kubernetes context name

**Returns:** List of namespace names and their status

### k8s_get_nodes
List all nodes in a Kubernetes cluster.

**Parameters:**
- `context` (string, required): Kubernetes context name

**Returns:** List of nodes with status, roles, and version information

## Resource Operations

### k8s_get_resources
List Kubernetes resources of a specified kind.

**Parameters:**
- `context` (string, required): Kubernetes context name
- `kind` (string, required): Resource kind (e.g., "pods", "deployments")
- `namespace` (string, optional): Namespace to filter by
- `group` (string, optional): API group
- `version` (string, optional): API version

**Returns:** List of resources with basic information

### k8s_get_resource
Get detailed information about a specific resource.

**Parameters:**
- `context` (string, required): Kubernetes context name
- `namespace` (string, required): Namespace
- `kind` (string, required): Resource kind
- `name` (string, required): Resource name
- `group` (string, optional): API group
- `version` (string, optional): API version

**Returns:** Complete resource specification

### k8s_describe
Show detailed information about a specific resource or group of resources.

**Parameters:**
- `context` (string, required): Kubernetes context name
- `resource_type` (string, required): Resource type
- `name` (string, optional): Resource name
- `namespace` (string, optional): Namespace
- `selector` (string, optional): Label selector
- `all_namespaces` (bool, optional): Search all namespaces

**Returns:** Detailed description similar to kubectl describe

## Pod Operations

### k8s_get_pod_logs
Get logs from a specific pod.

**Parameters:**
- `context` (string, required): Kubernetes context name
- `namespace` (string, required): Namespace
- `pod` (string, required): Pod name
- `previousContainer` (bool, optional): Get previous container logs
- `sinceDuration` (string, optional): Time duration (e.g., "5m", "1h")

**Returns:** Pod logs as text

### k8s_pod_exec
Execute a command in a container.

**Parameters:**
- `context` (string, required): Kubernetes context name
- `pod_name` (string, required): Pod name
- `command` (string, required): Command to execute
- `container` (string, optional): Container name
- `namespace` (string, optional): Namespace
- `stdin` (bool, optional): Pass stdin
- `tty` (bool, optional): Allocate TTY
- `timeout` (int, optional): Timeout in seconds

**Returns:** Command output

## Metrics

### k8s_top_nodes
Display resource usage of nodes.

**Parameters:**
- `context` (string, required): Kubernetes context name

**Returns:** CPU and memory usage for each node

### k8s_top_pods
Display resource usage of pods.

**Parameters:**
- `context` (string, required): Kubernetes context name
- `namespace` (string, optional): Namespace filter

**Returns:** CPU and memory usage for pods

## Rollout Management

### k8s_rollout_status
Get the status of a rollout.

**Parameters:**
- `context` (string, required): Kubernetes context name
- `namespace` (string, required): Namespace
- `resource_type` (string, required): Resource type (deployment/daemonset/statefulset)
- `name` (string, required): Resource name

**Returns:** Rollout status information

### k8s_rollout_history
Get revision history of a rollout.

**Parameters:**
- `context` (string, required): Kubernetes context name
- `namespace` (string, required): Namespace
- `resource_type` (string, required): Resource type
- `name` (string, required): Resource name

**Returns:** List of revisions with change causes

### k8s_rollout_undo
Undo a rollout to a previous revision.

**Parameters:**
- `context` (string, required): Kubernetes context name
- `namespace` (string, required): Namespace
- `resource_type` (string, required): Resource type
- `name` (string, required): Resource name
- `to_revision` (int, optional): Target revision number

**Returns:** Rollback status

### k8s_rollout_restart
Restart a rollout.

**Parameters:**
- `context` (string, required): Kubernetes context name
- `namespace` (string, required): Namespace
- `resource_type` (string, required): Resource type
- `name` (string, required): Resource name

**Returns:** Restart status

### k8s_rollout_pause
Pause a rollout.

**Parameters:**
- `context` (string, required): Kubernetes context name
- `namespace` (string, required): Namespace
- `resource_type` (string, required): Resource type
- `name` (string, required): Resource name

**Returns:** Pause status

### k8s_rollout_resume
Resume a paused rollout.

**Parameters:**
- `context` (string, required): Kubernetes context name
- `namespace` (string, required): Namespace
- `resource_type` (string, required): Resource type
- `name` (string, required): Resource name

**Returns:** Resume status

## Scaling

### k8s_scale_resource
Scale a resource to specified replicas.

**Parameters:**
- `context` (string, required): Kubernetes context name
- `namespace` (string, required): Namespace
- `resource_type` (string, required): Resource type
- `name` (string, required): Resource name
- `replicas` (int, required): Number of replicas

**Returns:** Scale operation status

### k8s_autoscale_resource
Configure Horizontal Pod Autoscaler.

**Parameters:**
- `context` (string, required): Kubernetes context name
- `namespace` (string, required): Namespace
- `resource_type` (string, required): Resource type
- `name` (string, required): Resource name
- `min_replicas` (int, required): Minimum replicas
- `max_replicas` (int, required): Maximum replicas
- `cpu_percent` (int, optional): Target CPU percentage (default: 80)

**Returns:** HPA configuration status

### k8s_update_resources
Update resource requests and limits.

**Parameters:**
- `context` (string, required): Kubernetes context name
- `namespace` (string, required): Namespace
- `resource_type` (string, required): Resource type
- `name` (string, required): Resource name
- `container` (string, required): Container name
- `memory_request` (string, optional): Memory request (e.g., "256Mi")
- `memory_limit` (string, optional): Memory limit
- `cpu_request` (string, optional): CPU request (e.g., "100m")
- `cpu_limit` (string, optional): CPU limit

**Returns:** Update status

## Resource Management

### k8s_create_resource
Create a Kubernetes resource from YAML/JSON.

**Parameters:**
- `context` (string, required): Kubernetes context name
- `yaml_content` (string, required): YAML/JSON content
- `namespace` (string, optional): Override namespace

**Returns:** Creation status

### k8s_apply_resource
Apply a configuration to a resource.

**Parameters:**
- `context` (string, required): Kubernetes context name
- `yaml_content` (string, required): YAML/JSON content
- `namespace` (string, optional): Override namespace

**Returns:** Apply status

### k8s_patch_resource
Update fields of a resource.

**Parameters:**
- `context` (string, required): Kubernetes context name
- `resource_type` (string, required): Resource type
- `name` (string, required): Resource name
- `patch` (object, required): JSON patch content
- `namespace` (string, optional): Namespace

**Returns:** Patch status

### k8s_label_resource
Update labels on a resource.

**Parameters:**
- `context` (string, required): Kubernetes context name
- `resource_type` (string, required): Resource type
- `name` (string, required): Resource name
- `labels` (object, required): Labels to add/update
- `namespace` (string, optional): Namespace
- `overwrite` (bool, optional): Overwrite existing labels

**Returns:** Label update status

### k8s_annotate_resource
Update annotations on a resource.

**Parameters:**
- `context` (string, required): Kubernetes context name
- `resource_type` (string, required): Resource type
- `name` (string, required): Resource name
- `annotations` (object, required): Annotations to add/update
- `namespace` (string, optional): Namespace
- `overwrite` (bool, optional): Overwrite existing annotations

**Returns:** Annotation update status

## Workload Management

### k8s_expose_resource
Expose a resource as a new Kubernetes service.

**Parameters:**
- `context` (string, required): Kubernetes context name
- `resource_type` (string, required): Resource type
- `name` (string, required): Resource name
- `port` (int, required): Service port
- `target_port` (int, optional): Target port
- `namespace` (string, optional): Namespace
- `protocol` (string, optional): Protocol (TCP/UDP)
- `service_name` (string, optional): Custom service name
- `labels` (object, optional): Service labels
- `selector` (string, optional): Pod selector
- `type` (string, optional): Service type (ClusterIP/NodePort/LoadBalancer)

**Returns:** Service creation status

### k8s_set_resources_for_container
Set resource limits and requests for containers.

**Parameters:**
- `context` (string, required): Kubernetes context name
- `resource_type` (string, required): Resource type
- `resource_name` (string, required): Resource name
- `namespace` (string, optional): Namespace
- `containers` (array, optional): Container names
- `limits` (object, optional): Resource limits
- `requests` (object, optional): Resource requests

**Returns:** Resource update status

## Node Management

### k8s_cordon_node
Mark a node as unschedulable.

**Parameters:**
- `context` (string, required): Kubernetes context name
- `node_name` (string, required): Node name

**Returns:** Cordon status

### k8s_uncordon_node
Mark a node as schedulable.

**Parameters:**
- `context` (string, required): Kubernetes context name
- `node_name` (string, required): Node name

**Returns:** Uncordon status

### k8s_drain_node
Drain a node in preparation for maintenance.

**Parameters:**
- `context` (string, required): Kubernetes context name
- `node_name` (string, required): Node name
- `force` (bool, optional): Force deletion
- `ignore_daemonsets` (bool, optional): Ignore DaemonSets
- `delete_local_data` (bool, optional): Delete local data
- `timeout` (int, optional): Timeout in seconds

**Returns:** Drain status

### k8s_taint_node
Update taints on a node.

**Parameters:**
- `context` (string, required): Kubernetes context name
- `node_name` (string, required): Node name
- `key` (string, required): Taint key
- `value` (string, optional): Taint value
- `effect` (string, optional): Effect (NoSchedule/PreferNoSchedule/NoExecute)

**Returns:** Taint update status

### k8s_untaint_node
Remove taints from a node.

**Parameters:**
- `context` (string, required): Kubernetes context name
- `node_name` (string, required): Node name
- `key` (string, required): Taint key
- `effect` (string, optional): Effect to remove

**Returns:** Untaint status

## Discovery

### k8s_apis
List all available APIs in the cluster.

**Parameters:**
- `context` (string, required): Kubernetes context name

**Returns:** List of API groups and versions

### k8s_crds
List all Custom Resource Definitions.

**Parameters:**
- `context` (string, required): Kubernetes context name

**Returns:** List of CRDs with their groups and versions

## Diagnostics

### k8s_diagnose_application
Diagnose issues with a Kubernetes application.

**Parameters:**
- `context` (string, required): Kubernetes context name
- `namespace` (string, required): Namespace
- `app_name` (string, required): Application name
- `resource_type` (string, optional): Resource type (default: deployment)

**Returns:** Comprehensive diagnostic information including:
- Resource status
- Recent events
- Pod logs
- Resource usage
- Configuration issues 