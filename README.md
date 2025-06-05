# Multi Cluster Kubernetes MCP Server
[![smithery badge](https://smithery.ai/badge/@razvanmacovei/k8s-multicluster-mcp)](https://smithery.ai/server/@razvanmacovei/k8s-multicluster-mcp)

An MCP (Model Context Protocol) server application for Kubernetes operations, providing a standardized API to interact with multiple Kubernetes clusters simultaneously using multiple kubeconfig files.

## Quick Install

Add this MCP server to Cursor with one click:

[Add k8s-multicluster MCP server to Cursor](cursor://anysphere.cursor-deeplink/mcp/install?name=k8s-multicluster&config=eyJjb21tYW5kIjoicHl0aG9uMyIsImFyZ3MiOlsiYXBwLnB5Il0sImVudiI6eyJLVUJFQ09ORklHX0RJUiI6Ii9wYXRoL3RvL3lvdXIva3ViZWNvbmZpZ3MifX0=)

**Note:** After installation, you'll need to update the `KUBECONFIG_DIR` environment variable to point to your actual kubeconfig directory.

### Alternative Installation Options

Different deployment scenarios require different configurations:

- **Development (current directory):** [Add to Cursor](cursor://anysphere.cursor-deeplink/mcp/install?name=k8s-multicluster&config=eyJjb21tYW5kIjoicHl0aG9uMyIsImFyZ3MiOlsiYXBwLnB5Il0sImVudiI6eyJLVUJFQ09ORklHX0RJUiI6Ii9wYXRoL3RvL3lvdXIva3ViZWNvbmZpZ3MifX0=)
- **With UV package manager:** [Add to Cursor](cursor://anysphere.cursor-deeplink/mcp/install?name=k8s-multicluster&config=eyJjb21tYW5kIjoidXYiLCJhcmdzIjpbIi0tZGlyZWN0b3J5IiwiLiIsInJ1biIsImFwcC5weSJdLCJlbnYiOnsiS1VCRUNPTkZJR19ESVIiOiIvcGF0aC90by95b3VyL2t1YmVjb25maWdzIn19)

### MCPO Server Configuration

Add the following configuration to your MCPO server's `config.json` file (e.g., in Claude Desktop):

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

> Replace `/path/to/your/kubeconfigs` with the actual path to your kubeconfig files directory.

The server expects multiple kubeconfig files to be placed in the directory you specified. Each kubeconfig file represents a different Kubernetes cluster that you can interact with.


## Installation

### Option 1: One-Click Install (Recommended)

Click the "Add to Cursor" button above for the fastest installation method. After installation:

1. Open Cursor Settings → Features → MCP
2. Find "k8s-multicluster" in your server list
3. Edit the server configuration to update the `KUBECONFIG_DIR` environment variable to your actual kubeconfig directory path

### Option 2: Manual Configuration

Add the following to your Cursor MCP configuration file (`~/.cursor/mcp.json` or `.cursor/mcp.json` in your project):

#### Using Python3 directly:
```json
{
  "mcpServers": {
    "k8s-multicluster": {
      "command": "python3",
      "args": ["/path/to/k8s-multicluster-mcp/app.py"],
      "env": {
        "KUBECONFIG_DIR": "/path/to/your/kubeconfigs"
      }
    }
  }
}
```

#### Using UV (recommended for development):
```json
{
  "mcpServers": {
    "k8s-multicluster": {
      "command": "uv",
      "args": ["--directory", "/path/to/k8s-multicluster-mcp", "run", "app.py"],
      "env": {
        "KUBECONFIG_DIR": "/path/to/your/kubeconfigs"
      }
    }
  }
}
```

### Option 3: Installing via Smithery

To install Multi Cluster Kubernetes Server for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@razvanmacovei/k8s-multicluster-mcp):

```bash
npx -y @smithery/cli install @razvanmacovei/k8s-multicluster-mcp --client claude
```

### Prerequisites
- Python 3.8 or higher
- pip package manager
- uv package manager (optional, recommended for faster installation)

### Setting up a Local Environment

1. Clone the repository
   ```bash
   git clone https://github.com/razvanmacovei/k8s-multicluster-mcp.git
   cd k8s-multicluster-mcp
   ```

2. Create a virtual environment
   ```bash
   # Using venv (built-in)
   python3 -m venv .venv
   
   # Activate the virtual environment
   # On Windows
   .venv\Scripts\activate
   
   # On macOS/Linux
   source .venv/bin/activate
   ```

3. Install dependencies
   ```bash
   # Using pip
   pip install -r requirements.txt
   
   # Or using uv (faster)
   uv pip install -r requirements.txt
   ```

4. Configure your environment
   - Make sure you have your kubeconfig files ready
   - Set the `KUBECONFIG_DIR` environment variable to point to your kubeconfig directory

5. Run the application
   ```bash
   python3 app.py
   ```


## Multi-Cluster Management

This MCP server is designed specifically to work with multiple Kubernetes clusters:

- **Multiple Kubeconfig Files**: Place your kubeconfig files in the directory specified by `KUBECONFIG_DIR`
- **Context Selection**: Easily switch between clusters by specifying the context parameter in your commands
- **Cross-Cluster Operations**: Compare resources, status, and configurations across different clusters
- **Centralized Management**: Manage all your Kubernetes environments (dev, staging, production) from a single interface

## Features

The Kubernetes MCP Server provides a comprehensive set of tools for interacting with Kubernetes clusters:

### Cluster Management

- List available Kubernetes contexts
- List namespaces and nodes in a cluster
- List and retrieve detailed information about Kubernetes resources
- Discover available APIs and Custom Resource Definitions (CRDs)

### Resource Management

- List and inspect any Kubernetes resource (pods, deployments, services, etc.)
- Get logs from pods
- Get detailed status information about deployments, statefulsets, and daemonsets
- Describe resources with detailed information similar to `kubectl describe`

### Metrics and Monitoring

- Display resource usage (CPU/memory) of nodes
- Display resource usage (CPU/memory) of pods
- Diagnose application issues by checking status, events, and logs

### Rollout Management

- Get rollout status and history
- Undo, restart, pause, and resume rollouts
- Scale and autoscale resources
- Update resource constraints (CPU/memory limits and requests)

## Usage Examples

Here are some examples of how to use the Kubernetes MCP Server with AI assistants:

### Multi-Cluster Operations

```
List all available contexts across my kubeconfig files.
```

```
Compare the number of pods running in the 'backend' namespace between my 'prod' and 'staging' contexts.
```

```
Show me resource usage across all nodes in my 'dev' and 'prod' clusters.
```

### Diagnose Application Issues

```
I have a deployment called 'my-app' in the 'production' namespace that's having issues. Can you check what's wrong?
```

### Scale Resources

```
I need to scale my 'backend' deployment in the 'default' namespace to 5 replicas.
```

### Investigate Resource Usage

```
Show me the resource usage of nodes in my cluster.
```

### Update Resource Limits

```
My application 'web-app' in namespace 'web' is experiencing OOM issues. Can you increase the memory limit of the 'app' container to 512Mi?
```

### Rollback Deployment

```
I need to rollback my 'api-gateway' deployment in the 'services' namespace to the previous version.
```

### Discover API Resources

```
What APIs are available in my Kubernetes cluster?
```

### Describe Resources

```
Can you describe the pod 'my-pod' in the 'default' namespace?
```

### Create New Resources

```Create a new deployment with the following YAML:
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
        image: nginx:1.21
        ports:
        - containerPort: 80
```

### Expose a Deployment

```
Expose my 'backend' deployment in the 'default' namespace as a service on port 80 targeting port 8080.
```

### Execute Command in a Pod

```
Execute the command 'ls -la /app' in the 'app' container of pod 'web-app-1234' in the 'default' namespace.
```


### Node Maintenance

```
I need to perform maintenance on node 'worker-1'. Please cordon it, drain it, and then uncordon it after I complete my work.
```

### Apply Configuration

```
Apply this configuration to update my existing deployment:
apiVersion: apps/v1
kind: Deployment
metadata:
  name: existing-deployment
  namespace: default
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: app
        image: myapp:v2
```

### Patch a Resource

```
Patch the 'my-configmap' ConfigMap in the 'default' namespace to add a new key 'NEW_SETTING' with value 'enabled'.
```

### Update Labels

```
Add the label 'environment=production' to the 'api' deployment in the 'backend' namespace.
```

## Implemented Tools

The server implements the following MCP tools:

### Core Tools

- `k8s_get_contexts`: List all available Kubernetes contexts
- `k8s_get_namespaces`: List all namespaces in a specified context
- `k8s_get_nodes`: List all nodes in a cluster
- `k8s_get_resources`: List resources of a specified kind
- `k8s_get_resource`: Get detailed information about a specific resource
- `k8s_get_pod_logs`: Get logs from a specific pod
- `k8s_describe`: Show detailed information about a specific resource or group of resources

### API Discovery Tools

- `k8s_apis`: List all available APIs in the Kubernetes cluster
- `k8s_crds`: List all Custom Resource Definitions (CRDs) in the cluster

### Metrics Tools

- `k8s_top_nodes`: Display resource usage of nodes
- `k8s_top_pods`: Display resource usage of pods

### Rollout Management Tools

- `k8s_rollout_status`: Get status of a rollout
- `k8s_rollout_history`: Get revision history of a rollout
- `k8s_rollout_undo`: Undo a rollout to a previous revision
- `k8s_rollout_restart`: Restart a rollout
- `k8s_rollout_pause`: Pause a rollout
- `k8s_rollout_resume`: Resume a paused rollout

### Scaling Tools

- `k8s_scale_resource`: Scale a resource to a specified number of replicas
- `k8s_autoscale_resource`: Configure a Horizontal Pod Autoscaler (HPA)
- `k8s_update_resources`: Update resource requests and limits

### Diagnostic Tools

- `k8s_diagnose_application`: Diagnose issues with an application

### Resource Creation and Management Tools

- `k8s_create_resource`: Create a Kubernetes resource from YAML/JSON content
- `k8s_apply_resource`: Apply a configuration to a resource (create or update)
- `k8s_patch_resource`: Update fields of a resource
- `k8s_label_resource`: Update the labels on a resource
- `k8s_annotate_resource`: Update the annotations on a resource

### Workload Management Tools

- `k8s_expose_resource`: Expose a resource as a new Kubernetes service
- `k8s_set_resources_for_container`: Set resource limits and requests for containers

### Node Management Tools

- `k8s_cordon_node`: Mark a node as unschedulable
- `k8s_uncordon_node`: Mark a node as schedulable
- `k8s_drain_node`: Drain a node in preparation for maintenance
- `k8s_taint_node`: Update the taints on a node
- `k8s_untaint_node`: Remove taints from a node

### Pod Operations Tools

- `k8s_pod_exec`: Execute a command in a container

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
