# Research: Support Publishing to PyPI When New Tag Created

## Issue Context
Issue #4: feat: set up PyPI publishing on version tag creation - Set up automated PyPI publishing to enable installation via `uvx txtpack`. The publishing should trigger automatically when a new version tag is created by the semantic-release workflow.

## Codebase Context

### Current Project Structure
- **Build System**: Uses `hatchling` build backend with `pyproject.toml` configuration
- **Package Structure**: Source in `src/txtpack/` with console script entry point `txtpack = "txtpack.main:main"`
- **Version Management**: Static version `"1.0.0"` in pyproject.toml, updated by semantic-release via sed command
- **Development Tools**: uv for package management, Typer for CLI, Python 3.11+ requirement

### Existing CI/CD Pipeline
- **CI Workflow** (`.github/workflows/ci.yml`): Runs on push/PR to main, includes linting, formatting, type checking, and tests using uv
- **Release Workflow** (`.github/workflows/release.yml`): Triggered after CI success, uses semantic-release with Node.js
- **Semantic Release Config** (`.releaserc.json`): Configured with exec plugin that updates pyproject.toml version but has placeholder for PyPI publishing

### Current Release Process
1. Changes merged to main branch
2. CI pipeline validates code quality using `uv sync --group dev` and `uv run` commands
3. Semantic-release analyzes commits using conventional commit format
4. Version bumped in pyproject.toml via sed command
5. Changelog generated and GitHub release created
6. **Missing**: PyPI publishing step (currently shows placeholder message)

## External Resources

### uv-Native Publishing Approach (Recommended)
- **uv publish Command**: Native uv command for uploading distributions to PyPI
- **Trusted Publishing Integration**: Built-in support with `--trusted-publishing automatic`
- **Workflow Integration**: Direct `uv build` → `uv publish` pipeline
- **Performance**: Leverages uv's Rust-based optimizations and caching

### PyPI Trusted Publishing (Security Foundation)
- **Official Documentation**: PyPI Warehouse project provides comprehensive trusted publishing guides
- **Security Model**: Uses OpenID Connect (OIDC) tokens instead of long-lived API tokens
- **GitHub Integration**: Native support for GitHub Actions with `id-token: write` permission
- **uv Support**: `uv publish --trusted-publishing automatic` handles OIDC token exchange automatically

### GitHub Actions uv Integration
- **setup-uv Action**: `astral-sh/setup-uv@v6` with native caching and Python version management
- **Build Process**: `uv build` creates wheel and sdist in `dist/` directory
- **Publishing Process**: `uv publish --trusted-publishing automatic` handles upload
- **Caching**: Built-in uv cache with `enable-cache: true` and dependency glob patterns

### Best Practices from Research
- Use GitHub environments (e.g., "pypi") for additional approval gates
- Test with TestPyPI first using `uv publish --publish-url https://test.pypi.org/legacy/`
- Leverage uv's native caching for faster workflow execution
- Maintain uv ecosystem consistency throughout build and publish pipeline

## Domain Knowledge

### uv-Native Publishing Workflow
1. **Build**: `uv build` creates distributions in `dist/` directory
2. **Publish**: `uv publish --trusted-publishing automatic` handles:
   - OIDC token detection in GitHub Actions environment
   - Token exchange with PyPI for temporary API token
   - Upload of both wheel and source distributions
   - Automatic cleanup of temporary credentials

### uv publish Command Features
- **Default Behavior**: Uploads `dist/*` files (all distributions)
- **Trusted Publishing**: `--trusted-publishing automatic|always|never` options
- **Index Support**: Can target different indexes via `--publish-url` or `--index`
- **Authentication**: Supports tokens, username/password, and keyring providers
- **Error Handling**: Built-in duplicate detection and retry logic

### Integration with Semantic Release
- Current semantic-release config has `publishCmd` placeholder
- **Option 1**: Update semantic-release exec plugin to use `uv publish`
- **Option 2**: Trigger separate PyPI workflow on tag creation events
- **Preferred**: Integrate directly into release workflow for atomic releases
- Need to coordinate version updates with package building

## Related Files & References

### Project Configuration Files
- `pyproject.toml` - Package metadata, build system (hatchling), dependencies, and tool configuration
- `.releaserc.json` - Semantic-release configuration with exec plugin for version updates
- `CONTRIBUTING.md` - Development workflow with uv commands and conventional commit format

### Workflow Files
- `.github/workflows/ci.yml` - Code quality validation using uv ecosystem (`uv sync`, `uv run`)
- `.github/workflows/release.yml` - Automated release process using semantic-release
- Current release workflow uses workflow_run trigger dependent on CI success

### Development Environment
- `justfile` - Command runner for development tasks including `just ci`
- `uv` package manager - Used for dependency management, virtual environments, building, and publishing
- Python 3.11+ requirement with uv-managed dev dependencies

## Key Considerations

### uv Ecosystem Consistency
- **Native Tools**: Use `uv build` and `uv publish` instead of mixing pip/twine/external tools
- **Performance**: Leverage uv's Rust-based speed throughout the pipeline
- **Caching**: Utilize uv's built-in caching for dependencies and builds
- **Workflow Alignment**: Maintain consistency with existing `uv sync` and `uv run` patterns

