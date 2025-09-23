# Plan: Add Checksum Validation for File Integrity

## Implementation Steps

### Step 1: Extend Configuration System
- Add checksum algorithm option to `BundlerConfig` dataclass in `src/txtpack/config.py`
- Support `md5`, `sha256`, and `none` (default for backward compatibility) algorithm options
- Add CLI flag `--checksum-algorithm` to both `concat` and `split` commands in `src/txtpack/cli.py`
- **Deliverable**: Configuration system supports checksum algorithm selection with backward-compatible defaults

### Step 2: Enhance Delimiter Format
- Modify `create_file_start_delimiter()` in `src/txtpack/delimiter_processing.py` to include checksum when algorithm is specified
- Update delimiter format from `--- FILE: filename.txt (123 bytes) ---` to `--- FILE: filename.txt (123 bytes) [algorithm:checksum] ---`
- Ensure checksum field is optional to maintain backward compatibility
- **Deliverable**: New delimiter format supports embedded checksums while remaining backward compatible

### Step 3: Implement Checksum Calculation
- Create `calculate_file_checksum()` function in `src/txtpack/delimiter_processing.py` using Python's `hashlib`
- Support MD5 and SHA256 algorithms with streaming computation for large files
- Integrate checksum calculation into the pack operation in `pipeline.py`
- **Deliverable**: Reliable checksum calculation integrated into file packing workflow

### Step 4: Update Delimiter Parsing
- Enhance `parse_file_start_delimiter()` in `src/txtpack/delimiter_processing.py` to extract checksum information
- Gracefully handle delimiters both with and without checksum fields
- Return checksum data along with filename and byte count for validation
- **Deliverable**: Delimiter parsing supports both legacy and checksum-enhanced formats

### Step 5: Implement Checksum Validation
- Create `validate_file_checksum()` function in `src/txtpack/delimiter_processing.py`
- Integrate validation into `extract_next_file()` function when checksums are present
- Add appropriate error handling for checksum mismatches vs missing checksums
- Update `unpack_content()` in `pipeline.py` to perform validation when checksums are available
- **Deliverable**: Complete checksum validation during unpack operations with proper error handling

### Step 6: Add CLI Options for Validation Control
- Add `--verify-checksums` flag to `split` command for strict validation mode
- Implement warning vs error behavior based on validation mode
- Provide clear error messages distinguishing corruption from missing checksum scenarios
- **Deliverable**: User-controllable validation behavior through CLI options

## Testing Strategy

### Unit Testing
- **Checksum Calculation**: Test MD5 and SHA256 calculation accuracy against known test vectors
- **Delimiter Format**: Test parsing and creation of both legacy and checksum-enhanced delimiters
- **Validation Logic**: Test checksum validation with correct, incorrect, and missing checksums
- **Configuration**: Test algorithm selection and CLI flag parsing
- **Error Handling**: Test proper exception raising for various failure scenarios

### Property-Based Testing
- **Round-trip Integrity**: Use Hypothesis to generate files and verify pack→unpack preserves content exactly
- **Checksum Consistency**: Verify the same file always produces the same checksum
- **Algorithm Coverage**: Test both MD5 and SHA256 across various file types and sizes
- **Backward Compatibility**: Ensure existing packed files without checksums continue to work

### Integration Testing
- **CLI Workflow**: End-to-end testing of checksum-enabled pack and unpack operations
- **Mixed Format**: Test unpacking content that mixes files with and without checksums
- **Corruption Detection**: Intentionally corrupt packed content to verify detection capability
- **Performance**: Verify checksum calculation doesn't significantly impact processing time

### Edge Case Testing
- **Large Files**: Test streaming checksum calculation on files larger than available memory
- **Unicode Content**: Ensure checksum calculation works correctly with various character encodings
- **Delimiter Content**: Test files containing text that resembles delimiter patterns
- **Empty Files**: Verify checksum handling for zero-byte files
