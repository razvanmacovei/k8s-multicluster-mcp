# Multi Cluster Kubernetes MCP Server

[![smithery badge](https://smithery.ai/badge/@razvanmacovei/k8s-multicluster-mcp)](https://smithery.ai/server/@razvanmacovei/k8s-multicluster-mcp)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)

An MCP (Model Context Protocol) server for managing multiple Kubernetes clusters simultaneously. Provides **60+ tools** covering cluster operations, resource management, monitoring, RBAC, storage, networking, and more -- all accessible through AI assistants like Claude Desktop.

## Quick Start

### Installing via Smithery

```bash
npx -y @smithery/cli install @razvanmacovei/k8s-multicluster-mcp --client claude
```

### Manual Installation

```bash
git clone https://github.com/razvanmacovei/k8s-multicluster-mcp.git
cd k8s-multicluster-mcp
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

### Docker

```bash
docker build -t k8s-mcp .
docker run -v ~/.kube:/root/.kube k8s-mcp
```

## Configuration

### Claude Desktop / MCP Client

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "kubernetes": {
      "command": "python3",
      "args": ["/path/to/k8s-multicluster-mcp/app.py"],
      "env": {
        "KUBECONFIG_DIR": "/path/to/your/kubeconfigs"
      }
    }
  }
}
```

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `KUBECONFIG_DIR` | `~/.kube` | Directory containing kubeconfig files. Each file can contain one or more contexts. |

Place your kubeconfig files in the configured directory. The server discovers all contexts across all files automatically.

### Prerequisites

- Python 3.11 or higher
- One or more kubeconfig files with valid cluster credentials
- `metrics-server` installed in clusters for `k8s_top_*` and `k8s_cluster_info` tools

## Multi-Cluster Management

This server is purpose-built for managing multiple Kubernetes clusters:

- **Automatic Discovery**: Scans all kubeconfig files in `KUBECONFIG_DIR` and aggregates contexts
- **Partial Name Matching**: Use `prod` instead of `arn:aws:eks:us-east-1:123456:cluster/prod-cluster`
- **Cross-Cluster Operations**: Compare resources, health, and configurations across clusters
- **Context Caching**: Efficient 30-second TTL cache avoids re-reading kubeconfig files on every call
- **Centralized Management**: Manage dev, staging, and production from a single interface

## Tools Reference (60+ tools)

### Cluster & Context Management (6 tools)

| Tool | Description |
|---|---|
| `k8s_get_contexts` | List all available contexts across all kubeconfig files |
| `k8s_get_namespaces` | List all namespaces in a cluster |
| `k8s_create_ns` | Create a new namespace with optional labels/annotations |
| `k8s_delete_ns` | Delete a namespace (protects system namespaces) |
| `k8s_get_nodes` | List all nodes with status, roles, capacity, and version |
| `k8s_cluster_info` | Comprehensive cluster health summary (nodes, pods, deployments, warnings) |

### Resource Discovery & Inspection (7 tools)

| Tool | Description |
|---|---|
| `k8s_get_resources` | List resources of any kind (pods, deployments, services, ingress, etc.) |
| `k8s_get_resource` | Get the complete definition of a single resource |
| `k8s_get_pod_logs` | Get pod logs with duration filtering and container selection |
| `k8s_get_events` | List cluster events in a namespace, sorted by most recent |
| `k8s_describe` | Detailed resource description similar to `kubectl describe` |
| `k8s_apis` | List all available API groups and resources in the cluster |
| `k8s_crds` | List all Custom Resource Definitions with versions and scope |

### Metrics & Monitoring (3 tools)

| Tool | Description |
|---|---|
| `k8s_top_nodes` | Display node CPU/memory usage alongside capacity |
| `k8s_top_pods` | Display pod/container CPU/memory usage |
| `k8s_diagnose_application` | Comprehensive app diagnostics with issue detection and recommendations |

### Rollout Management (6 tools)

| Tool | Description |
|---|---|
| `k8s_rollout_status` | Get rollout status for deployment/statefulset/daemonset |
| `k8s_rollout_history` | Get revision history |
| `k8s_rollout_undo` | Roll back to a previous revision |
| `k8s_rollout_restart` | Trigger a rolling restart |
| `k8s_rollout_pause` | Pause an in-progress rollout |
| `k8s_rollout_resume` | Resume a paused rollout |

### Scaling (3 tools)

| Tool | Description |
|---|---|
| `k8s_scale_resource` | Scale deployment/statefulset/replicaset to N replicas |
| `k8s_autoscale_resource` | Configure Horizontal Pod Autoscaler (HPA) |
| `k8s_update_resources` | Update CPU/memory requests and limits for a container |

### Resource CRUD (6 tools)

| Tool | Description |
|---|---|
| `k8s_create_resource` | Create a resource from YAML/JSON content |
| `k8s_apply_resource` | Apply configuration (create or update, like `kubectl apply`) |
| `k8s_delete_resource` | Delete any resource type with optional force/grace period |
| `k8s_patch_resource` | Update specific fields with strategic merge patch |
| `k8s_label_resource` | Add or update labels on a resource |
| `k8s_annotate_resource` | Add or update annotations on a resource |

### Workload Management (3 tools)

| Tool | Description |
|---|---|
| `k8s_expose_resource` | Expose a deployment/pod as a new Service |
| `k8s_run_pod` | Create and run a pod with a specified image |
| `k8s_set_resources_for_container` | Set resource limits/requests for containers |

### Node Management (5 tools)

| Tool | Description |
|---|---|
| `k8s_cordon_node` | Mark a node as unschedulable |
| `k8s_uncordon_node` | Mark a node as schedulable |
| `k8s_drain_node` | Drain a node by evicting pods (for maintenance) |
| `k8s_taint_node` | Add taints to a node |
| `k8s_untaint_node` | Remove taints from a node |

### Pod Operations (1 tool)

| Tool | Description |
|---|---|
| `k8s_pod_exec` | Execute a command in a container (supports quoted arguments) |

### Secrets & ConfigMaps (6 tools)

| Tool | Description |
|---|---|
| `k8s_list_secret` | List secrets with metadata (values hidden for security) |
| `k8s_get_secret_detail` | Get a secret; optionally decode values |
| `k8s_create_secret_resource` | Create a new secret (auto base64-encodes values) |
| `k8s_list_configmap` | List ConfigMaps with their key names |
| `k8s_get_configmap_detail` | Get a ConfigMap with full data contents |
| `k8s_create_configmap_resource` | Create a new ConfigMap |

### RBAC (5 tools)

| Tool | Description |
|---|---|
| `k8s_get_roles` | List RBAC Roles with permission rules |
| `k8s_get_clusterroles` | List RBAC ClusterRoles |
| `k8s_get_rolebindings` | List RoleBindings (who has what role) |
| `k8s_get_clusterrolebindings` | List ClusterRoleBindings |
| `k8s_get_service_accounts` | List ServiceAccounts |

### Storage (3 tools)

| Tool | Description |
|---|---|
| `k8s_get_pvcs` | List PersistentVolumeClaims with status, capacity, and storage class |
| `k8s_get_pvs` | List PersistentVolumes with capacity and bound claims |
| `k8s_get_storage_classes` | List StorageClasses with provisioner and default status |

### Networking (1 tool)

| Tool | Description |
|---|---|
| `k8s_get_network_policies` | List NetworkPolicies with pod selectors and rule counts |

### Job Management (2 tools)

| Tool | Description |
|---|---|
| `k8s_get_jobs` | List Jobs with completion status and timing |
| `k8s_get_cronjobs` | List CronJobs with schedule, suspend status, and last run |

## Usage Examples

### Cluster Health Check

```
Give me a health overview of my production cluster.
```

### Multi-Cluster Comparison

```
Compare the number of pods running in the 'backend' namespace between my 'prod' and 'staging' contexts.
```

### Diagnose Application Issues

```
My deployment 'my-app' in the 'production' namespace is having issues. Can you diagnose what's wrong?
```

### Scale Resources

```
Scale the 'backend' deployment in the 'default' namespace to 5 replicas.
```

### Resource Management

```
Delete the failed job 'data-migration-v1' in the 'batch' namespace.
```

```
Create a new namespace called 'staging' with the label environment=staging.
```

### Secret Management

```
List all secrets in the 'production' namespace and show me the keys in the 'api-credentials' secret.
```

### RBAC Inspection

```
Show me all role bindings in the 'default' namespace -- who has access to what?
```

### Storage Overview

```
List all PVCs in the cluster and show which ones are Pending.
```

### Node Maintenance

```
Cordon node 'worker-3', drain it ignoring DaemonSets, then uncordon when maintenance is complete.
```

### Rollback Deployment

```
Roll back the 'api-gateway' deployment in the 'services' namespace to the previous version.
```

### Execute in Pod

```
Run 'ls -la /app/config' inside the 'app' container of pod 'web-app-xyz' in the 'default' namespace.
```

### Create Resources

```
Create a new deployment with this YAML:
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.27
        ports:
        - containerPort: 80
```

## Architecture

```
k8s-multicluster-mcp/
├── app.py                          # MCP server entry point & tool registration
├── src/
│   ├── utils/
│   │   ├── k8s_client.py           # Multi-cluster client with context caching
│   │   └── pluralize.py            # Kubernetes resource kind pluralization
│   └── tools/
│       ├── contexts.py             # Context listing
│       ├── namespaces.py           # Namespace listing
│       ├── namespace_management.py # Namespace create/delete
│       ├── nodes.py                # Node listing
│       ├── pods.py                 # Resource listing & pod logs
│       ├── resources.py            # Single resource retrieval
│       ├── events.py               # Event listing
│       ├── describe.py             # kubectl describe equivalent
│       ├── api_discovery.py        # API & CRD discovery
│       ├── metrics.py              # Node/pod metrics (top)
│       ├── diagnosis.py            # Application diagnostics
│       ├── cluster_health.py       # Cluster health summary
│       ├── rollouts.py             # Rollout management
│       ├── scaling.py              # Scale & autoscale & resource updates
│       ├── resource_management.py  # Create, apply, patch, label, annotate
│       ├── delete_resource.py      # Resource deletion
│       ├── workload_management.py  # Expose, run pod, set resources
│       ├── node_management.py      # Cordon, drain, taint
│       ├── pod_operations.py       # Exec into pods
│       ├── secret_configmap.py     # Secret & ConfigMap management
│       ├── rbac.py                 # Roles, bindings, service accounts
│       ├── storage_network.py      # PVC, PV, StorageClass, NetworkPolicy
│       └── job_management.py       # Jobs & CronJobs
├── requirements.txt
├── pyproject.toml
├── Dockerfile
└── smithery.yaml
```

## What's New in v2.0.0

- **20+ new tools**: Resource deletion, namespace management, secrets & configmaps, RBAC inspection, storage & network visibility, job management, cluster health summary, pod creation
- **Bug fixes**: Fixed resource pluralization (e.g., `Ingress` -> `ingresses` not `ingresss`), fixed pod exec command splitting to handle quoted arguments, fixed timeout parameter handling
- **Performance**: Context discovery now uses a 30-second TTL cache with direct context-to-file mapping, eliminating redundant file scanning
- **Improved tool descriptions**: All 60+ tools have detailed descriptions for better AI assistant integration
- **Dependency cleanup**: Removed unused `fastapi` and `uvicorn` dependencies
- **Security**: Namespace deletion protects system namespaces; secret values hidden by default

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
