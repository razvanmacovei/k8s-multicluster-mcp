# Contributing to k8s-multicluster-mcp

Thank you for your interest in contributing to k8s-multicluster-mcp! This document provides guidelines and instructions for contributing to the project.

## 🤝 Code of Conduct

By participating in this project, you agree to abide by our code of conduct:
- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive criticism
- Accept feedback gracefully

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- `pipx` for testing package installation
- `git` for version control
- A Kubernetes cluster (or kind/minikube) for testing

### Setting Up Development Environment

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/k8s_multicluster_mcp.git
   cd k8s_multicluster_mcp
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies**
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-asyncio pytest-cov black flake8 mypy
   ```

4. **Install the package in development mode**
   ```bash
   pip install -e .
   ```

## 📝 Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Write clean, readable code
- Follow the existing code style
- Add type hints where appropriate
- Update documentation as needed

### 3. Format Your Code

```bash
# Format with black (also handles import sorting)
black src/ tests/

# Check with flake8
flake8 src/ tests/ --max-line-length=120 --extend-ignore=E203,W503

# Type check with mypy
mypy src/ --ignore-missing-imports
```

### 4. Write Tests

- Add tests for new functionality in the `tests/` directory
- Ensure all tests pass:
  ```bash
  pytest tests/ -v
  ```

### 5. Test Package Building

```bash
# Build the package
pipx run build

# Test installation
pipx run --spec dist/*.whl k8s-multicluster-mcp --help
```

### 6. Update Documentation

- Update README.md if adding new features
- Update CHANGELOG.md with your changes in the "Unreleased" section
- Add docstrings to new functions and classes

## 🧪 Testing Guidelines

### Unit Tests

- Place tests in `tests/` directory
- Name test files as `test_*.py`
- Use descriptive test function names: `test_<what_is_being_tested>`
- Mock external dependencies (Kubernetes API calls)

### Integration Tests

For testing with real Kubernetes clusters:
```bash
export KUBECONFIG_DIR=/path/to/test/kubeconfigs
pytest tests/integration/ -v  # If integration tests exist
```

## 📚 Adding New Tools

To add a new MCP tool:

1. **Create tool module** in `src/tools/`:
   ```python
   # src/tools/your_tool.py
   from typing import Dict, Any
   import kubernetes
   
   async def your_kubernetes_operation(context: str, **kwargs) -> Dict[str, Any]:
       """Your tool description."""
       # Implementation
       pass
   ```

2. **Register in main.py**:
   ```python
   from .tools.your_tool import your_kubernetes_operation
   
   @mcp.tool()
   async def k8s_your_tool(context: str, **kwargs):
       """User-facing tool description."""
       return await your_kubernetes_operation(context, **kwargs)
   ```

3. **Update README.md** with:
   - Tool description in the tools list
   - Usage example

## 📋 Pull Request Process

1. **Before submitting**:
   - Ensure all tests pass
   - Update documentation
   - Add entry to CHANGELOG.md
   - Run linters and fix any issues

2. **PR Description** should include:
   - What changes were made and why
   - Link to related issue (if applicable)
   - Testing performed
   - Screenshots (if UI changes)

3. **PR Title Format**:
   - `feat: Add new feature`
   - `fix: Fix bug in X`
   - `docs: Update documentation`
   - `test: Add tests for Y`
   - `refactor: Refactor Z`

## 🐛 Reporting Issues

### Bug Reports

Include:
- Python version
- k8s-multicluster-mcp version
- Kubernetes version
- Steps to reproduce
- Expected vs actual behavior
- Error messages/logs

### Feature Requests

Include:
- Use case description
- Proposed solution
- Alternative solutions considered

## 🔄 Release Process

Maintainers handle releases:

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create and push tag: `git tag v1.x.x`
4. GitHub Actions automatically publishes to PyPI

## 💡 Tips

- Use `pipx run --spec . k8s-multicluster-mcp` to test local changes
- Set up pre-commit hooks for automatic formatting
- Test with multiple Python versions using `tox` or `nox`
- Use meaningful commit messages

## 📞 Getting Help

- Open an issue for bugs or feature requests
- Start a discussion for questions
- Tag maintainers for urgent issues

Thank you for contributing! 🎉 