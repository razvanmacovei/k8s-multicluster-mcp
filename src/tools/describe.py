from typing import Dict, Any, List, Optional
import os
import json
from kubernetes import client
from ..utils.k8s_client import KubernetesClient

# Initialize client with kubeconfig directory from environment or default
kubeconfig_dir = os.environ.get("KUBECONFIG_DIR", os.path.expanduser("~/.kube"))
k8s_client = KubernetesClient(kubeconfig_dir)


async def describe_k8s_resource(
    context: str,
    resource_type: str,
    name: Optional[str] = None,
    namespace: Optional[str] = None,
    selector: Optional[str] = None,
    all_namespaces: bool = False,
) -> Dict[str, Any]:
    """
    Show detailed information about a specific resource or group of resources
    using the Kubernetes Python client instead of kubectl.

    Supported resource types:
    - Core resources: pod, service, namespace, node, secret, configmap, persistentvolume,
      persistentvolumeclaim, serviceaccount, endpoint
    - Apps resources: deployment, statefulset, daemonset, replicaset
    - Networking resources: ingress
    - Batch resources: job, cronjob

    Args:
        context (str): Name of the Kubernetes context to use
        resource_type (str): Type of resource to describe (e.g., pod, deployment, service)
        name (str, optional): Name of the resource to describe
        namespace (str, optional): Namespace of the resource(s)
        selector (str, optional): Label selector to filter resources
        all_namespaces (bool, optional): If True, include resources across all namespaces

    Returns:
        Dict[str, Any]: Detailed information about the resource(s)

    Raises:
        RuntimeError: If there's an error accessing the Kubernetes API
    """
    try:
        # Get API client for the context
        api_client = k8s_client.get_api_client(context)

        # Create result structure
        result = {"resource_type": resource_type, "context": context}

        # Add optional parameters to result if provided
        if namespace and not all_namespaces:
            result["namespace"] = namespace
        elif all_namespaces:
            result["namespace"] = "all"

        if name:
            result["name"] = name
        if selector:
            result["selector"] = selector

        # Get structured information using the K8s API
        structured_info = await _get_structured_resource_info(
            api_client, resource_type, name, namespace, selector, all_namespaces
        )

        # Add structured information to result
        result.update(structured_info)

        # Generate a human-readable description similar to kubectl describe
        result["description"] = await _generate_description(structured_info, resource_type, name, namespace)

        return result

    except Exception as e:
        raise RuntimeError(f"Failed to describe {resource_type}: {str(e)}")


async def _generate_description(
    info: Dict[str, Any], resource_type: str, name: Optional[str] = None, namespace: Optional[str] = None
) -> Dict[str, str]:
    """
    Generate a human-readable description from structured information.

    Args:
        info (Dict[str, Any]): Structured resource information
        resource_type (str): Type of resource
        name (str, optional): Name of the resource
        namespace (str, optional): Namespace of the resource

    Returns:
        Dict[str, str]: Sections of description text
    """
    sections = {}

    # Process each item in the structured info
    if "items" in info and info["items"]:
        for i, item in enumerate(info["items"]):
            # Generate a title for this item
            if len(info["items"]) > 1:
                item_title = f"{resource_type.capitalize()} {i+1}: {item.get('name', 'unknown')}"
            else:
                item_title = f"{resource_type.capitalize()}: {item.get('name', 'unknown')}"

            # Extract basic information
            sections[item_title] = ""

            # Add namespace if available
            if "namespace" in item:
                sections[item_title] += f"Namespace:               {item['namespace']}\n"

            # Add common metadata
            sections[item_title] += _format_basic_info(item)

            # Add resource-specific sections
            if resource_type.lower() == "pod":
                sections[f"Status for {item.get('name', 'unknown')}"] = _format_pod_status(item)
                sections[f"Containers for {item.get('name', 'unknown')}"] = _format_containers(item)
                sections[f"Volumes for {item.get('name', 'unknown')}"] = _format_volumes(item)

            elif resource_type.lower() == "service":
                sections[f"Service Details for {item.get('name', 'unknown')}"] = _format_service_info(item)

            elif resource_type.lower() == "deployment":
                sections[f"Deployment Status for {item.get('name', 'unknown')}"] = _format_deployment_status(item)

            elif resource_type.lower() == "node":
                sections[f"Node Status for {item.get('name', 'unknown')}"] = _format_node_status(item)
                sections[f"Node Resources for {item.get('name', 'unknown')}"] = _format_node_resources(item)

            elif resource_type.lower() == "daemonset":
                sections[f"DaemonSet Status for {item.get('name', 'unknown')}"] = _format_daemonset_status(item)

            elif resource_type.lower() == "replicaset":
                sections[f"ReplicaSet Status for {item.get('name', 'unknown')}"] = _format_replicaset_status(item)

            elif resource_type.lower() == "configmap":
                sections[f"ConfigMap Data for {item.get('name', 'unknown')}"] = _format_configmap_data(item)

            elif resource_type.lower() == "secret":
                sections[f"Secret Data for {item.get('name', 'unknown')}"] = _format_secret_data(item)

            elif resource_type.lower() == "namespace":
                sections[f"Namespace Status for {item.get('name', 'unknown')}"] = _format_namespace_status(item)

            elif resource_type.lower() == "persistentvolume":
                sections[f"PersistentVolume Details for {item.get('name', 'unknown')}"] = _format_pv_info(item)

            elif resource_type.lower() == "persistentvolumeclaim":
                sections[f"PersistentVolumeClaim Details for {item.get('name', 'unknown')}"] = _format_pvc_info(item)

            elif resource_type.lower() == "ingress":
                sections[f"Ingress Details for {item.get('name', 'unknown')}"] = _format_ingress_info(item)

            elif resource_type.lower() == "job":
                sections[f"Job Details for {item.get('name', 'unknown')}"] = _format_job_info(item)

            elif resource_type.lower() == "cronjob":
                sections[f"CronJob Details for {item.get('name', 'unknown')}"] = _format_cronjob_info(item)

            # Add conditions if available
            if "conditions" in item or ("status" in item and "conditions" in item["status"]):
                conditions = item.get("conditions", item.get("status", {}).get("conditions", []))
                if conditions:
                    sections[f"Conditions for {item.get('name', 'unknown')}"] = _format_conditions(conditions)

    # If no items were found
    if not sections and "error" in info:
        sections["Error"] = info["error"]
    elif not sections and "message" in info:
        sections["Message"] = info["message"]
    elif not sections:
        sections["Info"] = "No resources found"

    return sections


