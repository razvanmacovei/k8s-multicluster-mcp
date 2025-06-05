# Multi Cluster Kubernetes MCP Server

[![PyPI version](https://badge.fury.io/py/k8s-multicluster-mcp.svg)](https://badge.fury.io/py/k8s-multicluster-mcp)
[![Python versions](https://img.shields.io/pypi/pyversions/k8s-multicluster-mcp.svg)](https://pypi.org/project/k8s-multicluster-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/razvanmacovei/k8s_multicluster_mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/razvanmacovei/k8s_multicluster_mcp/actions/workflows/ci.yml)

An MCP (Model Context Protocol) server application for Kubernetes operations, providing a standardized API to interact with multiple Kubernetes clusters simultaneously using multiple kubeconfig files.

## 🚀 Quick Start

### 1. Install via pipx (Recommended)

The easiest way to use k8s-multicluster-mcp is with `pipx run`:

```bash
# Run directly without installation
pipx run k8s-multicluster-mcp
```

No installation required! Just configure your MCP client (e.g., Claude Desktop) by adding to `config.json`:

```json
{
  "mcpServers": {
    "kubernetes": {
      "command": "pipx",
      "args": ["run", "k8s-multicluster-mcp"],
      "env": {
        "KUBECONFIG_DIR": "/path/to/your/kubeconfigs"
      }
    }
  }
}
```

> **Note**: Replace `/path/to/your/kubeconfigs` with the actual path to your kubeconfig files directory.

The first time you use it, `pipx` will automatically download and install the package in an isolated environment.

## 📋 Prerequisites

- Python 3.10 or higher
- `pipx` installed (`brew install pipx` on macOS, or see [pipx installation](https://pipx.pypa.io/stable/installation/))
- One or more kubeconfig files in a directory
- kubectl (optional, for verification)

## 🎯 Features

The Kubernetes MCP Server provides a comprehensive set of tools for interacting with Kubernetes clusters:

### Multi-Cluster Management

This MCP server is designed specifically to work with multiple Kubernetes clusters:

- **Multiple Kubeconfig Files**: Place your kubeconfig files in the directory specified by `KUBECONFIG_DIR`
- **Context Selection**: Easily switch between clusters by specifying the context parameter in your commands
- **Cross-Cluster Operations**: Compare resources, status, and configurations across different clusters
- **Centralized Management**: Manage all your Kubernetes environments (dev, staging, production) from a single interface

### Core Capabilities

- **Cluster Management**: List contexts, namespaces, nodes, and resources
- **Resource Operations**: Create, update, patch, label, and annotate resources
- **Pod Operations**: Get logs, execute commands, and manage pod lifecycle
- **Rollout Management**: Deploy, rollback, pause, resume, and restart rollouts
- **Scaling**: Manual scaling and HPA configuration
- **Node Management**: Cordon, uncordon, drain, taint operations
- **Metrics & Monitoring**: Resource usage for nodes and pods
- **Diagnostics**: Application troubleshooting and health checks

## 📖 Usage Examples

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

### Create New Resources

```
Create a new deployment with the following YAML:
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

### Node Maintenance

```
I need to perform maintenance on node 'worker-1'. Please cordon it, drain it, and then uncordon it after I complete my work.
```

## 🛠️ Implemented Tools

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

## 🔧 Configuration

### Environment Variables

- `KUBECONFIG_DIR`: Directory containing your kubeconfig files (required)
- Individual kubeconfig files should be placed in this directory

### Version Pinning

To use a specific version, update your config:

```json
{
  "args": ["run", "k8s-multicluster-mcp==1.1.0"]
}
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastMCP](https://github.com/jlowin/fastmcp) for the MCP protocol implementation
- Uses the official [Kubernetes Python client](https://github.com/kubernetes-client/python)

## 📚 Resources

- [MCP Protocol Documentation](https://modelcontextprotocol.io/)
- [Kubernetes API Reference](https://kubernetes.io/docs/reference/kubernetes-api/)
- [Project Repository](https://github.com/razvanmacovei/k8s_multicluster_mcp)

## 📖 Additional Documentation

- [API Reference](docs/API_REFERENCE.md) - Complete list of all MCP tools and their parameters
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Common issues and solutions
- [Contributing Guide](CONTRIBUTING.md) - How to contribute to the project
- [Release Checklist](RELEASE_CHECKLIST.md) - For maintainers
