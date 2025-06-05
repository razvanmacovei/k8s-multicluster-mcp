# Release Checklist

Use this checklist when preparing a new release of k8s-multicluster-mcp.

## Pre-release Steps

- [ ] Ensure all changes are committed and pushed to main branch
- [ ] Run all tests locally: `pytest tests/ -v`
- [ ] Run linters:
  ```bash
  black src/ tests/
  isort src/ tests/
  flake8 src/ tests/ --max-line-length=120 --extend-ignore=E203,W503
  ```
- [ ] Build package locally: `pipx run build`
- [ ] Test local installation: `pipx run --spec . k8s-multicluster-mcp`

## Release Steps

1. **Update Version**
   - [ ] Update version in `pyproject.toml` (e.g., `1.0.3` → `1.1.0`)
   - [ ] Update `CHANGELOG.md`:
     - Move items from "Unreleased" to new version section
     - Add release date
     - Update comparison links at bottom

2. **Commit Version Changes**
   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "chore: bump version to 1.1.0"
   git push origin main
   ```

3. **Create and Push Tag**
   ```bash
   git tag v1.1.0
   git push origin v1.1.0
   ```

4. **Monitor GitHub Actions**
   - [ ] Check that CI workflow passes
   - [ ] Check that Release workflow creates GitHub release
   - [ ] Check that Publish workflow uploads to PyPI

5. **Verify PyPI Release**
   - [ ] Check package appears on https://pypi.org/project/k8s-multicluster-mcp/
   - [ ] Test installation: `pipx run k8s-multicluster-mcp`

## Post-release Steps

- [ ] Update any external documentation
- [ ] Announce release (if applicable)
- [ ] Start new "Unreleased" section in CHANGELOG.md

## Rollback (if needed)

If something goes wrong:
1. Delete the tag: `git tag -d v1.1.0 && git push --delete origin v1.1.0`
2. Fix the issue
3. Start the release process again 