def _format_basic_info(item: Dict[str, Any]) -> str:
    """Format basic information about a resource."""
    result = ""

    # Add creation timestamp if available
    if "creation_timestamp" in item:
        result += f"Creation Timestamp:      {item['creation_timestamp']}\n"

    # Add labels if available
    if "labels" in item and item["labels"]:
        result += "Labels:                 "
        for i, (key, value) in enumerate(item["labels"].items()):
            if i > 0:
                result += "                       "
            result += f"{key}={value}\n"

    # Add annotations if available
    if "annotations" in item and item["annotations"]:
        result += "Annotations:            "
        for i, (key, value) in enumerate(item["annotations"].items()):
            if i > 0:
                result += "                       "
            result += f"{key}={value}\n"

    return result


def _format_pod_status(pod: Dict[str, Any]) -> str:
    """Format pod status information."""
    result = ""
    status = pod.get("status_phase", "Unknown")
    result += f"Status:                 {status}\n"

    if "node" in pod:
        result += f"Node:                   {pod['node']}\n"
    if "ip" in pod:
        result += f"IP:                     {pod['ip']}\n"
    if "start_time" in pod:
        result += f"Start Time:             {pod['start_time']}\n"

    return result


def _format_containers(pod: Dict[str, Any]) -> str:
    """Format container information for a pod."""
    result = ""

    for container in pod.get("containers", []):
        result += f"Container: {container.get('name', 'unknown')}\n"
        result += f"  Image:        {container.get('image', 'unknown')}\n"

        # Add ports if available
        if "ports" in container and container["ports"]:
            result += "  Ports:\n"
            for port in container["ports"]:
                result += f"    {port.get('container_port', 'unknown')}/{port.get('protocol', 'TCP')}\n"

        # Add resources if available
        if "resources" in container and container["resources"]:
            result += "  Resources:\n"
            if "requests" in container["resources"] and container["resources"]["requests"]:
                result += "    Requests:\n"
                for resource, value in container["resources"]["requests"].items():
                    result += f"      {resource}: {value}\n"
            if "limits" in container["resources"] and container["resources"]["limits"]:
                result += "    Limits:\n"
                for resource, value in container["resources"]["limits"].items():
                    result += f"      {resource}: {value}\n"

        result += "\n"

    return result


def _format_volumes(pod: Dict[str, Any]) -> str:
    """Format volume information for a pod."""
    result = ""

    for volume in pod.get("volumes", []):
        result += f"Volume: {volume.get('name', 'unknown')}\n"
        result += f"  Type: {volume.get('type', 'unknown')}\n"
        result += "\n"

    return result


def _format_service_info(service: Dict[str, Any]) -> str:
    """Format service information."""
    result = ""

    result += f"Type:                   {service.get('type', 'unknown')}\n"
    result += f"ClusterIP:              {service.get('cluster_ip', 'unknown')}\n"

    if "external_ips" in service and service["external_ips"]:
        result += f"External IPs:           {', '.join(service['external_ips'])}\n"

    if "ports" in service and service["ports"]:
        result += "Ports:\n"
        for port in service["ports"]:
            result += f"  {port.get('name', '')} {port.get('port', 'unknown')}/{port.get('protocol', 'TCP')}"
            if "target_port" in port:
                result += f" -> {port['target_port']}"
            if "node_port" in port and port["node_port"]:
                result += f" (NodePort: {port['node_port']})"
            result += "\n"

    if "selector" in service and service["selector"]:
        result += "Selector:               "
        for i, (key, value) in enumerate(service["selector"].items()):
            if i > 0:
                result += "                       "
            result += f"{key}={value}\n"

    return result


def _format_deployment_status(deployment: Dict[str, Any]) -> str:
    """Format deployment status information."""
    result = ""

    result += f"Replicas:               {deployment.get('replicas', 'unknown')}\n"
    result += f"Strategy:               {deployment.get('strategy', 'unknown')}\n"

    if "status" in deployment:
        status = deployment["status"]
        result += "Status:\n"
        result += f"  Ready Replicas:      {status.get('ready_replicas', 0)}\n"
        result += f"  Updated Replicas:    {status.get('updated_replicas', 0)}\n"
        result += f"  Available Replicas:  {status.get('available_replicas', 0)}\n"

        if "unavailable_replicas" in status and status["unavailable_replicas"]:
            result += f"  Unavailable:         {status['unavailable_replicas']}\n"

    if "selector" in deployment and deployment["selector"]:
        result += "Selector:               "
        for i, (key, value) in enumerate(deployment["selector"].items()):
            if i > 0:
                result += "                       "
            result += f"{key}={value}\n"

    return result


def _format_node_status(node: Dict[str, Any]) -> str:
    """Format node status information."""
    result = ""

    if "status" in node and "addresses" in node["status"]:
        result += "Addresses:\n"
        for address in node["status"]["addresses"]:
            result += f"  {address.get('type', 'unknown')}: {address.get('address', 'unknown')}\n"

    if "spec" in node and "taints" in node["spec"] and node["spec"]["taints"]:
        result += "Taints:\n"
        for taint in node["spec"]["taints"]:
            result += (
                f"  {taint.get('key', 'unknown')}={taint.get('value', 'unknown')}:{taint.get('effect', 'unknown')}\n"
            )

    return result


