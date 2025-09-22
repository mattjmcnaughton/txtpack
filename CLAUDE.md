# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python CLI tool for bundling and unbundling files using pattern matching,
featuring `concat` and `split` commands that preserve file integrity through byte-accurate delimiters.
The tool supports glob patterns for file selection and enables round-trip
workflows where multiple files can be concatenated into a single stream
and later reconstructed back to their original individual files.

## Development Commands

See [CONTRIBUTING.md](CONTRIBUTING.md) for full development workflow details.

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
- **Follow contributing guidelines**: See [CONTRIBUTING.md](CONTRIBUTING.md) for commit format and workflow

### Code Style
- **Follow contributing guidelines**: See [CONTRIBUTING.md](CONTRIBUTING.md) for commit format and workflow
- Use absolute imports in python
- Use top-level imports (avoid guarded/conditional imports)
- Use existing patterns and conventions within each service
- Do not use emojis in code, comments, or CLI output - keep all text professional and plain
- **Comments**: Only include comments that explain meaningful additional context; avoid redundant or obvious comments

## Issue Management

Use GitHub CLI (`gh`) for issue management:

### Available Labels
- `bug`, `documentation`, `duplicate`, `enhancement`, `good first issue`, `help wanted`, `invalid`, `question`, `wontfix`

### Common Commands
- `gh issue list` - View all issues
- `gh issue view [number]` - View specific issue
- `gh issue create --title "TITLE" --body "BODY" --label "LABEL"` - Create new issue
