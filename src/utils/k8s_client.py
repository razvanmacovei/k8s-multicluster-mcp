import os
import glob
import time
from kubernetes import client, config
from typing import Dict, List, Optional


class KubernetesClient:
    """Utility class to handle Kubernetes API client operations with context caching."""

    # Cache TTL in seconds (refresh contexts at most every 30 seconds)
    CACHE_TTL = 30

    def __init__(self, kubeconfig_dir: str = None):
        """
        Initialize the Kubernetes client utility.

        Args:
            kubeconfig_dir: Directory containing kubeconfig files.
                           Defaults to KUBECONFIG_DIR env var or ~/.kube.
        """
        self.kubeconfig_dir = kubeconfig_dir or os.environ.get(
            'KUBECONFIG_DIR', os.path.expanduser('~/.kube')
        )
        self._contexts: List[str] = []
        self._context_file_map: Dict[str, str] = {}  # context_name -> kubeconfig_file
        self._cache_timestamp: float = 0
        self._refresh_contexts()

    def _refresh_contexts(self) -> None:
        """Refresh the internal cache of available contexts and their source files."""
        contexts = []
        context_file_map = {}

        kubeconfig_files = glob.glob(os.path.join(self.kubeconfig_dir, '*'))

        for kubeconfig in kubeconfig_files:
            if os.path.isfile(kubeconfig):
                try:
                    contexts_from_file = config.list_kube_config_contexts(kubeconfig)
                    if contexts_from_file and contexts_from_file[0]:
                        for ctx in contexts_from_file[0]:
                            name = ctx['name']
                            contexts.append(name)
                            context_file_map[name] = kubeconfig
                except Exception:
                    # Skip invalid files
                    continue

        self._contexts = contexts
        self._context_file_map = context_file_map
        self._cache_timestamp = time.monotonic()

    def _ensure_fresh_cache(self) -> None:
        """Refresh contexts if cache has expired."""
        if time.monotonic() - self._cache_timestamp > self.CACHE_TTL:
            self._refresh_contexts()

    @property
    def contexts(self) -> List[str]:
        """Get the list of available context names."""
        self._ensure_fresh_cache()
        return self._contexts

    def refresh_contexts(self) -> List[str]:
        """
        Force refresh the list of available Kubernetes contexts.

        Returns:
            Updated list of available context names.
        """
        self._refresh_contexts()
        return self._contexts

    def list_contexts(self) -> List[str]:
        """
        Get a list of all available Kubernetes contexts.

        Returns:
            List of available context names.
        """
        self._ensure_fresh_cache()
        return self._contexts

    def get_matching_context(self, context_name: str) -> str:
        """
        Get the full context name that matches the provided context name or partial name.

        Supports exact match and partial (substring) match. If the provided name
        is a substring of exactly one context, that context is returned.

        Args:
            context_name: Full or partial name of the Kubernetes context.

        Returns:
            Full matching context name.

        Raises:
            ValueError: If no matching context is found or multiple matches exist.
        """
        self._ensure_fresh_cache()

        # Exact match first
        if context_name in self._contexts:
            return context_name

        # Partial (substring) match
        matching = [ctx for ctx in self._contexts if context_name in ctx]

        if len(matching) == 1:
            return matching[0]
        elif len(matching) > 1:
            raise ValueError(
                f"Multiple contexts found matching '{context_name}': {matching}. "
                f"Please specify the full context name."
            )
        else:
            raise ValueError(
                f"Context '{context_name}' not found in available contexts: {self._contexts}"
            )

    def get_api_client(self, context_name: str) -> client.ApiClient:
        """
        Get a Kubernetes API client for a specific context or a partial match.

        Uses cached context-to-file mapping for fast lookups instead of
        scanning all kubeconfig files on every call.

        Args:
            context_name: Full or partial name of the Kubernetes context.

        Returns:
            Configured Kubernetes API client.

        Raises:
            ValueError: If the context is not found or multiple matches are found.
        """
        self._ensure_fresh_cache()

        # Resolve context name (exact or partial)
        full_context_name = self.get_matching_context(context_name)

        # Look up the kubeconfig file from cache
        kubeconfig = self._context_file_map.get(full_context_name)

        if kubeconfig:
            try:
                configuration = client.Configuration()
                config.load_kube_config(
                    config_file=kubeconfig,
                    context=full_context_name,
                    client_configuration=configuration
                )
                return client.ApiClient(configuration)
            except Exception:
                pass

        # Fallback: force refresh and retry (handles race conditions where cache is stale)
        self._refresh_contexts()
        kubeconfig = self._context_file_map.get(full_context_name)

        if kubeconfig:
            configuration = client.Configuration()
            config.load_kube_config(
                config_file=kubeconfig,
                context=full_context_name,
                client_configuration=configuration
            )
            return client.ApiClient(configuration)

        raise ValueError(f"Failed to load context '{full_context_name}'") 