def _format_node_resources(node: Dict[str, Any]) -> str:
    """Format node resource information."""
    result = ""

    if "status" in node:
        if "capacity" in node["status"]:
            result += "Capacity:\n"
            for resource, value in node["status"]["capacity"].items():
                result += f"  {resource}: {value}\n"

        if "allocatable" in node["status"]:
            result += "Allocatable:\n"
            for resource, value in node["status"]["allocatable"].items():
                result += f"  {resource}: {value}\n"

    return result


def _format_daemonset_status(daemonset: Dict[str, Any]) -> str:
    """Format daemonset status information."""
    result = ""

    result += f"Desired Number:         {daemonset.get('desired_number', 'unknown')}\n"
    result += f"Update Strategy:        {daemonset.get('update_strategy', 'unknown')}\n"

    if "status" in daemonset:
        status = daemonset["status"]
        result += "Status:\n"
        result += f"  Current Number:      {status.get('current_number', 0)}\n"
        result += f"  Ready Number:        {status.get('ready_number', 0)}\n"
        result += f"  Updated Number:      {status.get('updated_number', 0)}\n"
        result += f"  Available Number:    {status.get('available_number', 0)}\n"

    if "selector" in daemonset and daemonset["selector"]:
        result += "Selector:               "
        for i, (key, value) in enumerate(daemonset["selector"].items()):
            if i > 0:
                result += "                       "
            result += f"{key}={value}\n"

    return result


def _format_replicaset_status(replicaset: Dict[str, Any]) -> str:
    """Format replicaset status information."""
    result = ""

    result += f"Replicas:               {replicaset.get('replicas', 'unknown')}\n"

    if "status" in replicaset:
        status = replicaset["status"]
        result += "Status:\n"
        result += f"  Ready Replicas:      {status.get('ready_replicas', 0)}\n"
        result += f"  Available Replicas:  {status.get('available_replicas', 0)}\n"

        if "fully_labeled_replicas" in status:
            result += f"  Fully Labeled:       {status['fully_labeled_replicas']}\n"

    if "selector" in replicaset and replicaset["selector"]:
        result += "Selector:               "
        for i, (key, value) in enumerate(replicaset["selector"].items()):
            if i > 0:
                result += "                       "
            result += f"{key}={value}\n"

    if "pod_template_hash" in replicaset:
        result += f"Pod Template Hash:      {replicaset['pod_template_hash']}\n"

    return result


def _format_configmap_data(configmap: Dict[str, Any]) -> str:
    """Format configmap data."""
    result = ""

    if "data" in configmap and configmap["data"]:
        result += "Data:\n"
        for key, value in configmap["data"].items():
            result += f"  {key}: "
            # Limit output for large values
            if len(str(value)) > 100:
                result += f"{str(value)[:100]}...\n"
            else:
                result += f"{value}\n"

    if "binary_data" in configmap and configmap["binary_data"]:
        result += "Binary Data:\n"
        for key in configmap["binary_data"].keys():
            result += f"  {key}: <binary data>\n"

    return result


def _format_secret_data(secret: Dict[str, Any]) -> str:
    """Format secret data (without revealing it)."""
    result = ""

    result += f"Type:                   {secret.get('type', 'unknown')}\n"

    if "data" in secret and secret["data"]:
        result += "Data:\n"
        for key in secret["data"].keys():
            result += f"  {key}: <sensitive data>\n"

    return result


def _format_namespace_status(namespace: Dict[str, Any]) -> str:
    """Format namespace status information."""
    result = ""

    result += f"Status:                 {namespace.get('status', 'unknown')}\n"

    if "resource_quota" in namespace and namespace["resource_quota"]:
        result += "Resource Quotas:\n"
        for quota in namespace["resource_quota"]:
            result += f"  {quota.get('name', 'unknown')}:\n"
            if "hard" in quota:
                result += "    Hard:\n"
                for resource, value in quota["hard"].items():
                    result += f"      {resource}: {value}\n"

    if "limit_range" in namespace and namespace["limit_range"]:
        result += "Limit Ranges:\n"
        for limit in namespace["limit_range"]:
            result += f"  {limit.get('name', 'unknown')}\n"

    return result


def _format_pv_info(pv: Dict[str, Any]) -> str:
    """Format persistent volume information."""
    result = ""

    result += f"Status:                 {pv.get('status', 'unknown')}\n"
    result += f"Capacity:               {pv.get('capacity', {}).get('storage', 'unknown')}\n"
    result += f"Access Modes:           {', '.join(pv.get('access_modes', []))}\n"
    result += f"Storage Class:          {pv.get('storage_class', 'unknown')}\n"
    result += f"Reclaim Policy:         {pv.get('reclaim_policy', 'unknown')}\n"

    if "claim_ref" in pv and pv["claim_ref"]:
        claim = pv["claim_ref"]
        result += "Claim:\n"
        result += f"  Namespace:   {claim.get('namespace', 'unknown')}\n"
        result += f"  Name:        {claim.get('name', 'unknown')}\n"

    if "source" in pv and pv["source"]:
        result += "Source:\n"
        for source_type, source_value in pv["source"].items():
            if isinstance(source_value, dict):
                result += f"  {source_type}:\n"
                for key, value in source_value.items():
                    result += f"    {key}: {value}\n"
            else:
                result += f"  {source_type}: {source_value}\n"

    return result


