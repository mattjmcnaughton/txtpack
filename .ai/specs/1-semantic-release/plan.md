# Plan: Add Semantic-Release Automation

## Implementation Steps

### Step 1: Create Semantic-Release Configuration
- Create `.releaserc.json` with @semantic-release/exec plugin for Python project integration
- Configure plugins for commit analysis, release notes generation, version updates, git commits, and GitHub releases
- Set up version update command using sed to modify pyproject.toml
- Configure git assets to include pyproject.toml and CHANGELOG.md
- Enable automatic git tag creation and GitHub release generation
- **Deliverable**: `.releaserc.json` file with complete semantic-release configuration

### Step 2: Create Release GitHub Actions Workflow
- Create `.github/workflows/release.yml` with `workflow_run` trigger that depends on CI workflow completion
- Configure workflow to only run when CI workflow completes successfully on main branch
- Set up proper permissions (contents: write, issues: write, pull-requests: write, id-token: write)
- Set up Node.js environment for npx semantic-release execution
- Configure semantic-release execution with GITHUB_TOKEN authentication
- **Deliverable**: GitHub Actions workflow file that triggers releases only after CI passes

### Step 3: Test and Validate Configuration
- Test semantic-release configuration using `--dry-run` flag to validate setup without creating actual releases
- Verify workflow dependencies work correctly by testing CI → Release workflow chain
- Ensure version update commands work correctly with pyproject.toml format
- Validate that releases only trigger when CI passes on main branch
- **Deliverable**: Verified working semantic-release setup with proper CI dependencies

### Step 4: Update Documentation
- Add conventional commit format requirements to CLAUDE.md development instructions
- Document the new automated release process and CI → Release workflow dependency
- Include examples of conventional commit messages and their version impact
- Document how to test releases using dry-run mode
- **Deliverable**: Updated project documentation with release automation guidelines

## Testing Strategy

### Configuration Testing
- Use `npx semantic-release --dry-run` to test configuration without creating releases
- Verify all plugins load correctly and commands execute successfully in dry-run mode
- Test version update logic against current pyproject.toml format
- Validate workflow trigger conditions and CI dependency logic

### Workflow Integration Testing
- Test that release workflow only triggers after successful CI completion on main branch
- Verify that failed CI workflows prevent release workflow execution
- Ensure Node.js environment setup works correctly in release workflow
- Test authentication flow using GITHUB_TOKEN for GitHub API access

### Version Management Testing
- Verify sed command correctly updates version in pyproject.toml without breaking TOML format
- Test that git commits are created with proper commit messages and asset inclusion
- Ensure changelog generation works correctly for conventional commit messages
- Validate that GitHub releases and git tags are created with appropriate release notes
