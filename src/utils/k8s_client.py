import os
import glob
from kubernetes import client, config
from typing import Dict, List, Optional


class KubernetesClient:
    """Utility class to handle Kubernetes API client operations"""

    def __init__(self, kubeconfig_dir: str = None):
        """
        Initialize the Kubernetes client utility

        Args:
            kubeconfig_dir (str, optional): Directory containing kubeconfig files
                                           Defaults to None (uses KUBECONFIG_DIR env var or ~/.kube)
        """
        self.kubeconfig_dir = kubeconfig_dir or os.environ.get("KUBECONFIG_DIR", os.path.expanduser("~/.kube"))
        self.contexts = self._get_available_contexts()

    def _get_available_contexts(self) -> List[str]:
        """
        Get available Kubernetes contexts from all kubeconfig files

        Returns:
            List[str]: List of available context names
        """
        contexts = []
        kubeconfig_files = glob.glob(os.path.join(self.kubeconfig_dir, "*"))

        for kubeconfig in kubeconfig_files:
            if os.path.isfile(kubeconfig):
                try:
                    # Load this specific kubeconfig file
                    contexts_from_file = config.list_kube_config_contexts(kubeconfig)
                    if contexts_from_file and contexts_from_file[0]:
                        # Add all contexts from this file
                        for ctx in contexts_from_file[0]:
                            contexts.append(ctx["name"])
                except Exception as e:
                    # Skip invalid files
                    continue

        return contexts

    def refresh_contexts(self) -> List[str]:
        """
        Refresh the list of available Kubernetes contexts

        Returns:
            List[str]: Updated list of available context names
        """
        self.contexts = self._get_available_contexts()
        return self.contexts

    def list_contexts(self) -> List[str]:
        """
        Get a list of all available Kubernetes contexts

        Returns:
            List[str]: List of available context names
        """
        return self.refresh_contexts()

    def get_matching_context(self, context_name: str) -> str:
        """
        Get the full context name that matches the provided context name or partial name

        Args:
            context_name (str): Full or partial name of the Kubernetes context

        Returns:
            str: Full matching context name

        Raises:
            ValueError: If no matching context is found or multiple matches are found
        """
        # First check if the exact context exists
        if context_name in self.contexts:
            return context_name

        # If not, try to find contexts that contain the provided name
        matching_contexts = [ctx for ctx in self.contexts if context_name in ctx]

        if len(matching_contexts) == 1:
            # If exactly one match, use it
            return matching_contexts[0]
        elif len(matching_contexts) > 1:
            # If multiple matches, raise an error
            raise ValueError(
                f"Multiple contexts found matching '{context_name}': {matching_contexts}. "
                f"Please specify the full context name."
            )
        else:
            # If no matches, raise an error
            raise ValueError(f"Context '{context_name}' not found in available contexts: {self.contexts}")

    def get_api_client(self, context_name: str) -> client.ApiClient:
        """
        Get a Kubernetes API client for a specific context or a partial match

        Args:
            context_name (str): Full or partial name of the Kubernetes context

        Returns:
            client.ApiClient: Configured Kubernetes API client

        Raises:
            ValueError: If the context is not found or multiple matches are found
        """
        # Refresh contexts to ensure we have the latest
        self.refresh_contexts()

        # Get the full context name that matches (exact or partial)
        full_context_name = self.get_matching_context(context_name)

        # Find which kubeconfig file contains this context
        for kubeconfig in glob.glob(os.path.join(self.kubeconfig_dir, "*")):
            if os.path.isfile(kubeconfig):
                try:
                    contexts_from_file = config.list_kube_config_contexts(kubeconfig)
                    if contexts_from_file and contexts_from_file[0]:
                        context_names = [ctx["name"] for ctx in contexts_from_file[0]]
                        if full_context_name in context_names:
                            # Load this kubeconfig and set the context
                            configuration = client.Configuration()
                            config.load_kube_config(
                                config_file=kubeconfig, context=full_context_name, client_configuration=configuration
                            )
                            return client.ApiClient(configuration)
                except Exception:
                    continue

        # This should not happen as we check membership above
        raise ValueError(f"Failed to load context '{full_context_name}'")
