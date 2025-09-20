# Research: Write End-to-End Tests

## Issue Context
Issue #2: Add end-to-end testing - The txtpack CLI tool needs comprehensive end-to-end (e2e) testing to ensure complete user workflows function correctly. Focus is on testing full CLI commands and interactions rather than individual code units, with emphasis on round-trip file integrity (pack → unpack → verify identical files).

## Codebase Context

### Current Test Infrastructure
- **Test structure**: Well-organized with separate `tests/e2e/` (empty, ready for implementation) and `tests/unit/` directories
- **Testing framework**: pytest configured with proper test discovery patterns in `pyproject.toml`
- **Quality gates**: Comprehensive CI pipeline using `just ci` (lint, format-check, typecheck, test)
- **Development commands**: `just test` for pytest execution, `just ci` for full pipeline

### CLI Architecture Analysis
- **Framework**: Built with **Typer** for modern CLI development
- **Commands**:
  - `pack`: Takes glob/regex patterns, outputs to stdout with byte-accurate delimiters
  - `unpack`: Reads from stdin/file, reconstructs original files with integrity preservation
- **Entry points**:
  - Main: `txtpack.main:main` (pyproject.toml)
  - CLI app: `txtpack.cli:app` (Typer application)
- **Testing surface**: Well-separated private functions in `cli.py` suitable for comprehensive testing

### Code Quality Standards
- **Ruff** for linting/formatting (120 char line length)
- **ty** for type checking (excludes tests)
- **structlog** for structured logging to stderr
- **Professional text policy**: No emojis, plain text only

### Existing Patterns
- **Error handling**: Structured logging with proper exit codes via `typer.Exit(1)`
- **Configuration**: Dataclass `BundlerConfig` for delimiter configuration
- **File operations**: Modular private functions (`_find_matching_files`, `_parse_concatenated_content`)

## External Resources

### pytest Documentation and Best Practices
- **pytest fixtures**: Comprehensive fixture system for setup/teardown, with support for parametrization and scope management
- **Capture fixtures**: Built-in fixtures like `capsys`, `capfd`, `capfdbinary` for capturing stdout/stderr output
- **CLI testing patterns**: pytest supports subprocess testing for CLI applications
- **Test organization**: AAA pattern (Arrange, Act, Assert) recommended for clear test structure

### Python E2E Testing Best Practices (2024)
- **CLI subprocess testing**: Use `subprocess.run()` with `capture_output=True` and `text=True` for CLI testing
- **pytest-console-scripts plugin**: Specialized plugin for testing console scripts installed via setup.py entry points
- **E2E test characteristics**: Should validate entire workflows from input to output, complement (not replace) unit/integration tests
- **Test independence**: Keep test cases independent and use meaningful test names
- **Fixture usage**: Implement proper fixtures for resource management and cleanup

### Testing Framework Advantages
- **pytest popularity**: Most popular Python testing framework in 2024
- **Simple syntax**: Easier than unittest, powerful fixture system
- **Plugin ecosystem**: Large community with specialized plugins for different scenarios
- **Parameterized testing**: Built-in support for running same test with different inputs

## Domain Knowledge

### E2E Testing Concepts
- **Round-trip testing**: Critical for txtpack - pack files → unpack → verify byte-accurate reconstruction
- **CLI testing approaches**:
  - Direct function calls vs subprocess invocation
  - Capturing and asserting stdout/stderr output
  - Testing error conditions and exit codes
- **File system testing**: Creating temporary test structures, cleanup management
- **Edge case coverage**: Empty files, binary content, special characters, large files

### pytest Fixture System
- **Fixture scopes**: session, module, class, function for different setup/teardown needs
- **Parametrized fixtures**: Testing same functionality with different inputs
- **Fixture dependencies**: Building complex setup logic by composing fixtures
- **Capture fixtures**: `capsys` for sys.stdout/stderr, `capfd` for file descriptors

### CLI Testing Strategies
- **subprocess.run()**: Standard approach for testing CLI commands as black box
- **Output capture**: Verifying both success outputs and error messages
- **Exit code testing**: Ensuring proper error signaling
- **Pipeline testing**: Testing stdin/stdout operations that txtpack uses

## Related Files & References

### Project Files
- `tests/e2e/` - Empty directory ready for e2e test implementation
- `tests/unit/test_always_pass.py` - Existing unit test example
- `src/txtpack/cli.py` - Main CLI implementation with Typer
- `pyproject.toml` - pytest configuration and test discovery settings
- `justfile` - Development commands including `just test` and `just ci`
- `CONTRIBUTING.md` - Development workflow and quality standards

### External Documentation
- [pytest documentation](https://docs.pytest.org/) - Comprehensive testing framework docs
- [Typer documentation](https://typer.tiangolo.com/) - CLI framework used by txtpack
- [Python subprocess module](https://docs.python.org/3/library/subprocess.html) - For CLI testing implementation

## Key Considerations

### Technical Constraints
- **Byte accuracy**: Tests must verify exact file reconstruction without data loss
- **Cross-platform compatibility**: Tests should work on different operating systems
- **Temporary file management**: Proper cleanup of test artifacts
- **CI pipeline integration**: Tests must pass in automated environment

### Implementation Factors
- **Test data strategy**: Need representative files (text, binary, empty, large)
- **Glob pattern testing**: Real filesystem scenarios with various file patterns
- **Error scenario coverage**: Invalid inputs, missing files, permission issues
- **Performance considerations**: E2E tests inherently slower than unit tests

### Quality Standards
- **Code style consistency**: Follow existing ruff/ty quality standards
- **Test naming**: Clear, descriptive names following project conventions
- **Documentation**: Inline comments only when necessary (project prefers minimal comments)
- **CI integration**: Must pass `just ci` quality gates before merge

### Scope Management
- **Focus on CLI interface**: Test through command-line entry points, not internal APIs
- **Round-trip workflows**: Primary focus on pack → unpack → verify cycles
- **User-facing scenarios**: Test actual workflows users would perform
- **Error message validation**: Ensure user-facing error messages are helpful and accurate