def _format_pvc_info(pvc: Dict[str, Any]) -> str:
    """Format persistent volume claim information."""
    result = ""

    result += f"Status:                 {pvc.get('status', 'unknown')}\n"
    result += f"Volume:                 {pvc.get('volume_name', 'unknown')}\n"
    result += f"Capacity:               {pvc.get('capacity', {}).get('storage', 'unknown')}\n"
    result += f"Access Modes:           {', '.join(pvc.get('access_modes', []))}\n"
    result += f"Storage Class:          {pvc.get('storage_class', 'unknown')}\n"

    if "volume_mode" in pvc:
        result += f"Volume Mode:            {pvc['volume_mode']}\n"

    return result


def _format_ingress_info(ingress: Dict[str, Any]) -> str:
    """Format ingress information."""
    result = ""

    result += f"Class:                  {ingress.get('ingress_class', 'unknown')}\n"

    if "rules" in ingress and ingress["rules"]:
        result += "Rules:\n"
        for rule in ingress["rules"]:
            if "host" in rule:
                result += f"  Host: {rule['host']}\n"
            if "http" in rule and "paths" in rule["http"]:
                for path in rule["http"]["paths"]:
                    result += f"    Path: {path.get('path', '/')}\n"
                    result += f"    Path Type: {path.get('path_type', 'Prefix')}\n"
                    if "backend" in path:
                        backend = path["backend"]
                        if "service" in backend:
                            service = backend["service"]
                            result += f"    Backend: service={service.get('name', 'unknown')}, "
                            if "port" in service:
                                port = service["port"]
                                if "number" in port:
                                    result += f"port={port['number']}\n"
                                elif "name" in port:
                                    result += f"port={port['name']}\n"
                                else:
                                    result += "\n"
                            else:
                                result += "\n"

    if "tls" in ingress and ingress["tls"]:
        result += "TLS:\n"
        for tls in ingress["tls"]:
            result += f"  Hosts: {', '.join(tls.get('hosts', []))}\n"
            result += f"  Secret Name: {tls.get('secret_name', 'unknown')}\n"

    return result


def _format_job_info(job: Dict[str, Any]) -> str:
    """Format job information."""
    result = ""

    result += f"Completions:            {job.get('completions', 'unknown')}\n"
    result += f"Parallelism:            {job.get('parallelism', 'unknown')}\n"

    if "status" in job:
        status = job["status"]
        result += "Status:\n"
        result += f"  Active:               {status.get('active', 0)}\n"
        result += f"  Succeeded:            {status.get('succeeded', 0)}\n"
        result += f"  Failed:               {status.get('failed', 0)}\n"

        if "start_time" in status:
            result += f"Start Time:             {status['start_time']}\n"

        if "completion_time" in status:
            result += f"Completion Time:        {status['completion_time']}\n"

    return result


def _format_cronjob_info(cronjob: Dict[str, Any]) -> str:
    """Format cronjob information."""
    result = ""

    result += f"Schedule:               {cronjob.get('schedule', 'unknown')}\n"
    result += f"Concurrency Policy:     {cronjob.get('concurrency_policy', 'unknown')}\n"
    result += f"Suspend:                {cronjob.get('suspend', False)}\n"

    if "last_schedule_time" in cronjob:
        result += f"Last Schedule Time:     {cronjob['last_schedule_time']}\n"

    if "active_jobs" in cronjob and cronjob["active_jobs"]:
        result += "Active Jobs:\n"
        for job in cronjob["active_jobs"]:
            result += f"  {job.get('name', 'unknown')}\n"

    return result


def _format_conditions(conditions: List[Dict[str, Any]]) -> str:
    """Format conditions information."""
    result = ""

    for condition in conditions:
        result += f"Type:                {condition.get('type', 'unknown')}\n"
        result += f"Status:              {condition.get('status', 'unknown')}\n"

        if "reason" in condition:
            result += f"Reason:              {condition['reason']}\n"
        if "message" in condition:
            result += f"Message:             {condition['message']}\n"

        result += "\n"

    return result


