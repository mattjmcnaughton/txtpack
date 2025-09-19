# Plan: Support Publishing to PyPI When New Tag Created

## Implementation Steps

### Step 1: Configure PyPI Trusted Publishing
- Set up trusted publisher configuration in PyPI project settings
- Configure GitHub Actions as trusted publisher for the txtpack repository
- **Deliverable**: PyPI project configured to accept trusted publishing from GitHub Actions

### Step 2: Update Semantic Release Configuration
- Modify `.releaserc.json` exec plugin to replace placeholder `publishCmd` with `uv publish --trusted-publishing automatic`
- **Deliverable**: Updated `.releaserc.json` with integrated PyPI publishing

### Step 3: Enhance Release Workflow
- Add `id-token: write` permission to `.github/workflows/release.yml`
- **Deliverable**: Updated release workflow with PyPI publishing capabilities

### Step 4: Update Documentation
- Update installation instructions to include `uvx txtpack` and `pip install txtpack`
- **Deliverable**: Updated documentation reflecting new PyPI availability

## Testing Strategy

### End-to-End Validation
- Create a test release to verify complete workflow from commit to package availability
- Verify `uvx txtpack` works after publishing
- Confirm published package version matches git tag
