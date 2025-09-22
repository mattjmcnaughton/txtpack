# Plan: Refactor into Unit Testable Chunks and Add Unit Tests

## Implementation Steps

### Step 1: Set Up Testing Infrastructure
- Add hypothesis dependency to pyproject.toml for property-based testing
- Create module structure in tests/unit/ for organized unit tests
- Set up base test utilities and fixtures for common test patterns
- **Deliverable**: Complete testing infrastructure ready for unit test development

### Step 2: Extract Pattern Matching Module
- Extract `_convert_pattern_to_regex()` and `_find_matching_files()` into `src/txtpack/pattern_matching.py`
- Design as pure functions that take inputs and return outputs without side effects
- Create comprehensive unit tests in `tests/unit/test_pattern_matching.py`
- Implement property-based tests using hypothesis for pattern edge cases
- **Deliverable**: Pure function module for pattern matching with full test coverage

### Step 3: Extract File Operations Module
- Extract file I/O functions into `src/txtpack/file_operations.py`
- Create `read_input_content()`, `write_file_with_delimiters()` as pure functions with I/O abstraction
- Design functions to accept file paths/content and return results without global state
- Create unit tests in `tests/unit/test_file_operations.py` with mock filesystem
- **Deliverable**: Pure function I/O module with abstraction for testing

### Step 4: Extract Delimiter Processing Module
- Extract delimiter functions into `src/txtpack/delimiter_processing.py`
- Move `_parse_file_start_delimiter()`, `_extract_file_content_at_position()` as pure functions
- Functions should operate on strings/bytes and return parsed results
- Create comprehensive unit tests in `tests/unit/test_delimiter_processing.py`
- Implement property-based tests for delimiter edge cases and byte-accuracy
- **Deliverable**: Pure function delimiter processing with comprehensive tests

### Step 5: Extract Content Parsing Module
- Extract `_parse_concatenated_content()` into `src/txtpack/content_parsing.py`
- Design as pure function that takes concatenated content and returns file list
- Create unit tests in `tests/unit/test_content_parsing.py`
- Implement property-based tests for round-trip validation using hypothesis
- **Deliverable**: Pure function content parsing module with round-trip property tests

### Step 6: Create Pipeline Orchestration Module
- Create `src/txtpack/pipeline.py` with `pack_files()` and `unpack_content()` functions
- Compose the extracted modules using function composition patterns
- Design functions that orchestrate the workflow: pattern → files → delimited content → output
- Create unit tests in `tests/unit/test_pipeline.py` focusing on integration of pure functions
- **Deliverable**: Pure function pipeline that composes all modules into complete workflows

### Step 7: Refactor CLI Module
- Refactor `src/txtpack/cli.py` to use pipeline functions
- Maintain exact same external CLI interface and behavior
- Convert CLI functions to thin wrappers that call pipeline functions
- CLI should handle only framework concerns (argument parsing, error display, file writing)
- **Deliverable**: Streamlined CLI module with preserved external interface

### Step 8: Comprehensive Round-Trip Validation
- Create extensive property-based tests for complete pack → unpack workflows
- Implement tests in `tests/unit/test_round_trip_properties.py`
- Use hypothesis strategies for file content, patterns, and edge cases
- Test with unicode, special characters, delimiter-like content, empty files
- **Deliverable**: Comprehensive property-based validation of core functionality

### Step 9: Integration and Quality Assurance
- Run full test suite to ensure all existing e2e tests still pass
- Execute `just ci` to verify all quality gates (lint, format, typecheck, test)
- Verify backward compatibility with existing packed files
- **Deliverable**: Fully refactored codebase passing all quality gates

## Testing Strategy

### Functional Testing Approach
- **Pure function testing**: Each function tested independently with known inputs/outputs
- **No mocking complexity**: Pure functions eliminate need for complex dependency injection
- **Composability testing**: Test function composition in pipeline module
- **Isolation**: Functions tested without side effects or global state

### Property-Based Testing Strategy
- **Round-trip validation**: Use hypothesis to generate arbitrary file sets and verify pack → unpack produces identical results
- **Pattern matching**: Generate various glob patterns and validate regex conversion accuracy
- **Delimiter edge cases**: Test with content that resembles delimiters, special characters, and unicode
- **File content strategies**: Generate content including empty files, large files, binary-like content, and unicode edge cases
- **Function composition**: Test that composed functions maintain properties of individual functions

### Integration Testing
- **Preserve existing e2e tests**: Maintain current test_basic_roundtrip.py as regression safety net
- **CLI interface validation**: Ensure external behavior remains identical
- **Backward compatibility**: Test unpacking of files created with current version
- **Pipeline testing**: Verify function composition produces expected end-to-end results

### Test Organization
- **Unit tests**: `tests/unit/` with one test file per module (test_pattern_matching.py, test_file_operations.py, etc.)
- **Property-based tests**: Integrated within unit tests using hypothesis `@given` decorator
- **Pipeline tests**: Separate test file for testing function composition
- **Test utilities**: Shared fixtures and data generators in `tests/unit/conftest.py`

### Quality Gates
- **Test execution**: All tests must pass via `pytest`
- **Coverage reporting**: Maintain high coverage for new unit tests
- **Type checking**: Pass `ty` type checking for all refactored modules
- **Code quality**: Pass `ruff` linting and formatting checks
- **CI validation**: Complete `just ci` command must succeed before completion

## Functional Module Design Principles

### Pure Function Guidelines
- **No side effects**: Functions should not modify global state or perform I/O directly
- **Deterministic**: Same inputs always produce same outputs
- **Testable**: Easy to test with known inputs and expected outputs
- **Composable**: Functions can be easily combined to create larger workflows

### I/O Abstraction Strategy
- **Separate I/O from logic**: File operations abstracted through function parameters
- **Dependency injection**: Pass file reading/writing functions as parameters where needed
- **Mockable interfaces**: Enable testing without actual filesystem operations
- **Future extensibility**: Design supports adding HTTP URL support through same interfaces