async def _get_structured_resource_info(
    api_client,
    resource_type: str,
    name: Optional[str] = None,
    namespace: Optional[str] = None,
    selector: Optional[str] = None,
    all_namespaces: bool = False,
) -> Dict[str, Any]:
    """
    Helper function to get structured information about resources using the K8s API.

    Returns:
        Dict[str, Any]: Structured resource information
    """
    # Normalize resource type (remove plural forms if present)
    resource_type = resource_type.lower()
    if resource_type.endswith("s") and resource_type not in ["access", "endpoints", "status"]:
        resource_type = resource_type[:-1]

    # Initialize appropriate API client based on resource type
    result = {"items": []}

    try:
        # Handle core resources
        if resource_type in [
            "pod",
            "service",
            "namespace",
            "node",
            "secret",
            "configmap",
            "persistentvolume",
            "persistentvolumeclaim",
            "serviceaccount",
            "endpoint",
        ]:
            core_v1 = client.CoreV1Api(api_client)

            # Handle different resource types
            if resource_type == "pod":
                if name and namespace:
                    item = core_v1.read_namespaced_pod(name, namespace)
                    result["items"] = [_extract_pod_info(item)]
                elif namespace and not all_namespaces:
                    pods = core_v1.list_namespaced_pod(namespace, label_selector=selector)
                    result["items"] = [_extract_pod_info(pod) for pod in pods.items]
                else:
                    pods = core_v1.list_pod_for_all_namespaces(label_selector=selector)
                    result["items"] = [_extract_pod_info(pod) for pod in pods.items]

            elif resource_type == "service":
                if name and namespace:
                    item = core_v1.read_namespaced_service(name, namespace)
                    result["items"] = [_extract_service_info(item)]
                elif namespace and not all_namespaces:
                    services = core_v1.list_namespaced_service(namespace, label_selector=selector)
                    result["items"] = [_extract_service_info(svc) for svc in services.items]
                else:
                    services = core_v1.list_service_for_all_namespaces(label_selector=selector)
                    result["items"] = [_extract_service_info(svc) for svc in services.items]

            elif resource_type == "node":
                if name:
                    item = core_v1.read_node(name)
                    result["items"] = [_extract_node_info(item)]
                else:
                    nodes = core_v1.list_node(label_selector=selector)
                    result["items"] = [_extract_node_info(node) for node in nodes.items]

            elif resource_type == "configmap":
                if name and namespace:
                    item = core_v1.read_namespaced_config_map(name, namespace)
                    result["items"] = [_extract_configmap_info(item)]
                elif namespace and not all_namespaces:
                    configmaps = core_v1.list_namespaced_config_map(namespace, label_selector=selector)
                    result["items"] = [_extract_configmap_info(cm) for cm in configmaps.items]
                else:
                    configmaps = core_v1.list_config_map_for_all_namespaces(label_selector=selector)
                    result["items"] = [_extract_configmap_info(cm) for cm in configmaps.items]

            elif resource_type == "secret":
                if name and namespace:
                    item = core_v1.read_namespaced_secret(name, namespace)
                    result["items"] = [_extract_secret_info(item)]
                elif namespace and not all_namespaces:
                    secrets = core_v1.list_namespaced_secret(namespace, label_selector=selector)
                    result["items"] = [_extract_secret_info(secret) for secret in secrets.items]
                else:
                    secrets = core_v1.list_secret_for_all_namespaces(label_selector=selector)
                    result["items"] = [_extract_secret_info(secret) for secret in secrets.items]

            elif resource_type == "namespace":
                if name:
                    item = core_v1.read_namespace(name)
                    result["items"] = [_extract_namespace_info(item)]
                else:
                    namespaces = core_v1.list_namespace(label_selector=selector)
                    result["items"] = [_extract_namespace_info(ns) for ns in namespaces.items]

            elif resource_type == "persistentvolume":
                if name:
                    item = core_v1.read_persistent_volume(name)
                    result["items"] = [_extract_pv_info(item)]
                else:
                    pvs = core_v1.list_persistent_volume(label_selector=selector)
                    result["items"] = [_extract_pv_info(pv) for pv in pvs.items]

            elif resource_type == "persistentvolumeclaim":
                if name and namespace:
                    item = core_v1.read_namespaced_persistent_volume_claim(name, namespace)
                    result["items"] = [_extract_pvc_info(item)]
                elif namespace and not all_namespaces:
                    pvcs = core_v1.list_namespaced_persistent_volume_claim(namespace, label_selector=selector)
                    result["items"] = [_extract_pvc_info(pvc) for pvc in pvcs.items]
                else:
                    pvcs = core_v1.list_persistent_volume_claim_for_all_namespaces(label_selector=selector)
                    result["items"] = [_extract_pvc_info(pvc) for pvc in pvcs.items]

        # Handle apps resources
        elif resource_type in ["deployment", "statefulset", "daemonset", "replicaset"]:
            apps_v1 = client.AppsV1Api(api_client)

            if resource_type == "deployment":
                if name and namespace:
                    item = apps_v1.read_namespaced_deployment(name, namespace)
                    result["items"] = [_extract_deployment_info(item)]
                elif namespace and not all_namespaces:
                    deployments = apps_v1.list_namespaced_deployment(namespace, label_selector=selector)
                    result["items"] = [_extract_deployment_info(dep) for dep in deployments.items]
                else:
                    deployments = apps_v1.list_deployment_for_all_namespaces(label_selector=selector)
                    result["items"] = [_extract_deployment_info(dep) for dep in deployments.items]

            elif resource_type == "statefulset":
                if name and namespace:
                    item = apps_v1.read_namespaced_stateful_set(name, namespace)
                    result["items"] = [_extract_statefulset_info(item)]
                elif namespace and not all_namespaces:
                    statefulsets = apps_v1.list_namespaced_stateful_set(namespace, label_selector=selector)
                    result["items"] = [_extract_statefulset_info(sts) for sts in statefulsets.items]
                else:
                    statefulsets = apps_v1.list_stateful_set_for_all_namespaces(label_selector=selector)
                    result["items"] = [_extract_statefulset_info(sts) for sts in statefulsets.items]

            elif resource_type == "daemonset":
                if name and namespace:
                    item = apps_v1.read_namespaced_daemon_set(name, namespace)
                    result["items"] = [_extract_daemonset_info(item)]
                elif namespace and not all_namespaces:
                    daemonsets = apps_v1.list_namespaced_daemon_set(namespace, label_selector=selector)
                    result["items"] = [_extract_daemonset_info(ds) for ds in daemonsets.items]
                else:
                    daemonsets = apps_v1.list_daemon_set_for_all_namespaces(label_selector=selector)
                    result["items"] = [_extract_daemonset_info(ds) for ds in daemonsets.items]

            elif resource_type == "replicaset":
                if name and namespace:
                    item = apps_v1.read_namespaced_replica_set(name, namespace)
                    result["items"] = [_extract_replicaset_info(item)]
                elif namespace and not all_namespaces:
                    replicasets = apps_v1.list_namespaced_replica_set(namespace, label_selector=selector)
                    result["items"] = [_extract_replicaset_info(rs) for rs in replicasets.items]
                else:
                    replicasets = apps_v1.list_replica_set_for_all_namespaces(label_selector=selector)
                    result["items"] = [_extract_replicaset_info(rs) for rs in replicasets.items]

        # Handle networking resources
        elif resource_type == "ingress":
            networking_v1 = client.NetworkingV1Api(api_client)

            if name and namespace:
                item = networking_v1.read_namespaced_ingress(name, namespace)
                result["items"] = [_extract_ingress_info(item)]
            elif namespace and not all_namespaces:
                ingresses = networking_v1.list_namespaced_ingress(namespace, label_selector=selector)
                result["items"] = [_extract_ingress_info(ing) for ing in ingresses.items]
            else:
                ingresses = networking_v1.list_ingress_for_all_namespaces(label_selector=selector)
                result["items"] = [_extract_ingress_info(ing) for ing in ingresses.items]

        # Handle batch resources
        elif resource_type in ["job", "cronjob"]:
            batch_v1 = client.BatchV1Api(api_client)

            if resource_type == "job":
                if name and namespace:
                    item = batch_v1.read_namespaced_job(name, namespace)
                    result["items"] = [_extract_job_info(item)]
                elif namespace and not all_namespaces:
                    jobs = batch_v1.list_namespaced_job(namespace, label_selector=selector)
                    result["items"] = [_extract_job_info(job) for job in jobs.items]
                else:
                    jobs = batch_v1.list_job_for_all_namespaces(label_selector=selector)
                    result["items"] = [_extract_job_info(job) for job in jobs.items]

            elif resource_type == "cronjob":
                if name and namespace:
                    item = batch_v1.read_namespaced_cron_job(name, namespace)
                    result["items"] = [_extract_cronjob_info(item)]
                elif namespace and not all_namespaces:
                    cronjobs = batch_v1.list_namespaced_cron_job(namespace, label_selector=selector)
                    result["items"] = [_extract_cronjob_info(cj) for cj in cronjobs.items]
                else:
                    cronjobs = batch_v1.list_cron_job_for_all_namespaces(label_selector=selector)
                    result["items"] = [_extract_cronjob_info(cj) for cj in cronjobs.items]

        # For other resources, use the custom objects API if possible
        else:
            result["message"] = f"Structured data not available for resource type '{resource_type}'"

    except Exception as e:
        result["error"] = str(e)

    return result


