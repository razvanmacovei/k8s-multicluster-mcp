# Troubleshooting Guide

This guide helps you resolve common issues when using k8s-multicluster-mcp.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Configuration Issues](#configuration-issues)
- [Runtime Errors](#runtime-errors)
- [Kubernetes Connection Issues](#kubernetes-connection-issues)
- [Performance Issues](#performance-issues)

## Installation Issues

### "pipx: command not found"

**Problem**: The `pipx` command is not available on your system.

**Solution**:
- macOS: `brew install pipx`
- Ubuntu/Debian: `sudo apt install pipx`
- Other systems: `python3 -m pip install --user pipx`

Then ensure pipx is in your PATH:
```bash
pipx ensurepath
```

### "Python version not supported"

**Problem**: Your Python version is below 3.8.

**Solution**: Install Python 3.8 or higher:
- macOS: `brew install python@3.11`
- Ubuntu: `sudo apt install python3.11`
- Windows: Download from [python.org](https://www.python.org/)

## Configuration Issues

### "KUBECONFIG_DIR not set"

**Problem**: The environment variable `KUBECONFIG_DIR` is not configured.

**Solution**: Ensure your MCP client configuration includes the environment variable:
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

### "No kubeconfig files found"

**Problem**: The specified directory doesn't contain any kubeconfig files.

**Solution**:
1. Verify the path exists: `ls -la /path/to/your/kubeconfigs`
2. Ensure kubeconfig files are in the directory (not subdirectories)
3. Check file permissions: `chmod 600 /path/to/your/kubeconfigs/*`

### Multiple kubeconfig files with same context names

**Problem**: Different kubeconfig files contain contexts with identical names.

**Solution**: Rename contexts to be unique:
```bash
kubectl config rename-context old-name new-unique-name --kubeconfig=/path/to/config
```

## Runtime Errors

### "Connection refused" or "Unable to connect to the server"

**Problem**: Cannot connect to Kubernetes API server.

**Solutions**:
1. Check cluster is running: `kubectl cluster-info`
2. Verify credentials haven't expired
3. Check network connectivity to cluster
4. For cloud clusters, ensure VPN is connected if required

### "Unauthorized" errors

**Problem**: Authentication credentials are invalid or expired.

**Solutions**:
1. Refresh credentials:
   - AWS EKS: `aws eks update-kubeconfig --name cluster-name`
   - GKE: `gcloud container clusters get-credentials cluster-name`
   - Azure AKS: `az aks get-credentials --name cluster-name`
2. Check certificate expiration dates
3. Verify service account tokens are valid

### "The server does not have resource type"

**Problem**: Trying to access a resource that doesn't exist in the cluster.

**Solution**: 
- Check available resources: Use the `k8s_apis` tool to list available APIs
- Verify CRDs are installed if accessing custom resources

## Kubernetes Connection Issues

### Slow response times

**Problem**: Commands take a long time to execute.

**Solutions**:
1. Check network latency to clusters
2. Reduce number of resources being fetched
3. Use specific namespaces instead of `--all-namespaces`
4. Check if API server is under heavy load

### SSL/TLS certificate errors

**Problem**: Certificate verification failures.

**Solutions**:
1. Update cluster certificates if expired
2. Ensure system time is synchronized
3. For self-signed certificates, ensure they're properly trusted

### Context not found

**Problem**: Specified context doesn't exist in any kubeconfig.

**Solution**: List available contexts using the `k8s_get_contexts` tool first.

## Performance Issues

### High memory usage

**Problem**: The MCP server uses excessive memory.

**Solutions**:
1. Limit the number of resources fetched at once
2. Use namespace filters when possible
3. Avoid fetching logs for many pods simultaneously

### Timeout errors

**Problem**: Operations timeout before completing.

**Solutions**:
1. Increase timeout values if configurable
2. Break large operations into smaller chunks
3. Check cluster API server performance

## Debug Mode

To get more detailed error information, you can:

1. Check Claude Desktop logs
2. Run the command directly to see full output:
   ```bash
   KUBECONFIG_DIR=/path/to/configs pipx run k8s-multicluster-mcp
   ```

## Getting Help

If you're still experiencing issues:

1. Check existing [GitHub Issues](https://github.com/razvanmacovei/k8s_multicluster_mcp/issues)
2. Create a new issue with:
   - Detailed error messages
   - Steps to reproduce
   - Environment information
   - Kubeconfig setup (without sensitive data)

## Common Patterns

### Working with multiple clusters

When working with multiple clusters, context names must be unique across all kubeconfig files. Consider naming patterns like:
- `prod-aws-us-east-1`
- `dev-gke-europe-west1`
- `staging-aks-northeurope`

### Security Best Practices

1. Keep kubeconfig files with restricted permissions (600)
2. Don't commit kubeconfig files to version control
3. Regularly rotate credentials
4. Use separate kubeconfig files for different environments 