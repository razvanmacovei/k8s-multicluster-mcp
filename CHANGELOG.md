# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Published package to PyPI for easy installation via `pipx run`
- GitHub Actions workflows for CI/CD (ci.yml, publish.yml, release.yml)
- Proper Python packaging with standard `pyproject.toml`
- Multi-platform testing (Linux, macOS, Windows)
- Automated security scanning with bandit, safety, and pip-audit
- Comprehensive documentation:
  - Contributing guide (CONTRIBUTING.md)
  - Troubleshooting guide (TROUBLESHOOTING.md)
  - Release checklist (RELEASE_CHECKLIST.md)
  - GitHub issue and PR templates
- Test suite with package structure validation
- Linter configurations (black, isort, flake8)
- Python 3.8+ support (previously 3.11+)

### Changed
- Moved from manual installation to `pipx run` approach
- Restructured code to follow Python packaging standards
- Updated documentation to reflect new installation method
- Moved entry point from `app.py` to `src/main.py`
- Updated all imports to use relative imports

## [1.0.3] - 2025-01-01

### Added
- Initial release with full Kubernetes multi-cluster support
- Support for multiple kubeconfig files
- Comprehensive Kubernetes tools:
  - Cluster and context management
  - Resource listing and inspection
  - Pod logs and exec commands
  - Rollout management (status, history, undo, restart, pause, resume)
  - Scaling and autoscaling
  - Resource creation, patching, and updates
  - Node management (cordon, drain, taint)
  - Metrics display
  - API discovery and CRD listing
  - Application diagnostics
- MCP server implementation using FastMCP
- Support for all standard Kubernetes resources

[Unreleased]: https://github.com/razvanmacovei/k8s_multicluster_mcp/compare/v1.0.3...HEAD
[1.0.3]: https://github.com/razvanmacovei/k8s_multicluster_mcp/releases/tag/v1.0.3 