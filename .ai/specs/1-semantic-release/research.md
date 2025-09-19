# Research: Add Semantic-Release Automation

## Issue Context
Issue #1: feat: set up automated semantic-release with GitHub Actions

The issue specifies implementing automated release workflow using GitHub Actions that automatically updates version numbers based on conventional commits, generates and maintains CHANGELOG.md, creates git tags for releases, and triggers on merge to main branch. The solution should use `npx` to avoid installing semantic-release as a project dependency and configure for Python project structure.

## Codebase Context

### Current Project Structure
- **Python CLI project** using Typer framework with uv package management
- **Version**: Currently at `0.0.1-rc1` in pyproject.toml:3
- **Build system**: Hatchling with packages in `src/txtpack/` directory
- **Dependencies**: Minimal (structlog, typer) with dev dependencies (pytest, ruff, ty)
- **CI/CD**: Existing GitHub Actions workflow (`.github/workflows/ci.yml`) running on main/PR branches
- **Quality tools**: Ruff for linting/formatting, ty for type checking, pytest for testing
- **Development workflow**: Uses justfile for task automation (`just ci` command available)

### Existing CI Pipeline
The current CI workflow runs on push/PR to main branch and includes:
- Python 3.13 setup with uv package manager
- Dependency installation via `uv sync --group dev`
- Linting, formatting, type checking, and testing
- All quality gates required by CLAUDE.md instructions

### Version Management Context
- Version defined in `pyproject.toml` at `project.version = "0.0.1-rc1"`
- Uses hatchling build backend
- No existing version management automation
- Package structure follows `src/txtpack/` layout

## External Resources

