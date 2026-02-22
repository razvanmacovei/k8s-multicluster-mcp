from typing import Dict, List, Any, Optional
import os
from kubernetes import client
from kubernetes.client.rest import ApiException

from ..utils.k8s_client import KubernetesClient

# Initialize client with kubeconfig directory from environment or default
kubeconfig_dir = os.environ.get('KUBECONFIG_DIR', os.path.expanduser('~/.kube'))
k8s_client = KubernetesClient(kubeconfig_dir)


async def k8s_list_jobs(context: str, namespace: Optional[str] = None,
                        label_selector: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List Jobs in the cluster.

    Args:
        context: The Kubernetes context to use
        namespace: Namespace to list jobs from (all namespaces if not specified)
        label_selector: Label selector to filter jobs

    Returns:
        List of Job information
    """
    try:
        api_client = k8s_client.get_api_client(context)
        batch_v1 = client.BatchV1Api(api_client)

        kwargs = {}
        if label_selector:
            kwargs["label_selector"] = label_selector

        if namespace:
            jobs = batch_v1.list_namespaced_job(namespace=namespace, **kwargs)
        else:
            jobs = batch_v1.list_job_for_all_namespaces(**kwargs)

        return [
            {
                "name": job.metadata.name,
                "namespace": job.metadata.namespace,
                "completions": f"{job.status.succeeded or 0}/{job.spec.completions or 1}",
                "active": job.status.active or 0,
                "succeeded": job.status.succeeded or 0,
                "failed": job.status.failed or 0,
                "status": _job_status(job),
                "start_time": job.status.start_time.isoformat() if job.status.start_time else None,
                "completion_time": job.status.completion_time.isoformat() if job.status.completion_time else None,
                "created": job.metadata.creation_timestamp.isoformat() if job.metadata.creation_timestamp else None
            }
            for job in jobs.items
        ]
    except Exception as e:
        raise RuntimeError(f"Failed to list jobs: {str(e)}")


async def k8s_list_cronjobs(context: str, namespace: Optional[str] = None,
                            label_selector: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List CronJobs in the cluster.

    Args:
        context: The Kubernetes context to use
        namespace: Namespace to list cronjobs from (all namespaces if not specified)
        label_selector: Label selector to filter cronjobs

    Returns:
        List of CronJob information
    """
    try:
        api_client = k8s_client.get_api_client(context)
        batch_v1 = client.BatchV1Api(api_client)

        kwargs = {}
        if label_selector:
            kwargs["label_selector"] = label_selector

        if namespace:
            cronjobs = batch_v1.list_namespaced_cron_job(namespace=namespace, **kwargs)
        else:
            cronjobs = batch_v1.list_cron_job_for_all_namespaces(**kwargs)

        return [
            {
                "name": cj.metadata.name,
                "namespace": cj.metadata.namespace,
                "schedule": cj.spec.schedule,
                "suspend": cj.spec.suspend,
                "active_jobs": len(cj.status.active) if cj.status.active else 0,
                "last_schedule": cj.status.last_schedule_time.isoformat() if cj.status.last_schedule_time else None,
                "last_successful": cj.status.last_successful_time.isoformat() if cj.status.last_successful_time else None,
                "concurrency_policy": cj.spec.concurrency_policy,
                "created": cj.metadata.creation_timestamp.isoformat() if cj.metadata.creation_timestamp else None
            }
            for cj in cronjobs.items
        ]
    except Exception as e:
        raise RuntimeError(f"Failed to list cronjobs: {str(e)}")


def _job_status(job) -> str:
    """Determine the status string for a job."""
    if job.status.completion_time:
        return "Complete"
    if job.status.failed and job.status.failed > 0:
        # Check conditions for failure
        for condition in (job.status.conditions or []):
            if condition.type == "Failed" and condition.status == "True":
                return f"Failed: {condition.reason or 'unknown'}"
        return "Failed"
    if job.status.active and job.status.active > 0:
        return "Running"
    return "Pending"