### Security and Trust
- **Trusted Publishing Preferred**: `uv publish --trusted-publishing automatic` eliminates API token management
- **Repository Configuration**: Need to configure trusted publisher in PyPI project settings
- **Environment Protection**: Consider using GitHub environments for additional approval gates
- **Permissions**: Minimal required permissions (id-token: write, contents: read)

### Integration Strategy
- **Trigger Mechanism**: Tag creation events vs workflow_run vs semantic-release integration
- **Version Coordination**: Ensure version in pyproject.toml matches tag version before build
- **Build and Publish Timing**: Must build package after version update but before upload
- **uv Workflow**: Use `astral-sh/setup-uv@v6` with caching for optimal performance

### Testing and Validation
- **TestPyPI Testing**: Use `uv publish --publish-url https://test.pypi.org/legacy/` for testing
- **Package Installation**: Verify `uvx txtpack` works after publishing
- **CI Integration**: Ensure publishing doesn't break if CI pipeline changes
- **Error Handling**: Plan for network issues, validation errors, and retry scenarios

### Backwards Compatibility
- **Existing Workflows**: Must not break current uv-based CI/release process
- **Development Experience**: Maintain current `just ci` and uv development commands
- **Version Management**: Preserve semantic-release version bump behavior
- **GitHub Releases**: Continue creating GitHub releases alongside PyPI publishing

### Recommended Implementation Approach
1. **Update semantic-release**: Modify `.releaserc.json` exec plugin `publishCmd` to use `uv publish --trusted-publishing automatic`
2. **GitHub Actions**: Ensure release workflow has `id-token: write` permission for trusted publishing
3. **PyPI Setup**: Configure trusted publisher for GitHub Actions in PyPI project settings
4. **Testing**: Test with TestPyPI first using `--publish-url` override
5. **Documentation**: Update installation instructions to include `uvx txtpack`

## Manual PyPI Publishing for Existing Tags

### GitHub Actions Manual Trigger Options

#### Option 1: workflow_dispatch Trigger
Add `workflow_dispatch` trigger to the PyPI publishing workflow to enable manual execution:

```yaml
name: PyPI Publish
on:
  workflow_run:
    workflows: ["Release"]
    types: [completed]
  workflow_dispatch:
    inputs:
      tag:
        description: 'Git tag to publish (e.g., v1.0.0)'
        required: true
        type: string
      environment:
        description: 'Target environment'
        required: true
        default: 'pypi'
        type: choice
        options:
        - pypi
        - testpypi
```

**Usage**: Go to Actions tab → Select workflow → "Run workflow" → Enter tag name

#### Option 2: GitHub CLI Command
Trigger workflow manually using GitHub CLI:

```bash
# Publish specific tag to PyPI
gh workflow run "PyPI Publish" \
  --field tag=v1.0.0 \
  --field environment=pypi

# Publish to TestPyPI for testing
gh workflow run "PyPI Publish" \
  --field tag=v1.0.0 \
  --field environment=testpypi
```

#### Option 3: Repository Dispatch Event
Create a separate trigger workflow for on-demand publishing:

```bash
# Trigger via repository dispatch
gh api repos/:owner/:repo/dispatches \
  --method POST \
  --field event_type=publish-pypi \
  --field client_payload='{"tag":"v1.0.0","environment":"pypi"}'
```

### Workflow Implementation Considerations

#### Tag Checkout Strategy
Ensure the workflow checks out the specific tag:

```yaml
steps:
  - name: Checkout specific tag
    uses: actions/checkout@v4
    with:
      ref: ${{ inputs.tag || github.ref }}
      fetch-depth: 0
```

#### Version Validation
Validate that the pyproject.toml version matches the tag:

```yaml
  - name: Validate version consistency
    run: |
      TAG_VERSION=${{ inputs.tag || github.ref_name }}
      TAG_VERSION=${TAG_VERSION#v}  # Remove 'v' prefix if present
      PROJECT_VERSION=$(uv run python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")
      if [ "$TAG_VERSION" != "$PROJECT_VERSION" ]; then
        echo "Version mismatch: tag=$TAG_VERSION, project=$PROJECT_VERSION"
        exit 1
      fi
```

#### Environment-Specific Publishing
Support both PyPI and TestPyPI targets:

```yaml
  - name: Publish to PyPI
    run: |
      if [ "${{ inputs.environment }}" = "testpypi" ]; then
        uv publish --trusted-publishing automatic --publish-url https://test.pypi.org/legacy/
      else
        uv publish --trusted-publishing automatic
      fi
```

### Local Manual Publishing (Alternative)

For immediate publishing without waiting for CI/CD:

```bash
# Checkout specific tag locally
git checkout v1.0.0

# Build distributions
uv build

# Publish to TestPyPI (testing)
uv publish --publish-url https://test.pypi.org/legacy/ --token $TESTPYPI_TOKEN

# Publish to PyPI (production) - requires API token for local use
uv publish --token $PYPI_TOKEN

# Or if you have trusted publishing configured locally (less common)
uv publish --trusted-publishing automatic
```

**Note**: Local publishing requires API tokens since trusted publishing is primarily designed for CI/CD environments. The GitHub Actions approach is preferred for security and auditability.