### NPM Semantic Release Documentation
- **Primary Documentation**: [Semantic Release GitBook](https://semantic-release.gitbook.io/semantic-release/) - Official npm semantic-release documentation
- **GitHub Repository**: [semantic-release/semantic-release](https://github.com/semantic-release/semantic-release) - Source code and examples
- **GitHub Actions Integration**: [GitHub Actions Recipe](https://github.com/semantic-release/semantic-release/blob/master/docs/recipes/ci-configurations/github-actions.md) - Official workflow examples

### Python-Specific Plugins
- **@semantic-release/exec**: [Exec Plugin](https://github.com/semantic-release/exec) - Custom command execution for Python version updates
- **semantic-release-pypi**: [PyPI Plugin](https://www.npmjs.com/package/semantic-release-pypi) - Python-specific semantic-release plugin
- **sr-uv-plugin**: Context7 documentation shows a uv-specific plugin for pyproject.toml management

### Standard Specifications
- **Conventional Commits**: [conventionalcommits.org](https://www.conventionalcommits.org/en/v1.0.0/) - Commit format standard for automated versioning
- **Semantic Versioning**: [semver.org](https://semver.org/) - Version numbering specification (MAJOR.MINOR.PATCH)

### GitHub Actions Resources
- **Actions Documentation**: [GitHub Actions Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#jobsjob_idpermissions) - Permission requirements
- **Node.js Setup**: [actions/setup-node](https://github.com/actions/setup-node) - Node.js environment for npx
- **Python Setup**: [actions/setup-python](https://github.com/actions/setup-python) - Python environment integration

## Domain Knowledge

### NPM Semantic Release Architecture
- **Configuration**: Uses `.releaserc.json`, `.releaserc.js`, or `release.config.js` files
- **Plugin System**: Modular architecture with official and community plugins
- **Version Management**: Uses template variables like `${nextRelease.version}` for dynamic updates
- **Git Integration**: Handles commit creation, tagging, and pushing with proper authentication
- **GitHub Integration**: Creates releases, uploads assets, comments on issues/PRs via @semantic-release/github

### Python Project Integration Patterns
**Using @semantic-release/exec plugin:**
```json
{
  "plugins": [
    "@semantic-release/commit-analyzer",
    "@semantic-release/release-notes-generator",
    [
      "@semantic-release/exec",
      {
        "verifyReleaseCmd": "uv run just ci",
        "prepareCmd": "sed -i 's/version = \".*\"/version = \"${nextRelease.version}\"/' pyproject.toml && uv build",
        "publishCmd": "echo 'No PyPI publishing configured'"
      }
    ],
    [
      "@semantic-release/git",
      {
        "assets": ["pyproject.toml", "CHANGELOG.md"],
        "message": "chore(release): ${nextRelease.version} [skip ci]\\n\\n${nextRelease.notes}"
      }
    ],
    "@semantic-release/github"
  ]
}
```

### Conventional Commit Format
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Version Impact Rules:**
- `fix:` → PATCH version (0.0.X)
- `feat:` → MINOR version (0.X.0)
- `BREAKING CHANGE:` or `!` → MAJOR version (X.0.0)

**Additional Types:**
- `docs:`, `style:`, `refactor:`, `test:`, `chore:`, `ci:` → No version bump

### GitHub Actions Integration Patterns
**Required Permissions:**
```yaml
permissions:
  contents: write      # Create releases and push tags
  issues: write        # Comment on released issues
  pull-requests: write # Comment on released PRs
  id-token: write     # OIDC token for enhanced security
```

**Authentication**: Uses `GITHUB_TOKEN` secret for GitHub API access

**Workflow Structure:**
```yaml
- name: Setup Node.js
  uses: actions/setup-node@v4
  with:
    node-version: "lts/*"
- name: Setup Python
  uses: actions/setup-python@v5
  with:
    python-version: "3.13"
- name: Install uv
  run: pip install uv
- name: Run Quality Gates
  run: uv run just ci
- name: Release
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  run: npx semantic-release
```

### Template Variables for Python Projects
- `${nextRelease.version}` - The new semantic version
- `${nextRelease.notes}` - Generated release notes
- `${branch.name}` - Current branch name
- `${commits.length}` - Number of commits in release

## Related Files & References

### Configuration Files to Create
- `.releaserc.json` - Main semantic-release configuration
- `.github/workflows/release.yml` - GitHub Actions workflow for releases
- `scripts/update_version.py` - Python script for robust version updating (optional)

### Project Files to Modify
- `pyproject.toml` (line 3) - Primary version location for updates
- `CLAUDE.md` - May need documentation of conventional commit requirements

### Existing Integration Points
- `justfile` - Contains `just ci` command for quality gates
- `.github/workflows/ci.yml` - Existing CI pattern to follow for release workflow
- Python 3.13 + uv setup pattern from existing CI

## Key Considerations

### Technical Architecture Decisions
- **NPX vs Local Installation**: Using `npx semantic-release` avoids adding Node.js dependencies to Python project
- **Plugin Selection**: @semantic-release/exec provides flexibility for Python-specific commands
- **Version Update Strategy**: Can use sed for simple updates or Python script for robust parsing
- **Build Integration**: Should use `uv build` to align with existing toolchain

### Authentication & Permissions
- **GITHUB_TOKEN Limitations**: Cannot work with protected branches; may need PAT
- **Required Scopes**: Need `contents: write` for releases, `issues: write` and `pull-requests: write` for notifications
- **Security Considerations**: Use OIDC tokens (`id-token: write`) for enhanced security
- **PyPI Publishing**: Out of scope but would require `PYPI_TOKEN` secret if added later

### Integration Challenges
- **Node.js + Python Environment**: Workflow needs both Node.js (for semantic-release) and Python (for builds/tests)
- **Version File Updates**: pyproject.toml format requires careful string replacement or Python parsing
- **Existing CI Coordination**: Release workflow should run quality gates before releasing
- **Git History**: Need `fetch-depth: 0` for semantic-release to analyze commit history

### Configuration Complexity
- **Plugin Ordering**: Order matters in semantic-release plugin array
- **Error Handling**: Commands in @semantic-release/exec can fail and abort release
- **Testing Strategy**: Use `--dry-run` flag to test configuration safely
- **Branch Configuration**: Must specify correct branch names (main vs master)

### Scope Boundaries from Goal.md
- **No PyPI Publishing**: publishCmd should be no-op or echo statement
- **No Retrospective Commits**: Won't modify existing commit history
- **No Custom Templates**: Use standard changelog and release note formats
- **Git-based Releases Only**: Focus on GitHub releases, not package registries

### Maintainability Considerations
- **Dependency Management**: No Node.js dependencies in project, only used via npx
- **Documentation Needs**: Team must learn conventional commit format
- **Testing Workflow**: Need safe way to test release configuration
- **Version Conflicts**: Ensure version updates don't conflict with manual changes
