"""Basic tests to verify package structure and imports."""

import importlib.util
import os
import sys
from pathlib import Path

import pytest


def test_package_imports():
    """Test that the main package can be imported."""
    # Add src to path for testing
    src_path = Path(__file__).parent.parent / "src"
    sys.path.insert(0, str(src_path))
    
    try:
        # Test importing main module
        from src import main
        assert hasattr(main, 'main'), "main function should exist in main module"
        assert hasattr(main, 'mcp'), "mcp object should exist in main module"
    finally:
        sys.path.pop(0)


def test_tool_modules_exist():
    """Test that all tool modules exist."""
    tools_dir = Path(__file__).parent.parent / "src" / "tools"
    
    expected_modules = [
        "contexts.py",
        "namespaces.py",
        "nodes.py",
        "pods.py",
        "events.py",
        "resources.py",
        "metrics.py",
        "rollouts.py",
        "scaling.py",
        "diagnosis.py",
        "api_discovery.py",
        "describe.py",
        "resource_management.py",
        "workload_management.py",
        "node_management.py",
        "pod_operations.py",
    ]
    
    for module in expected_modules:
        module_path = tools_dir / module
        assert module_path.exists(), f"Tool module {module} should exist"


def test_pyproject_toml_valid():
    """Test that pyproject.toml is valid and contains required fields."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml should exist"
    
    # Read pyproject.toml
    import tomllib
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)
    
    # Check required fields
    assert "project" in data, "pyproject.toml should have [project] section"
    project = data["project"]
    
    assert "name" in project, "Project name should be defined"
    assert project["name"] == "k8s-multicluster-mcp"
    
    assert "version" in project, "Project version should be defined"
    assert "description" in project, "Project description should be defined"
    assert "dependencies" in project, "Project dependencies should be defined"
    
    # Check build system
    assert "build-system" in data, "Build system should be defined"
    assert data["build-system"]["build-backend"] == "hatchling.build"
    
    # Check console scripts
    assert "scripts" in project, "Console scripts should be defined"
    assert "k8s-multicluster-mcp" in project["scripts"]


def test_license_exists():
    """Test that LICENSE file exists."""
    license_path = Path(__file__).parent.parent / "LICENSE"
    assert license_path.exists(), "LICENSE file should exist"
    
    # Check it's MIT license
    with open(license_path) as f:
        content = f.read()
        assert "MIT License" in content, "Should be MIT License"


def test_readme_exists():
    """Test that README.md exists and has proper content."""
    readme_path = Path(__file__).parent.parent / "README.md"
    assert readme_path.exists(), "README.md should exist"
    
    with open(readme_path) as f:
        content = f.read()
        # Check for key sections
        assert "pipx run k8s-multicluster-mcp" in content, "README should mention pipx run"
        assert "Quick Start" in content, "README should have Quick Start section"
        assert "config.json" in content, "README should show config.json example" 