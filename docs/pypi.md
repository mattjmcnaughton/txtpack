# PyPI Trusted Publishing Setup

This document provides step-by-step instructions for configuring PyPI trusted publishing with GitHub Actions for the txtpack package.

## Overview

PyPI trusted publishing uses OpenID Connect (OIDC) tokens to securely publish packages without storing API tokens. This setup enables automatic publishing when semantic-release creates new version tags.

## Prerequisites

- GitHub repository with txtpack code
- PyPI account (create at https://pypi.org)
- Repository admin access for environment configuration

## Step 1: Configure PyPI Trusted Publishing

### 1.1 Access PyPI Account Publishing Settings

1. Go to https://pypi.org
2. Sign in to your account
3. Navigate to https://pypi.org/manage/account/publishing/
4. Click "Add a new pending publisher"

### 1.2 Configure Pending Publisher

Fill in the pending publisher configuration:

| Field | Value |
|-------|--------|
| **PyPI project name** | `txtpack` |
| **Owner** | Your GitHub username or organization |
| **Repository name** | `txtpack` |
| **Workflow filename** | `release.yml` |
| **Environment name** | `pypi` |

### 1.3 Save Configuration

Click "Add" to save the pending publisher configuration.

**Important**:
- Use "pending publisher" because the txtpack project doesn't exist on PyPI yet
- The pending publisher will automatically become active when the first successful publish happens
- The values must match exactly with your GitHub repository and workflow configuration

## Step 2: Configure GitHub Environment

### 2.1 Create Environment

1. Go to your GitHub repository
2. Click "Settings" tab
3. In left sidebar, find "Code and automation" section
4. Click "Environments"
5. Click "New environment"
6. Enter name: `pypi`
7. Click "Configure environment"

### 2.2 Configure Protection Rules (Recommended)

For additional security, configure protection rules:

#### Required Reviewers
- **Purpose**: Require manual approval before PyPI publishing
- **Setup**:
  - Check "Required reviewers"
  - Add maintainers who should approve releases
  - Check "Prevent self-review" for additional security

#### Wait Timer
- **Purpose**: Add delay before publishing starts
- **Setup**: Set timer (e.g., 5 minutes) to allow review time

#### Deployment Branches
- **Purpose**: Restrict publishing to specific branches
- **Setup**:
  - Select "Selected branches"
  - Add rule for `main` branch

### 2.3 Save Environment

Click "Save protection rules" to complete environment setup.

## Step 3: Verify Configuration

### 3.1 Check Workflow Configuration

Verify your `.github/workflows/release.yml` includes:

```yaml
permissions:
  id-token: write  # Required for trusted publishing
  contents: write
  issues: write
  pull-requests: write

jobs:
  release:
    environment: pypi  # Must match PyPI environment name
```

### 3.2 Check Semantic Release Configuration

Verify `.releaserc.json` includes:

```json
{
  "plugins": [
    [
      "@semantic-release/exec",
      {
        "publishCmd": "uv build && uv publish --trusted-publishing automatic"
      }
    ]
  ]
}
```

## Step 4: Test the Setup

### 4.1 Trigger Release

Create a test commit using conventional commit format:

```bash
git add .
git commit -m "feat: test pypi publishing setup"
git push origin main
```

### 4.2 Monitor Workflow

1. Go to "Actions" tab in GitHub repository
2. Watch the "Release" workflow execution
3. If environment protection is enabled, approve the deployment when prompted
4. Verify successful completion

### 4.3 Verify Package Publication

After successful workflow completion:

```bash
# Test installation with uv
uvx txtpack --help

# Test installation with pip
pip install txtpack
txtpack --help
```

Check package page: https://pypi.org/project/txtpack/

## Step 5: Verify Publisher Activation

After first successful publish:

1. Go back to https://pypi.org/manage/account/publishing/
2. Verify the pending publisher has been converted to an active publisher
3. The txtpack project should now exist at https://pypi.org/project/txtpack/
4. You can now manage the project directly at https://pypi.org/manage/project/txtpack/

## Troubleshooting

### Common Issues

#### "Trusted publisher not configured"
- Verify PyPI pending publisher settings match GitHub repository exactly
- Check spelling of repository owner, name, workflow filename
- Ensure environment name matches (`pypi`)

#### "Environment protection rules failed"
- Check if required reviewers are configured but haven't approved
- Verify deployment branch rules allow publishing from current branch
- Review environment protection settings

#### "Permission denied (id-token)"
- Confirm workflow has `id-token: write` permission
- Verify job is running in correct environment (`environment: pypi`)

#### "Package upload failed"
- Check for version conflicts (semantic-release should handle automatically)
- Verify package builds successfully with `uv build`
- Review PyPI project name spelling

#### "Pending publisher not found"
- Verify you created the pending publisher at the account level (not project level)
- Double-check all field values match exactly

### Manual Publishing (Emergency)

If automated publishing fails, publish manually:

```bash
# Build package
uv build

# Publish with API token (create token in PyPI settings)
uv publish --token $PYPI_API_TOKEN
```

## Security Benefits

- **No stored secrets**: Eliminates long-lived API tokens in repository
- **Scoped access**: Publishing only works from specific GitHub workflows
- **Audit trail**: All publications logged and traceable to commits
- **Environment protection**: Additional approval gates for sensitive operations
- **Automatic token rotation**: OIDC tokens are short-lived and automatically managed

## Maintenance

### Updating Configuration

If you need to change repository name, workflow file, or environment:

1. Update PyPI trusted publisher settings (or pending publisher)
2. Update GitHub workflow configuration
3. Update environment name if changed
4. Test with new commit

### Revoking Access

To revoke publishing access:

1. Remove trusted publisher from PyPI account settings
2. Delete GitHub environment (optional)
3. Remove publishing commands from semantic-release configuration

## Additional Resources

- [PyPI Trusted Publishing Documentation](https://docs.pypi.org/trusted-publishers/)
- [GitHub Environments Documentation](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
- [uv Publishing Documentation](https://docs.astral.sh/uv/guides/publish/)
