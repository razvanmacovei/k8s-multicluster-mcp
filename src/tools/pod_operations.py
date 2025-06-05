import json
import os
from typing import Any, Dict, List, Optional, Union

from kubernetes import client, stream
from kubernetes.client.rest import ApiException

from ..utils.k8s_client import KubernetesClient

# Initialize client with kubeconfig directory from environment or default
kubeconfig_dir = os.environ.get("KUBECONFIG_DIR", os.path.expanduser("~/.kube"))
k8s_client = KubernetesClient(kubeconfig_dir)


async def k8s_exec_command(
    context: str,
    pod_name: str,
    command: str,
    container: Optional[str] = None,
    namespace: Optional[str] = None,
    stdin: Optional[bool] = False,
    tty: Optional[bool] = False,
    timeout: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Execute a command in a container.

    Args:
        context (str): The Kubernetes context to use
        pod_name (str): The name of the pod to execute the command in
        command (str): The command to execute
        container (str, optional): The container to execute the command in (if not specified, the first container is used)
        namespace (str, optional): The namespace of the pod
        stdin (bool, optional): Whether to pass stdin to the container
        tty (bool, optional): Whether to allocate a TTY
        timeout (int, optional): The timeout for the command in seconds

    Returns:
        Dict[str, Any]: The output of the command

    Raises:
        RuntimeError: If there's an error executing the command
    """
    try:
        # Get the API client for the specified context
        api_client = k8s_client.get_api_client(context)
        api_instance = client.CoreV1Api(api_client)

        # Set default namespace if not provided
        namespace = namespace or "default"

        # If command is a string, split it into a list
        if isinstance(command, str):
            command = command.split()

        # If timeout is specified, set it
        if timeout:
            _request_timeout = timeout

        # Execute the command
        exec_result = stream.stream(
            api_instance.connect_get_namespaced_pod_exec,
            name=pod_name,
            namespace=namespace,
            container=container,
            command=command,
            stderr=True,
            stdin=stdin,
            stdout=True,
            tty=tty,
        )

        return {
            "status": "Success",
            "message": f"Command executed in pod '{pod_name}' container '{container or 'default'}'",
            "output": exec_result,
        }
    except ApiException as e:
        raise RuntimeError(f"Failed to execute command in pod '{pod_name}': {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error executing command in pod '{pod_name}': {str(e)}")