def _extract_pod_info(pod) -> Dict[str, Any]:
    """Extract key information from a pod object."""
    return {
        "name": pod.metadata.name,
        "namespace": pod.metadata.namespace,
        "status_phase": pod.status.phase,
        "node": pod.spec.node_name,
        "ip": pod.status.pod_ip,
        "start_time": pod.status.start_time.isoformat() if pod.status.start_time else None,
        "containers": [
            {
                "name": container.name,
                "image": container.image,
                "ports": [
                    {"container_port": port.container_port, "protocol": port.protocol}
                    for port in (container.ports or [])
                ],
                "resources": (
                    {
                        "requests": container.resources.requests if hasattr(container.resources, "requests") else {},
                        "limits": container.resources.limits if hasattr(container.resources, "limits") else {},
                    }
                    if container.resources
                    else {}
                ),
            }
            for container in pod.spec.containers
        ],
        "conditions": [
            {"type": condition.type, "status": condition.status, "reason": condition.reason}
            for condition in (pod.status.conditions or [])
        ],
        "volumes": [
            {"name": volume.name, "type": _determine_volume_type(volume)} for volume in (pod.spec.volumes or [])
        ],
    }


def _extract_service_info(svc) -> Dict[str, Any]:
    """Extract key information from a service object."""
    return {
        "name": svc.metadata.name,
        "namespace": svc.metadata.namespace,
        "type": svc.spec.type,
        "cluster_ip": svc.spec.cluster_ip,
        "external_ips": svc.spec.external_i_ps if hasattr(svc.spec, "external_i_ps") else [],
        "ports": [
            {
                "name": port.name,
                "protocol": port.protocol,
                "port": port.port,
                "target_port": port.target_port,
                "node_port": port.node_port if hasattr(port, "node_port") else None,
            }
            for port in (svc.spec.ports or [])
        ],
        "selector": svc.spec.selector or {},
    }


def _extract_node_info(node) -> Dict[str, Any]:
    """Extract key information from a node object."""
    return {
        "name": node.metadata.name,
        "labels": node.metadata.labels or {},
        "status": {
            "capacity": node.status.capacity,
            "allocatable": node.status.allocatable,
            "conditions": [
                {
                    "type": condition.type,
                    "status": condition.status,
                    "reason": condition.reason,
                    "message": condition.message,
                }
                for condition in (node.status.conditions or [])
            ],
            "addresses": [{"type": addr.type, "address": addr.address} for addr in (node.status.addresses or [])],
        },
        "spec": {
            "pod_cidr": node.spec.pod_cidr if hasattr(node.spec, "pod_cidr") else None,
            "taints": (
                [{"key": taint.key, "value": taint.value, "effect": taint.effect} for taint in (node.spec.taints or [])]
                if hasattr(node.spec, "taints")
                else []
            ),
        },
    }


def _extract_deployment_info(deployment) -> Dict[str, Any]:
    """Extract key information from a deployment object."""
    return {
        "name": deployment.metadata.name,
        "namespace": deployment.metadata.namespace,
        "replicas": deployment.spec.replicas,
        "strategy": deployment.spec.strategy.type if deployment.spec.strategy else None,
        "selector": deployment.spec.selector.match_labels if deployment.spec.selector else {},
        "status": {
            "replicas": deployment.status.replicas,
            "ready_replicas": deployment.status.ready_replicas,
            "updated_replicas": deployment.status.updated_replicas,
            "available_replicas": deployment.status.available_replicas,
            "unavailable_replicas": deployment.status.unavailable_replicas,
            "conditions": (
                [
                    {
                        "type": condition.type,
                        "status": condition.status,
                        "reason": condition.reason,
                        "message": condition.message,
                    }
                    for condition in (deployment.status.conditions or [])
                ]
                if deployment.status.conditions
                else []
            ),
        },
    }


