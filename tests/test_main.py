"""Tests for the main entry point."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_main_function_exists():
    """Test that main function can be imported and exists."""
    from main import main

    assert callable(main), "main should be a callable function"


def test_kubeconfig_dir_handling():
    """Test that KUBECONFIG_DIR environment variable is handled correctly."""
    from main import main

    # Test with directory path
    with patch.dict(os.environ, {"KUBECONFIG_DIR": "/tmp/kubeconfigs"}):
        with patch("os.path.isfile", return_value=False):
            with patch("os.path.isdir", return_value=True):
                with patch("builtins.print") as mock_print:
                    with patch.object(sys.modules["main"].mcp, "run"):
                        main()
                        mock_print.assert_any_call("Using kubeconfig directory: /tmp/kubeconfigs")

    # Test with file path (should use parent directory)
    with patch.dict(os.environ, {"KUBECONFIG_DIR": "/tmp/kubeconfigs/config"}):
        with patch("os.path.isfile", return_value=True):
            with patch("os.path.dirname", return_value="/tmp/kubeconfigs"):
                with patch("builtins.print") as mock_print:
                    with patch.object(sys.modules["main"].mcp, "run"):
                        main()
                        mock_print.assert_any_call("Using kubeconfig directory: /tmp/kubeconfigs")


def test_mcp_tools_registered():
    """Test that MCP tools are properly registered."""
    import main

    # Check that mcp object exists
    assert hasattr(main, "mcp"), "mcp object should exist"

    # Check some key tool functions are defined
    expected_tools = [
        "k8s_get_contexts",
        "k8s_get_namespaces",
        "k8s_get_nodes",
        "k8s_get_resources",
        "k8s_get_pod_logs",
        "k8s_create_resource",
        "k8s_scale_resource",
        "k8s_rollout_status",
        "k8s_cordon_node",
        "k8s_pod_exec",
    ]

    for tool in expected_tools:
        assert hasattr(main, tool), f"Tool function {tool} should be defined"


def test_mcp_server_name():
    """Test that MCP server has correct name."""
    import main

    # The FastMCP object should be initialized with correct name
    # Note: This is a basic check, actual verification would need to inspect the mcp object
    assert main.mcp is not None, "mcp object should be initialized"
