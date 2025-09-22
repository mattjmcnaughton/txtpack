# Research: Refactor into Unit Testable Chunks and Add Unit Tests

## Issue Context
Issue #7: chore: refactor codebase for modularization and unit testability

The current txtpack implementation consists of a single 385-line CLI module containing all functionality - file pattern matching, delimiter processing, I/O operations, and command handling. This monolithic structure makes unit testing difficult and requires comprehensive refactoring to improve modularity and enable comprehensive testing.

## Codebase Context

### Current Architecture
- **Single module design**: All functionality in `src/txtpack/cli.py` (385 lines)
- **Tech stack**: Typer for CLI, structlog for logging, Python 3.11+
- **Existing functionality**:
  - Pack command: finds files by pattern, writes with byte-accurate delimiters
  - Unpack command: parses delimited content, reconstructs original files
  - Round-trip compatibility with byte-accurate parsing

### Current Code Organization
- `src/txtpack/main.py`: Simple entry point importing CLI app
- `src/txtpack/cli.py`: Monolithic module with all logic mixed together
- `tests/e2e/`: Comprehensive end-to-end tests with good coverage
- `tests/unit/`: Only contains `test_always_pass.py` placeholder

### Key Functions to Refactor
Current functions that need extraction and modularization:
- `_convert_pattern_to_regex()`: Pattern matching logic
- `_find_matching_files()`: File discovery
- `_write_file_with_delimiters()`, `_read_input_content()`: I/O operations
- `_parse_file_start_delimiter()`, `_extract_file_content_at_position()`: Delimiter parsing
- `_parse_concatenated_content()`: Content parsing logic

### Configuration and Testing Setup
- **Development workflow**: Uses justfile with `just ci` (lint, format-check, typecheck, test)
- **Testing**: pytest configured in pyproject.toml
- **Quality tools**: ruff for linting/formatting, ty for type checking

## External Resources

### Pytest Documentation and Best Practices
- **Core pytest concepts**: Function-based tests with normal assert statements, extensive fixture system for dependency injection
- **Fixture patterns**: Parameterized fixtures, fixture scopes (function, module, session), dependency injection between fixtures
- **Advanced features**: pytest.param for conditional test skipping, pytest-mock integration for cleaner mocking

### Hypothesis Property-Based Testing
- **Core concepts**: `@given` decorator with strategies for generating test data
- **Strategy composition**: `st.lists()`, `st.integers()`, `st.text()` for various data types
- **Round-trip testing**: Perfect fit for txtpack's concat/split workflow validation
- **Key strategies for txtpack**:
  - `st.text()` for file content generation including edge cases
  - `st.lists(st.text())` for multiple file scenarios
  - Custom strategies for valid filenames and delimiter edge cases

### Refactoring for Testability Best Practices
- **Separation of concerns**: Divide program into distinct sections each handling specific responsibility
- **Dependency injection**: Objects receive dependencies from external sources rather than creating them
- **Testable design patterns**:
  - Extract I/O operations to enable mocking
  - Separate business logic from framework code (CLI layer)
  - Create abstraction layers for filesystem operations
- **Incremental refactoring**: Make small changes supported by comprehensive test suite

## Domain Knowledge

### Key Testing Patterns for txtpack
1. **Round-trip property testing**: Essential for validating that pack → unpack produces identical files
2. **File I/O abstraction**: Enable testing without actual file system operations
3. **Pattern matching isolation**: Test glob-to-regex conversion independently
4. **Delimiter parsing validation**: Test byte-accurate parsing with edge cases
5. **Error handling**: Test various failure scenarios (invalid patterns, missing files, corrupted delimiters)

### Hypothesis Strategies for txtpack
- **File content generation**: Including unicode, special characters, delimiter-like content
- **Pattern generation**: Valid glob patterns and edge cases
- **Multi-file scenarios**: Various combinations of file names and content
- **Edge cases**: Empty files, very large files, special characters in filenames

