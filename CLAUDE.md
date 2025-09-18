# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python CLI tool for bundling and unbundling files using pattern matching,
featuring `concat` and `split` commands that preserve file integrity through byte-accurate delimiters.
The tool supports glob patterns for file selection and enables round-trip
workflows where multiple files can be concatenated into a single stream
and later reconstructed back to their original individual files.

## Development Commands

### Installation & Setup
```bash
just install          # Install all dependencies
```

### Code Quality & Testing
```bash
# Full CI pipeline
just ci               # Run all linting, formatting, typechecking, and tests

# Individual checks
just lint             # Lint
just lint-fix         # Auto-fix linting issues
just format           # Format code
just format-check     # Check formatting without fixing
just typecheck        # Run type checking
just test             # Run tests (pytest)
```
## Architecture & Code Organization

- **Tech Stack**: Typer, Python 3.11+, uv package management
- **Structure**:
  - `src/txtpack/` - Main package
- **Testing**: pytest with unit and integration test directories
- **Code Quality**: Ruff for linting/formatting, ty for type checking

## Project-Specific Instructions

### Critical Rules
- **Use justfile commands**: Prefer `just <command>` over direct tool invocation
- **Quality gates**: Run `just ci` before committing significant changes


### Code Style
- Use absolute imports in python
- Follow Ruff configuration (120 char line length, Python 3.11 target)
- Use existing patterns and conventions within each service
- Do not use emojis in code, comments, or CLI output - keep all text professional and plain
- Use `structlog` for all logging throughout the backend
- Use snake_case for structured log event names (e.g., `logger.error("no_files_found", ...)` instead of `"No files found"`)

## Issue Management

Use GitHub CLI (`gh`) for issue management:

### Available Labels
- `bug`, `documentation`, `duplicate`, `enhancement`, `good first issue`, `help wanted`, `invalid`, `question`, `wontfix`

### Common Commands
- `gh issue list` - View all issues
- `gh issue view [number]` - View specific issue
- `gh issue create --title "TITLE" --body "BODY" --label "LABEL"` - Create new issue
