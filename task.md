# Task: Publish k8s-multicluster-mcp via pipx

## Overview

Transform the current k8s-multicluster-mcp MCP server into a proper Python package that can be used via `pipx run`, replacing the current manual installation methods. This will provide users with a single configuration step using `pipx run k8s-multicluster-mcp` directly in their MCP client config.

## Current State Analysis

- **Project Structure**: Well-organized with `src/` layout
- **Configuration**: Uses `tool.uv` configuration (non-standard)
- **Entry Point**: `app.py` in root directory
- **Dependencies**: Listed in both `requirements.txt` and `pyproject.toml`
- **Current Version**: 1.0.3
- **Installation Methods**: Smithery and manual setup
- **Target**: Single-step configuration using `pipx run`

## Implementation Plan

### Phase 1: Package Structure Refactoring

#### 1.1 Update pyproject.toml for Standard Python Packaging
- **Issue**: Current `pyproject.toml` uses `tool.uv` configuration, not standard Python packaging
- **Action**: Convert to standard `project` table configuration
- **Requirements**:
  - Add proper `[project]` section with metadata
  - Configure `[project.scripts]` for console entry point
  - Add `[build-system]` using setuptools or hatchling
  - Include all dependencies in `[project.dependencies]`
  - Add optional dependencies for development

#### 1.2 Create Package Entry Point
- **Current**: `app.py` in root needs to be executed directly
- **Target**: Create a proper console script entry point
- **Actions**:
  - Move `app.py` → `src/main.py` (or keep as `src/app.py`)
  - Add `main()` function that can be called as console script
  - Update imports to work from within the package
  - Configure console script in `pyproject.toml`

#### 1.3 Package Structure (Minimal Changes)
```
k8s_multicluster_mcp/          # Repo root
├── src/                       # Package source (becomes the package)
│   ├── __init__.py           # Already exists
│   ├── main.py               # Entry point (move app.py here)
│   ├── tools/                # Tool modules (already exists)
│   │   ├── __init__.py
│   │   ├── contexts.py
│   │   ├── namespaces.py
│   │   └── ...
│   └── utils/                # Utility modules (already exists)
├── tests/                    # Unit tests (future)
├── pyproject.toml           # Standard Python packaging
├── README.md                # Updated installation docs
├── CHANGELOG.md             # Version history
└── LICENSE                  # Add license file
```

**Changes needed:**
- Move `app.py` → `src/main.py` (or rename to `src/app.py`)
- Configure `pyproject.toml` to use `src/` as package root
- Add `main()` function for console script entry point

### Phase 2: Publishing Infrastructure

#### 2.1 PyPI Account and Configuration
- **Requirements**:
  - PyPI account setup
  - Generate API tokens for secure publishing
  - Configure trusted publishing (recommended) or token-based auth

#### 2.2 GitHub Repository Preparation
- **Add Files**:
  - `LICENSE` file (choose appropriate license)
  - `CHANGELOG.md` for version tracking
  - `.github/ISSUE_TEMPLATE/` for bug reports and features
  - `.github/PULL_REQUEST_TEMPLATE.md`

#### 2.3 Version Management Strategy
- **Current**: Manual version in `pyproject.toml`
- **Target**: Automated version management
- **Options**:
  1. **Git Tags + Dynamic Versioning**: Use `hatch-vcs` or `setuptools-scm`
  2. **Manual Versioning**: Keep manual versioning with strict workflow
- **Recommendation**: Git tags + dynamic versioning for automation

### Phase 3: CI/CD Pipeline Setup

#### 3.1 GitHub Actions Workflow Structure
```
.github/workflows/
├── ci.yml                 # Continuous Integration
├── release.yml            # Release workflow  
└── publish.yml            # PyPI publishing
```

#### 3.2 CI Workflow (`ci.yml`)
- **Triggers**: Pull requests, pushes to main
- **Jobs**:
  - Linting (black, isort, flake8, mypy)
  - Security scanning (bandit, safety)
  - Unit tests (pytest)
  - Integration tests with dummy kubeconfig
  - Package build test
  - Multi-platform testing (Linux, macOS, Windows)

#### 3.3 Release Workflow (`release.yml`)
- **Trigger**: Manual dispatch or tag creation
- **Jobs**:
  - Version validation
  - Changelog generation
  - GitHub release creation
  - Trigger publish workflow

#### 3.4 Publish Workflow (`publish.yml`)  
- **Trigger**: GitHub release created
- **Jobs**:
  - Build package (`python -m build`)
  - Run security checks on built package
  - Publish to Test PyPI first
  - Run installation test from Test PyPI
  - Publish to production PyPI
  - Update package statistics

#### 3.5 Trusted Publishing Setup
- **Benefits**: No API tokens needed, more secure
- **Setup**: Configure PyPI trusted publisher with GitHub repository
- **Workflow**: Use `pypa/gh-action-pypi-publish` with OIDC

### Phase 4: Documentation Updates

#### 4.1 README.md Updates
- **Remove**: Manual installation section and Smithery installation
- **Update**: Replace with single-step `pipx run` configuration
- **Add**: 
  - Quick start guide showing only the config step
  - Configuration examples for Claude Desktop
  - Benefits of `pipx run` approach
  - Troubleshooting section
  - Contribution guidelines