### Python Testing Architecture Patterns
- **Repository pattern**: Abstract file system operations for testability
- **Strategy pattern**: Separate pattern matching algorithms
- **Command pattern**: Isolate CLI commands from business logic
- **Factory pattern**: Create test data and mock objects consistently

## Related Files & References
- `goal.md`: Comprehensive task definition and scope
- `tests/e2e/test_basic_roundtrip.py`: Existing test patterns to maintain compatibility with
- `pyproject.toml`: Current pytest configuration and dependency setup
- `justfile`: Development workflow commands including quality gates
- `CONTRIBUTING.md`: Commit format and workflow guidelines

## Key Considerations

### Backward Compatibility Requirements
- External CLI interface must remain unchanged
- All existing functionality must work identically
- Delimiter format cannot change (affects round-trip compatibility)
- Command line arguments and behavior must be preserved

### Testing Strategy Design
- **Unit tests**: Focus on individual components (pattern matching, parsing, I/O abstraction)
- **Property-based tests**: Use hypothesis for round-trip validation and edge case discovery
- **Integration tests**: Maintain existing e2e tests for CLI behavior validation
- **Mock strategies**: Abstract file system operations to enable isolated testing

### Dependencies and Constraints
- Add hypothesis library for property-based testing
- Maintain existing tech stack (Typer, structlog)
- Follow existing code quality standards (ruff, ty type checking)
- Must pass all quality gates (`just ci`) before completion

### Refactoring Approach
- **Incremental extraction**: Move functions to focused modules one at a time
- **Test-first approach**: Write unit tests for extracted components
- **Maintain test coverage**: Ensure comprehensive testing throughout refactoring
- **Preserve existing tests**: Keep e2e tests as regression safety net

## Upcoming Work

### Current Open Issues
Based on the GitHub issue tracker, there are additional enhancements planned after the current refactoring work:

#### Issue #5: HTTP/HTTPS URL Support (Enhancement)
- **Scope**: Extend pack/unpack commands to support remote files via HTTP/HTTPS URLs
- **Key requirements**:
  - Unpack from remote URLs: `unpack https://example.com/bundle.txt`
  - Pack from mixed local/remote sources
  - Network error handling and URL validation
- **Technical considerations**:
  - URL detection vs local paths
  - HTTP library integration (requests/httpx)
  - Temporary file management for downloads
  - Streaming for large files
- **Impact on current refactoring**: Will benefit significantly from modular architecture, particularly:
  - I/O abstraction layer will need to support URL-based inputs
  - File reading/writing operations should be easily extensible
  - Error handling patterns established in refactoring will support network errors

#### Issue #3: Checksum Validation (Enhancement)
- **Scope**: Add MD5/SHA256 checksum validation for enhanced file integrity
- **Key requirements**:
  - Calculate checksums during pack operation
  - Enhanced delimiter format: `--- FILE: filename.md (123 bytes, sha256:abc123...) ---`
  - Verify checksums during unpack with mismatch reporting
  - Backward compatibility with existing packed files
- **Technical considerations**:
  - Configurable hash algorithms
  - Performance impact on large files
  - Graceful degradation for files without checksums
- **Impact on current refactoring**: Directly benefits from modular approach:
  - Delimiter parsing/generation logic needs to be easily extensible
  - Checksum calculation can be a separate, testable module
  - File processing pipeline should support pluggable validation steps

### Architectural Implications for Refactoring
The planned features inform the refactoring strategy:

1. **I/O Abstraction Priority**: The HTTP URL support feature makes I/O abstraction even more critical, as the system will need to handle both local files and remote URLs through a unified interface

2. **Extensible Delimiter Format**: The checksum validation feature requires the delimiter parsing system to be easily extensible to support additional metadata fields

3. **Plugin Architecture Consideration**: Both features suggest the refactored architecture should support extensibility through composition rather than modification

4. **Error Handling Framework**: Network operations and checksum validation will require robust error handling patterns that should be established during the refactoring

5. **Configuration System**: Future features will likely require configuration options (hash algorithms, network timeouts, etc.), suggesting the need for a configuration abstraction layer