def _extract_statefulset_info(statefulset) -> Dict[str, Any]:
    """Extract key information from a statefulset object."""
    return {
        "name": statefulset.metadata.name,
        "namespace": statefulset.metadata.namespace,
        "replicas": statefulset.spec.replicas,
        "service_name": statefulset.spec.service_name,
        "selector": statefulset.spec.selector.match_labels if statefulset.spec.selector else {},
        "update_strategy": (
            statefulset.spec.update_strategy.type if hasattr(statefulset.spec, "update_strategy") else None
        ),
        "status": {
            "replicas": statefulset.status.replicas,
            "ready_replicas": statefulset.status.ready_replicas,
            "current_replicas": statefulset.status.current_replicas,
            "updated_replicas": statefulset.status.updated_replicas,
            "conditions": (
                [
                    {
                        "type": condition.type,
                        "status": condition.status,
                        "reason": condition.reason,
                        "message": condition.message,
                    }
                    for condition in (statefulset.status.conditions or [])
                ]
                if hasattr(statefulset.status, "conditions") and statefulset.status.conditions
                else []
            ),
        },
    }


def _extract_daemonset_info(daemonset) -> Dict[str, Any]:
    """Extract key information from a daemonset object."""
    return {
        "name": daemonset.metadata.name,
        "namespace": daemonset.metadata.namespace,
        "desired_number": daemonset.status.desired_number_scheduled,
        "update_strategy": daemonset.spec.update_strategy.type if hasattr(daemonset.spec, "update_strategy") else None,
        "selector": daemonset.spec.selector.match_labels if daemonset.spec.selector else {},
        "status": {
            "current_number": daemonset.status.current_number_scheduled,
            "ready_number": daemonset.status.number_ready,
            "updated_number": daemonset.status.updated_number_scheduled,
            "available_number": daemonset.status.number_available,
            "conditions": (
                [
                    {
                        "type": condition.type,
                        "status": condition.status,
                        "reason": condition.reason,
                        "message": condition.message,
                    }
                    for condition in (daemonset.status.conditions or [])
                ]
                if hasattr(daemonset.status, "conditions") and daemonset.status.conditions
                else []
            ),
        },
    }


def _extract_replicaset_info(replicaset) -> Dict[str, Any]:
    """Extract key information from a replicaset object."""
    pod_template_hash = None
    if replicaset.metadata.labels and "pod-template-hash" in replicaset.metadata.labels:
        pod_template_hash = replicaset.metadata.labels["pod-template-hash"]

    return {
        "name": replicaset.metadata.name,
        "namespace": replicaset.metadata.namespace,
        "replicas": replicaset.spec.replicas,
        "selector": replicaset.spec.selector.match_labels if replicaset.spec.selector else {},
        "pod_template_hash": pod_template_hash,
        "status": {
            "replicas": replicaset.status.replicas,
            "ready_replicas": replicaset.status.ready_replicas,
            "available_replicas": replicaset.status.available_replicas,
            "fully_labeled_replicas": replicaset.status.fully_labeled_replicas,
            "conditions": (
                [
                    {
                        "type": condition.type,
                        "status": condition.status,
                        "reason": condition.reason,
                        "message": condition.message,
                    }
                    for condition in (replicaset.status.conditions or [])
                ]
                if hasattr(replicaset.status, "conditions") and replicaset.status.conditions
                else []
            ),
        },
    }


def _extract_configmap_info(configmap) -> Dict[str, Any]:
    """Extract key information from a configmap object."""
    return {
        "name": configmap.metadata.name,
        "namespace": configmap.metadata.namespace,
        "data": configmap.data or {},
        "binary_data": configmap.binary_data or {},
        "labels": configmap.metadata.labels or {},
        "annotations": configmap.metadata.annotations or {},
        "creation_timestamp": (
            configmap.metadata.creation_timestamp.isoformat() if configmap.metadata.creation_timestamp else None
        ),
    }


def _extract_secret_info(secret) -> Dict[str, Any]:
    """Extract key information from a secret object (without revealing data)."""
    return {
        "name": secret.metadata.name,
        "namespace": secret.metadata.namespace,
        "type": secret.type,
        "data": {key: "<sensitive data>" for key in (secret.data or {}).keys()},
        "labels": secret.metadata.labels or {},
        "annotations": secret.metadata.annotations or {},
        "creation_timestamp": (
            secret.metadata.creation_timestamp.isoformat() if secret.metadata.creation_timestamp else None
        ),
    }


def _extract_namespace_info(namespace) -> Dict[str, Any]:
    """Extract key information from a namespace object."""
    return {
        "name": namespace.metadata.name,
        "status": namespace.status.phase if hasattr(namespace.status, "phase") else "Active",
        "labels": namespace.metadata.labels or {},
        "annotations": namespace.metadata.annotations or {},
        "creation_timestamp": (
            namespace.metadata.creation_timestamp.isoformat() if namespace.metadata.creation_timestamp else None
        ),
        # Resource quota and limit range would need to be fetched separately
        "resource_quota": [],
        "limit_range": [],
    }


def _extract_pv_info(pv) -> Dict[str, Any]:
    """Extract key information from a persistent volume object."""
    source = {}

    # Extract volume source type and details
    volume_source_attributes = [
        "host_path",
        "nfs",
        "gce_persistent_disk",
        "aws_elastic_block_store",
        "iscsi",
        "cinder",
        "cephfs",
        "fc",
        "flex_volume",
        "vsphere_volume",
        "quobyte",
        "azure_disk",
        "azure_file",
        "csi",
    ]

    for source_type in volume_source_attributes:
        if hasattr(pv.spec, source_type) and getattr(pv.spec, source_type) is not None:
            source_obj = getattr(pv.spec, source_type)
            if source_type == "host_path":
                source[source_type] = {"path": source_obj.path}
            elif source_type == "nfs":
                source[source_type] = {"server": source_obj.server, "path": source_obj.path}
            elif source_type == "csi":
                source[source_type] = {"driver": source_obj.driver, "volume_handle": source_obj.volume_handle}
            else:
                source[source_type] = "<volume details available>"

    claim_ref = None
    if hasattr(pv.spec, "claim_ref") and pv.spec.claim_ref:
        claim_ref = {"namespace": pv.spec.claim_ref.namespace, "name": pv.spec.claim_ref.name}

    return {
        "name": pv.metadata.name,
        "status": pv.status.phase,
        "capacity": pv.spec.capacity,
        "access_modes": pv.spec.access_modes,
        "reclaim_policy": pv.spec.persistent_volume_reclaim_policy,
        "storage_class": pv.spec.storage_class_name,
        "source": source,
        "claim_ref": claim_ref,
        "labels": pv.metadata.labels or {},
        "annotations": pv.metadata.annotations or {},
        "creation_timestamp": pv.metadata.creation_timestamp.isoformat() if pv.metadata.creation_timestamp else None,
    }