#### 4.2 Installation Documentation
```markdown
## Installation

No separate installation required! Just configure your MCP client:

### Configuration for Claude Desktop

Add to your `config.json`:
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

The first time you use it, `pipx` will automatically download and install the package in an isolated environment.

### Benefits of `pipx run` Approach

- **Zero Installation**: No separate installation step required
- **Always Latest**: Can optionally specify version or always use latest
- **Isolated Environment**: Runs in its own Python environment, no conflicts
- **Automatic Updates**: Easy to specify version constraints
- **No Global Pollution**: Doesn't install anything globally on user's system
- **Cross-Platform**: Works identically on Windows, macOS, and Linux

#### 4.3 Migration Guide
- **Create**: Migration guide for existing users
- **Include**: How to uninstall old methods and install via pipx

### Phase 5: Testing and Quality Assurance

#### 5.1 Packaging Tests
- **Local Testing**:
  - `python -m build` - verify package builds
  - `pip install dist/k8s_multicluster_mcp-*.whl` - test wheel installation
  - `pipx run .` - test local pipx run
  - Test console script works: `pipx run k8s-multicluster-mcp --version`

#### 5.2 Integration Testing
- **Create Test Environment**:
  - Dummy kubeconfig files
  - Mock Kubernetes clusters (kind/minikube)
  - Test all MCP tools work correctly

#### 5.3 User Acceptance Testing
- **Beta Testing**:
  - Install from Test PyPI
  - Test with real Claude Desktop configuration
  - Verify all functionality works as expected

### Phase 6: Release Process

#### 6.1 Pre-release Checklist
- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated  
- [ ] Version bumped appropriately
- [ ] Security scan clean
- [ ] Manual testing completed

#### 6.2 Release Steps
1. **Create Release Branch**: `release/v1.1.0`
2. **Update Version**: Bump version in pyproject.toml (if manual versioning)
3. **Update CHANGELOG**: Add release notes
4. **Create Pull Request**: Release branch → main
5. **Review and Merge**: After approval
6. **Create Git Tag**: `git tag v1.1.0`
7. **Push Tag**: Triggers release workflow
8. **Monitor Release**: Ensure PyPI publish succeeds

#### 6.3 Post-release Tasks
- [ ] Update documentation site (if any)
- [ ] Announce on relevant communities
- [ ] Update Smithery package (transition plan)
- [ ] Monitor for issues

## Technical Considerations

### 6.1 Package Naming
- **Current**: `k8s-multicluster-mcp`
- **PyPI Name**: Check availability, may need `k8s-multicluster-mcp-server`
- **Console Script**: `k8s-multicluster-mcp` or `k8s-mcp`

### 6.2 Python Version Support
- **Current**: Python 3.11+
- **Recommendation**: Support 3.8+ for broader compatibility
- **Testing**: Test on multiple Python versions in CI

### 6.3 Dependencies Management
- **Pin Major Versions**: Use `>=1.0.0,<2.0.0` for stability
- **Security**: Regular dependency updates via Dependabot
- **Optimization**: Review if all dependencies are necessary

### 6.4 Configuration Handling
- **Environment Variables**: Document all required env vars
- **Config File Support**: Consider adding config file support
- **Error Handling**: Improve error messages for missing configs

## Security Considerations

### 6.1 Package Security
- **Code Signing**: Consider package signing
- **Dependency Scanning**: Automated vulnerability scanning
- **SBOM Generation**: Software Bill of Materials for transparency

### 6.2 Secrets Management
- **PyPI Tokens**: Use GitHub secrets securely
- **Trusted Publishing**: Preferred over token-based auth
- **Audit Trail**: Log all publishes and access

## Migration Strategy

### 6.1 Transition Phase
- **Maintain Parallel Support**: Keep Smithery method temporarily
- **Clear Documentation**: Explain migration path
- **Version Communication**: Announce pipx as preferred method

### 6.2 Deprecation Timeline
- **Phase 1 (v1.1.0)**: Introduce pipx installation, mark others as legacy
- **Phase 2 (v1.2.0)**: Add deprecation warnings to old methods
- **Phase 3 (v2.0.0)**: Remove alternative installation methods

## Success Metrics

### 6.1 Adoption Metrics
- PyPI download statistics
- GitHub release download counts
- User feedback and issues
- Installation success rate

### 6.2 Quality Metrics
- CI/CD pipeline success rate
- Security scan results
- User-reported issues
- Time from development to release

## Implementation Timeline

### Package Structure
- [x] Refactor pyproject.toml
- [x] Create proper package structure
- [x] Add console script entry point
- [x] Local testing

### CI/CD Pipeline
- [x] Create GitHub Actions workflows
- [x] Set up PyPI accounts and trusted publishing
- [x] Configure security scanning
- [x] Test automation

### Documentation and Testing
- [x] Update README and documentation
- [x] Create comprehensive tests
- [x] Create troubleshooting guide
- [x] Create contributing guide
- [x] Add GitHub templates (issues, PRs)
- [x] Add usage examples

### Release and Launch
- [ ] Final testing and validation
- [ ] Create first official release
- [ ] Monitor release and fix any issues
- [ ] Announce to community

## Long-term Maintenance

### Community Management
- **Issue Triage**: Regular issue review and response
- **Feature Requests**: Evaluation and implementation
- **Documentation**: Keep docs current and comprehensive

### Backwards Compatibility
- **Semantic Versioning**: Strict adherence to semver
- **Deprecation Policy**: Clear communication of breaking changes
- **Migration Guides**: For major version updates

---

This plan provides a comprehensive roadmap for transforming your MCP server into a professional, easily installable Python package. The pipx installation method will significantly improve the user experience and make adoption much easier. 