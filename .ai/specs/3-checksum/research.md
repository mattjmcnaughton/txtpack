# Research: Add Checksum Validation for File Integrity

## Issue Context
Issue #3: feat: add checksum validation for file integrity

This enhancement adds checksum validation (MD5 or SHA256) to provide stronger file integrity verification beyond current byte count validation. The implementation must extend the existing delimiter format while maintaining full backward compatibility with existing packed files.

## Codebase Context

### Current Architecture
- **Tech Stack**: Python 3.11+, Typer for CLI, structlog for logging, uv for package management
- **Structure**: Clean separation between CLI (`cli.py`), business logic (`pipeline.py`), and utilities (`delimiter_processing.py`)
- **Testing**: Comprehensive unit tests with property-based testing using Hypothesis, plus E2E tests

### Current Delimiter Format
```
--- FILE: filename.txt (123 bytes) ---
[exactly 123 bytes of file content]
--- END: filename.txt ---
```

### Key Implementation Points
- **`delimiter_processing.py`**: Contains `create_file_start_delimiter()`, `parse_file_start_delimiter()`, and `extract_next_file()` functions that would need enhancement
- **`pipeline.py`**: High-level `pack_files()` and `unpack_content()` orchestration functions
- **`BundlerConfig`**: Dataclass for configuration that could accommodate checksum settings
- **Byte-accurate parsing**: Uses UTF-8 byte counts for precise content extraction with validation
- **Pure function design**: All validation functions are side-effect-free and easily testable

### Error Handling Patterns
- **ValueError**: Used for pattern validation, parsing errors, no files found
- **FileNotFoundError**: Missing directories or files
- **IOError**: File read/write failures
- **UnicodeDecodeError**: Invalid UTF-8 content
- CLI-level exception handling with structured logging and meaningful error messages

### Testing Patterns
- **Property-based testing**: Hypothesis strategies for generating test data
- **Round-trip testing**: Ensures pack/unpack cycles preserve data exactly
- **Protocol-based testing**: FileReader/FileWriter protocols for dependency injection
- **Edge case coverage**: Unicode, special characters, delimiter-like content in files

## External Resources

### Python Cryptographic Libraries
- **hashlib (stdlib)**: Provides MD5, SHA256, and other hash algorithms
  - `hashlib.md5()`, `hashlib.sha256()` for checksum calculation
  - Documentation: https://docs.python.org/3/library/hashlib.html

### Best Practices for File Integrity
- **NIST Guidelines**: Cryptographic hash standards and recommendations
- **Common Hash Formats**: Hex encoding standard for displaying checksums
- **Backward Compatibility Patterns**: Graceful degradation when features are missing

### Delimiter Format Design
- **RFC-style delimiters**: Industry patterns for embedding metadata in text streams
- **Human-readable formats**: Balance between machine parsing and human inspection
- **Version tolerance**: Designing formats that can evolve while maintaining compatibility

## Domain Knowledge

### Cryptographic Hash Functions
- **MD5**: Fast but cryptographically weak, still useful for integrity checking (128-bit)
- **SHA256**: Cryptographically strong, recommended for security-sensitive applications (256-bit)
- **Hash collision**: Extremely unlikely for accidental corruption detection
- **Performance**: MD5 faster, SHA256 more secure; both suitable for file integrity

### File Integrity Concepts
- **Checksums vs signatures**: Checksums detect corruption, signatures detect tampering
- **Round-trip validation**: Pack → unpack should produce bit-identical files
- **Graceful degradation**: Handle missing checksums without breaking existing functionality

### CLI Design Patterns
- **Progressive enhancement**: New features shouldn't break existing workflows
- **Configuration flags**: Allow users to control checksum behavior
- **Error reporting**: Clear distinction between corruption and missing checksum scenarios

## Related Files & References

### Core Implementation Files
- `src/txtpack/delimiter_processing.py` - Delimiter parsing and creation logic
- `src/txtpack/pipeline.py` - High-level pack/unpack orchestration
- `src/txtpack/cli.py` - Typer-based CLI command structure
- `src/txtpack/config.py` - Configuration classes including `BundlerConfig`

### Testing Files
- `tests/unit/test_delimiter_processing.py` - Delimiter function unit tests
- `tests/unit/test_pipeline.py` - Pipeline workflow unit tests
- `tests/e2e/test_txtpack_cli.py` - End-to-end CLI testing
- `tests/strategies.py` - Hypothesis testing strategies

### Documentation
- `CONTRIBUTING.md` - Development workflow and commit conventions
- `CLAUDE.md` - Project-specific instructions for AI assistance
- `goal.md` - Current implementation goal and scope
- `justfile` - Development commands and quality gates

## Key Considerations

### Backward Compatibility
- **Graceful parsing**: Files without checksums must continue to unpack successfully
- **Optional validation**: Consider `--verify-checksums` flag for strict mode
- **Format evolution**: Design delimiter format to accommodate future enhancements

### Performance Impact
- **Checksum calculation overhead**: Consider file size implications for MD5 vs SHA256
- **Memory usage**: Stream-based hashing for large files vs loading entire content
- **User experience**: Minimal impact on typical file processing workflows

### Error Handling Strategy
- **Checksum mismatch**: Clear error messages distinguishing corruption from algorithm issues
- **Missing checksums**: Graceful fallback without breaking existing packed files
- **Invalid algorithms**: Proper validation of checksum algorithm configuration

### Testing Requirements
- **Round-trip validation**: Pack with checksums → unpack must verify integrity
- **Corruption simulation**: Intentionally corrupt content to test detection
- **Algorithm coverage**: Test both MD5 and SHA256 implementations
- **Backward compatibility**: Ensure existing test files without checksums still pass

### Configuration Design
- **Algorithm selection**: Support both MD5 and SHA256 with reasonable defaults
- **Validation modes**: Optional strict validation vs warning-only modes
- **Format extensibility**: Design configuration to support future hash algorithms