def _extract_pvc_info(pvc) -> Dict[str, Any]:
    """Extract key information from a persistent volume claim object."""
    return {
        "name": pvc.metadata.name,
        "namespace": pvc.metadata.namespace,
        "status": pvc.status.phase,
        "volume_name": pvc.spec.volume_name,
        "capacity": pvc.status.capacity if hasattr(pvc.status, "capacity") else {},
        "access_modes": pvc.spec.access_modes,
        "storage_class": pvc.spec.storage_class_name,
        "volume_mode": pvc.spec.volume_mode,
        "labels": pvc.metadata.labels or {},
        "annotations": pvc.metadata.annotations or {},
        "creation_timestamp": pvc.metadata.creation_timestamp.isoformat() if pvc.metadata.creation_timestamp else None,
    }


def _extract_ingress_info(ingress) -> Dict[str, Any]:
    """Extract key information from an ingress object."""
    rules = []
    if ingress.spec.rules:
        for rule in ingress.spec.rules:
            rule_info = {"host": rule.host}
            if rule.http and rule.http.paths:
                paths = []
                for path in rule.http.paths:
                    path_info = {"path": path.path, "path_type": path.path_type}

                    if path.backend and path.backend.service:
                        service_info = {"name": path.backend.service.name}
                        if path.backend.service.port:
                            if hasattr(path.backend.service.port, "number"):
                                service_info["port"] = {"number": path.backend.service.port.number}
                            elif hasattr(path.backend.service.port, "name"):
                                service_info["port"] = {"name": path.backend.service.port.name}

                        path_info["backend"] = {"service": service_info}

                    paths.append(path_info)

                rule_info["http"] = {"paths": paths}

            rules.append(rule_info)

    tls = []
    if ingress.spec.tls:
        for tls_item in ingress.spec.tls:
            tls.append({"hosts": tls_item.hosts, "secret_name": tls_item.secret_name})

    return {
        "name": ingress.metadata.name,
        "namespace": ingress.metadata.namespace,
        "ingress_class": ingress.spec.ingress_class_name,
        "rules": rules,
        "tls": tls,
        "labels": ingress.metadata.labels or {},
        "annotations": ingress.metadata.annotations or {},
        "creation_timestamp": (
            ingress.metadata.creation_timestamp.isoformat() if ingress.metadata.creation_timestamp else None
        ),
    }


def _extract_job_info(job) -> Dict[str, Any]:
    """Extract key information from a job object."""
    return {
        "name": job.metadata.name,
        "namespace": job.metadata.namespace,
        "completions": job.spec.completions,
        "parallelism": job.spec.parallelism,
        "status": {
            "active": job.status.active,
            "succeeded": job.status.succeeded,
            "failed": job.status.failed,
            "start_time": job.status.start_time.isoformat() if job.status.start_time else None,
            "completion_time": job.status.completion_time.isoformat() if job.status.completion_time else None,
            "conditions": (
                [
                    {
                        "type": condition.type,
                        "status": condition.status,
                        "reason": condition.reason,
                        "message": condition.message,
                    }
                    for condition in (job.status.conditions or [])
                ]
                if hasattr(job.status, "conditions") and job.status.conditions
                else []
            ),
        },
        "labels": job.metadata.labels or {},
        "annotations": job.metadata.annotations or {},
        "creation_timestamp": job.metadata.creation_timestamp.isoformat() if job.metadata.creation_timestamp else None,
    }


def _extract_cronjob_info(cronjob) -> Dict[str, Any]:
    """Extract key information from a cronjob object."""
    active_jobs = []
    if hasattr(cronjob.status, "active") and cronjob.status.active:
        for job_ref in cronjob.status.active:
            active_jobs.append({"name": job_ref.name, "namespace": job_ref.namespace})

    return {
        "name": cronjob.metadata.name,
        "namespace": cronjob.metadata.namespace,
        "schedule": cronjob.spec.schedule,
        "concurrency_policy": cronjob.spec.concurrency_policy,
        "suspend": cronjob.spec.suspend,
        "last_schedule_time": (
            cronjob.status.last_schedule_time.isoformat()
            if hasattr(cronjob.status, "last_schedule_time") and cronjob.status.last_schedule_time
            else None
        ),
        "active_jobs": active_jobs,
        "labels": cronjob.metadata.labels or {},
        "annotations": cronjob.metadata.annotations or {},
        "creation_timestamp": (
            cronjob.metadata.creation_timestamp.isoformat() if cronjob.metadata.creation_timestamp else None
        ),
    }


def _determine_volume_type(volume) -> str:
    """Determine the type of a volume based on its attributes."""
    volume_types = [
        "host_path",
        "empty_dir",
        "gce_persistent_disk",
        "aws_elastic_block_store",
        "secret",
        "config_map",
        "persistent_volume_claim",
        "projected",
    ]

    for vol_type in volume_types:
        if hasattr(volume, vol_type):
            return vol_type

    return "unknown"
