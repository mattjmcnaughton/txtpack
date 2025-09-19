# Goal: Support Publishing to PyPI When New Tag Created

## Related Issue
Issue #4: feat: set up PyPI publishing on version tag creation

## What We Want to Accomplish
We want to establish an automated PyPI publishing pipeline that seamlessly integrates with the existing semantic-release workflow. When semantic-release creates a new version tag, the system should automatically build and publish the txtpack package to PyPI, enabling users to install it via `uvx txtpack` or `pip install txtpack`.

This automation will complete the release cycle by taking packages from version tagging directly to public availability, removing manual publishing steps and ensuring consistent, reliable releases. The solution should leverage GitHub Actions and PyPI's trusted publishing mechanism for secure, token-free deployment.

## Optimization Target
**Automation and reliability** - Optimizing for automation means eliminating manual intervention in the publishing process while ensuring the pipeline is robust and handles edge cases gracefully. This includes proper error handling, secure credential management, and integration testing to prevent failed or corrupted releases from reaching PyPI.

## Out of Scope
- Setting up publishing to alternative package repositories (conda-forge, etc.)
- Creating custom package distribution formats beyond standard Python wheels/sdist
- Implementing rollback mechanisms for published packages (PyPI doesn't support deletion)
- Advanced publishing strategies like staged rollouts or canary releases
- Documentation website deployment or hosting
- Package analytics or download tracking setup
