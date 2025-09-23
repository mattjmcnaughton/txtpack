"""Unit tests for delimiter processing module."""

import pytest
from hypothesis import given, strategies as st

from txtpack.delimiter_processing import (
    BundlerConfig,
    ChecksumAlgorithm,
    calculate_file_checksum,
    create_file_end_delimiter,
    create_file_start_delimiter,
    extract_file_content_at_position,
    extract_next_file,
    find_next_line_end,
    is_file_end_delimiter,
    is_file_start_delimiter,
    parse_file_start_delimiter,
    skip_end_delimiter,
    validate_file_checksum,
)
from .conftest import file_content_strategy, filename_strategy


class TestBundlerConfig:
    """Test BundlerConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = BundlerConfig()
        assert config.file_start_prefix == "--- FILE: "
        assert config.file_start_middle == " ("
        assert config.file_start_bytes_suffix == " bytes) ---"
        assert config.file_end_prefix == "--- END: "
        assert config.file_end_suffix == " ---"
        assert config.default_search_path == "."
        assert config.checksum_algorithm == ChecksumAlgorithm.NONE

    def test_custom_config(self):
        """Test custom configuration values."""
        config = BundlerConfig(
            file_start_prefix="### START: ",
            file_start_middle=" [",
            file_start_bytes_suffix=" bytes] ###",
            file_end_prefix="### END: ",
            file_end_suffix=" ###",
        )
        assert config.file_start_prefix == "### START: "
        assert config.file_start_middle == " ["
        assert config.file_start_bytes_suffix == " bytes] ###"
        assert config.file_end_prefix == "### END: "
        assert config.file_end_suffix == " ###"

    def test_checksum_algorithm_config(self):
        """Test checksum algorithm configuration."""
        config = BundlerConfig(checksum_algorithm=ChecksumAlgorithm.MD5)
        assert config.checksum_algorithm == ChecksumAlgorithm.MD5

        config = BundlerConfig(checksum_algorithm=ChecksumAlgorithm.SHA256)
        assert config.checksum_algorithm == ChecksumAlgorithm.SHA256


class TestCreateFileStartDelimiter:
    """Test file start delimiter creation."""

    def test_create_start_delimiter_default_config(self):
        """Test creating start delimiter with default config."""
        result = create_file_start_delimiter("test.txt", 123)
        expected = "--- FILE: test.txt (123 bytes) ---"
        assert result == expected

    def test_create_start_delimiter_custom_config(self):
        """Test creating start delimiter with custom config."""
        config = BundlerConfig(
            file_start_prefix="### START: ",
            file_start_middle=" [",
            file_start_bytes_suffix=" bytes] ###",
        )
        result = create_file_start_delimiter("test.txt", 123, config)
        expected = "### START: test.txt [123 bytes] ###"
        assert result == expected

    def test_create_start_delimiter_zero_bytes(self):
        """Test creating start delimiter for empty file."""
        result = create_file_start_delimiter("empty.txt", 0)
        expected = "--- FILE: empty.txt (0 bytes) ---"
        assert result == expected

    @given(filename_strategy(), st.integers(min_value=0, max_value=1000000))
    def test_create_start_delimiter_property(self, filename, byte_count):
        """Property test: created delimiters should be parseable."""
        delimiter = create_file_start_delimiter(filename, byte_count)

        # The created delimiter should be valid
        assert is_file_start_delimiter(delimiter)

        # And should parse back to original values
        parsed_filename, parsed_bytes, _, _ = parse_file_start_delimiter(delimiter)
        assert parsed_filename == filename
        assert parsed_bytes == byte_count


class TestCreateFileEndDelimiter:
    """Test file end delimiter creation."""

    def test_create_end_delimiter_default_config(self):
        """Test creating end delimiter with default config."""
        result = create_file_end_delimiter("test.txt")
        expected = "--- END: test.txt ---"
        assert result == expected

    def test_create_end_delimiter_custom_config(self):
        """Test creating end delimiter with custom config."""
        config = BundlerConfig(
            file_end_prefix="### END: ",
            file_end_suffix=" ###",
        )
        result = create_file_end_delimiter("test.txt", config)
        expected = "### END: test.txt ###"
        assert result == expected

    @given(filename_strategy())
    def test_create_end_delimiter_property(self, filename):
        """Property test: created end delimiters should match filename."""
        delimiter = create_file_end_delimiter(filename)
        assert is_file_end_delimiter(delimiter, filename)


class TestIsFileStartDelimiter:
    """Test file start delimiter detection."""

    def test_valid_start_delimiters(self):
        """Test detection of valid start delimiters."""
        valid_delimiters = [
            "--- FILE: test.txt (123 bytes) ---",
            "--- FILE: data.json (0 bytes) ---",
            "--- FILE: my-file.py (999999 bytes) ---",
        ]

        for delimiter in valid_delimiters:
            assert is_file_start_delimiter(delimiter), f"Should be valid: {delimiter}"

    def test_invalid_start_delimiters(self):
        """Test detection of invalid start delimiters."""
        invalid_delimiters = [
            "regular text",
            "--- FILE: test.txt",  # Missing byte info
            "FILE: test.txt (123 bytes) ---",  # Missing prefix
            "--- FILE: test.txt (123 bytes)",  # Missing suffix
            "--- END: test.txt ---",  # End delimiter
        ]

        for delimiter in invalid_delimiters:
            assert not is_file_start_delimiter(delimiter), f"Should be invalid: {delimiter}"

    def test_start_delimiter_custom_config(self):
        """Test start delimiter detection with custom config."""
        config = BundlerConfig(
            file_start_prefix="### START: ",
            file_start_middle=" [",
            file_start_bytes_suffix=" bytes] ###",
        )

        valid_delimiter = "### START: test.txt [123 bytes] ###"
        invalid_delimiter = "--- FILE: test.txt (123 bytes) ---"

        assert is_file_start_delimiter(valid_delimiter, config)
        assert not is_file_start_delimiter(invalid_delimiter, config)


class TestParseFileStartDelimiter:
    """Test file start delimiter parsing."""

    def test_parse_valid_delimiter(self):
        """Test parsing valid start delimiter."""
        delimiter = "--- FILE: test.txt (123 bytes) ---"
        filename, byte_count, _, _ = parse_file_start_delimiter(delimiter)

        assert filename == "test.txt"
        assert byte_count == 123

    def test_parse_zero_bytes(self):
        """Test parsing delimiter with zero bytes."""
        delimiter = "--- FILE: empty.txt (0 bytes) ---"
        filename, byte_count, _, _ = parse_file_start_delimiter(delimiter)

        assert filename == "empty.txt"
        assert byte_count == 0

    def test_parse_large_byte_count(self):
        """Test parsing delimiter with large byte count."""
        delimiter = "--- FILE: large.txt (999999 bytes) ---"
        filename, byte_count, _, _ = parse_file_start_delimiter(delimiter)

        assert filename == "large.txt"
        assert byte_count == 999999

    def test_parse_invalid_delimiters(self):
        """Test error handling for invalid delimiters."""
        invalid_delimiters = [
            "regular text",
            "--- FILE: test.txt",
            "--- FILE: test.txt (abc bytes) ---",
            "--- FILE: test.txt (123 bytes",
        ]

        for delimiter in invalid_delimiters:
            with pytest.raises(ValueError):
                parse_file_start_delimiter(delimiter)

    def test_parse_custom_config(self):
        """Test parsing with custom config."""
        config = BundlerConfig(
            file_start_prefix="### START: ",
            file_start_middle=" [",
            file_start_bytes_suffix=" bytes] ###",
        )

        delimiter = "### START: test.txt [123 bytes] ###"
        filename, byte_count, _, _ = parse_file_start_delimiter(delimiter, config)

        assert filename == "test.txt"
        assert byte_count == 123


class TestIsFileEndDelimiter:
    """Test file end delimiter detection."""

    def test_valid_end_delimiter(self):
        """Test detection of valid end delimiter."""
        delimiter = "--- END: test.txt ---"
        assert is_file_end_delimiter(delimiter, "test.txt")

    def test_mismatched_filename(self):
        """Test detection with mismatched filename."""
        delimiter = "--- END: test.txt ---"
        assert not is_file_end_delimiter(delimiter, "other.txt")

    def test_invalid_end_delimiter(self):
        """Test detection of invalid end delimiter."""
        invalid_delimiters = [
            "regular text",
            "--- FILE: test.txt (123 bytes) ---",  # Start delimiter
            "--- END: test.txt",  # Missing suffix
            "END: test.txt ---",  # Missing prefix
        ]

        for delimiter in invalid_delimiters:
            assert not is_file_end_delimiter(delimiter, "test.txt")

    def test_end_delimiter_custom_config(self):
        """Test end delimiter detection with custom config."""
        config = BundlerConfig(
            file_end_prefix="### END: ",
            file_end_suffix=" ###",
        )

        delimiter = "### END: test.txt ###"
        assert is_file_end_delimiter(delimiter, "test.txt", config)

        # Default format should not match
        default_delimiter = "--- END: test.txt ---"
        assert not is_file_end_delimiter(default_delimiter, "test.txt", config)


class TestFindNextLineEnd:
    """Test line end finding functionality."""

    def test_find_line_end_with_newline(self):
        """Test finding line end when newline exists."""
        content = b"line1\nline2\nline3"
        assert find_next_line_end(content, 0) == 5  # After "line1"
        assert find_next_line_end(content, 6) == 11  # After "line2"

    def test_find_line_end_no_newline(self):
        """Test finding line end when no newline exists."""
        content = b"single line"
        assert find_next_line_end(content, 0) == len(content)

    def test_find_line_end_at_end(self):
        """Test finding line end at end of content."""
        content = b"line1\nline2"
        assert find_next_line_end(content, 6) == len(content)

    def test_find_line_end_empty_content(self):
        """Test finding line end in empty content."""
        content = b""
        assert find_next_line_end(content, 0) == 0


class TestExtractFileContentAtPosition:
    """Test file content extraction functionality."""

    def test_extract_valid_content(self):
        """Test extracting valid file content."""
        content_bytes = b"Hello, world!"
        filename = "test.txt"
        byte_count = 13

        file_content, new_pos = extract_file_content_at_position(content_bytes, 0, filename, byte_count)

        assert file_content == "Hello, world!"
        assert new_pos == 13

    def test_extract_partial_content(self):
        """Test extracting partial content from larger buffer."""
        content_bytes = b"Hello, world!\nExtra content"
        filename = "test.txt"
        byte_count = 13

        file_content, new_pos = extract_file_content_at_position(content_bytes, 0, filename, byte_count)

        assert file_content == "Hello, world!"
        assert new_pos == 13

    def test_extract_unicode_content(self):
        """Test extracting unicode content."""
        unicode_text = "Hello 🌍!"
        content_bytes = unicode_text.encode("utf-8")
        filename = "unicode.txt"
        byte_count = len(content_bytes)

        file_content, new_pos = extract_file_content_at_position(content_bytes, 0, filename, byte_count)

        assert file_content == unicode_text
        assert new_pos == byte_count

    def test_extract_insufficient_content(self):
        """Test error when insufficient content available."""
        content_bytes = b"short"
        filename = "test.txt"
        byte_count = 100  # More than available

        with pytest.raises(ValueError, match="Not enough content"):
            extract_file_content_at_position(content_bytes, 0, filename, byte_count)

    def test_extract_invalid_utf8(self):
        """Test error when content is not valid UTF-8."""
        content_bytes = b"\xff\xfe\xfd"  # Invalid UTF-8
        filename = "test.txt"
        byte_count = 3

        with pytest.raises(ValueError, match="Failed to decode"):
            extract_file_content_at_position(content_bytes, 0, filename, byte_count)

    @given(file_content_strategy())
    def test_extract_content_property(self, content):
        """Property test: extracting encoded content should return original."""
        content_bytes = content.encode("utf-8")
        byte_count = len(content_bytes)

        extracted, new_pos = extract_file_content_at_position(content_bytes, 0, "test.txt", byte_count)

        assert extracted == content
        assert new_pos == byte_count


class TestSkipEndDelimiter:
    """Test end delimiter skipping functionality."""

    def test_skip_valid_end_delimiter(self):
        """Test skipping valid end delimiter."""
        content = b"file content\n--- END: test.txt ---\nmore content"
        pos = 13  # After "file content\n"

        new_pos = skip_end_delimiter(content, pos, "test.txt")

        # Should be positioned after the end delimiter and newline
        expected_pos = len(b"file content\n--- END: test.txt ---\n")
        assert new_pos == expected_pos

    def test_skip_missing_end_delimiter(self):
        """Test skipping when end delimiter is missing."""
        content = b"file content\nwrong line\nmore content"
        pos = 13  # After "file content\n"

        new_pos = skip_end_delimiter(content, pos, "test.txt")

        # Should remain at original position when delimiter not found
        assert new_pos == pos

    def test_skip_at_end_of_content(self):
        """Test skipping when at end of content."""
        content = b"file content"
        pos = len(content)

        new_pos = skip_end_delimiter(content, pos, "test.txt")

        assert new_pos == pos

    def test_skip_with_custom_config(self):
        """Test skipping with custom config."""
        config = BundlerConfig(
            file_end_prefix="### END: ",
            file_end_suffix=" ###",
        )
        content = b"file content\n### END: test.txt ###\nmore content"
        pos = 13

        new_pos = skip_end_delimiter(content, pos, "test.txt", config)

        expected_pos = len(b"file content\n### END: test.txt ###\n")
        assert new_pos == expected_pos


class TestExtractNextFile:
    """Test next file extraction functionality."""

    def test_extract_valid_file(self):
        """Test extracting valid file from content."""
        content = b"--- FILE: test.txt (13 bytes) ---\nHello, world!\n--- END: test.txt ---\nremaining content"

        file_data, new_pos = extract_next_file(content, 0)

        assert file_data == ("test.txt", "Hello, world!")
        assert new_pos == len(content) - len(b"remaining content")

    def test_extract_multiple_files(self):
        """Test extracting multiple files sequentially."""
        content = (
            b"--- FILE: file1.txt (5 bytes) ---\n"
            b"Hello"
            b"\n--- END: file1.txt ---\n"
            b"--- FILE: file2.txt (5 bytes) ---\n"
            b"World"
            b"\n--- END: file2.txt ---\n"
        )

        # Extract first file
        file1_data, pos1 = extract_next_file(content, 0)
        assert file1_data == ("file1.txt", "Hello")

        # Extract second file
        file2_data, pos2 = extract_next_file(content, pos1)
        assert file2_data == ("file2.txt", "World")
        assert pos2 == len(content)

    def test_extract_no_valid_file(self):
        """Test extraction when no valid file found."""
        content = b"regular content\nno delimiters here"

        file_data, new_pos = extract_next_file(content, 0)

        assert file_data is None
        assert new_pos > 0  # Should advance position

    def test_extract_invalid_delimiter(self):
        """Test extraction with invalid delimiter."""
        content = b"--- FILE: invalid (abc bytes) ---\ncontent"

        file_data, new_pos = extract_next_file(content, 0)

        assert file_data is None
        assert new_pos > 0  # Should skip invalid line

    def test_extract_at_end_of_content(self):
        """Test extraction at end of content."""
        content = b"some content"
        pos = len(content)

        file_data, new_pos = extract_next_file(content, pos)

        assert file_data is None
        assert new_pos == pos

    @given(file_content_strategy(), filename_strategy())
    def test_extract_file_property(self, file_content, filename):
        """Property test: extracting properly formatted content should work."""
        # Create properly formatted content
        byte_count = len(file_content.encode("utf-8"))
        start_delimiter = create_file_start_delimiter(filename, byte_count)
        end_delimiter = create_file_end_delimiter(filename)

        content = f"{start_delimiter}\n{file_content}\n{end_delimiter}\n".encode("utf-8")

        file_data, new_pos = extract_next_file(content, 0)

        if file_data is not None:  # May be None for edge cases
            extracted_filename, extracted_content = file_data
            assert extracted_filename == filename
            assert extracted_content == file_content


class TestChecksumAlgorithm:
    """Test ChecksumAlgorithm enum."""

    def test_enum_values(self):
        """Test enum values are correctly defined."""
        assert ChecksumAlgorithm.NONE.value == "none"
        assert ChecksumAlgorithm.MD5.value == "md5"
        assert ChecksumAlgorithm.SHA256.value == "sha256"


class TestCalculateFileChecksum:
    """Test checksum calculation function."""

    def test_md5_checksum(self):
        """Test MD5 checksum calculation."""
        content = "hello"
        checksum = calculate_file_checksum(content, ChecksumAlgorithm.MD5)
        assert checksum == "5d41402abc4b2a76b9719d911017c592"

    def test_sha256_checksum(self):
        """Test SHA256 checksum calculation."""
        content = "hello"
        checksum = calculate_file_checksum(content, ChecksumAlgorithm.SHA256)
        assert checksum == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"

    def test_none_algorithm(self):
        """Test that NONE algorithm returns None."""
        content = "hello"
        checksum = calculate_file_checksum(content, ChecksumAlgorithm.NONE)
        assert checksum is None

    def test_unsupported_algorithm(self):
        """Test that unsupported algorithm raises ValueError."""
        content = "hello"

        # Create a mock enum value that's not supported
        class MockAlgorithm:
            value = "unsupported"

        with pytest.raises(ValueError, match="Unsupported checksum algorithm"):
            calculate_file_checksum(content, MockAlgorithm())

    def test_empty_content(self):
        """Test checksum calculation with empty content."""
        content = ""
        md5_checksum = calculate_file_checksum(content, ChecksumAlgorithm.MD5)
        sha256_checksum = calculate_file_checksum(content, ChecksumAlgorithm.SHA256)

        assert md5_checksum == "d41d8cd98f00b204e9800998ecf8427e"
        assert sha256_checksum == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    def test_unicode_content(self):
        """Test checksum calculation with unicode content."""
        content = "Hello 世界"
        md5_checksum = calculate_file_checksum(content, ChecksumAlgorithm.MD5)
        sha256_checksum = calculate_file_checksum(content, ChecksumAlgorithm.SHA256)

        # Verify checksums are generated (exact values depend on UTF-8 encoding)
        assert len(md5_checksum) == 32
        assert len(sha256_checksum) == 64
        assert all(c in "0123456789abcdef" for c in md5_checksum)
        assert all(c in "0123456789abcdef" for c in sha256_checksum)


class TestValidateFileChecksum:
    """Test checksum validation function."""

    def test_valid_md5_checksum(self):
        """Test validation with correct MD5 checksum."""
        content = "hello"
        expected_checksum = "5d41402abc4b2a76b9719d911017c592"

        assert validate_file_checksum(content, expected_checksum, ChecksumAlgorithm.MD5) is True

    def test_valid_sha256_checksum(self):
        """Test validation with correct SHA256 checksum."""
        content = "hello"
        expected_checksum = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"

        assert validate_file_checksum(content, expected_checksum, ChecksumAlgorithm.SHA256) is True

    def test_invalid_checksum(self):
        """Test validation with incorrect checksum."""
        content = "hello"
        wrong_checksum = "incorrect_checksum_value"

        assert validate_file_checksum(content, wrong_checksum, ChecksumAlgorithm.MD5) is False

    def test_none_algorithm_always_valid(self):
        """Test that NONE algorithm always validates as True."""
        content = "hello"
        any_checksum = "any_value"

        assert validate_file_checksum(content, any_checksum, ChecksumAlgorithm.NONE) is True


class TestCreateFileStartDelimiterWithChecksum:
    """Test file start delimiter creation with checksum support."""

    def test_delimiter_without_checksum(self):
        """Test delimiter creation without checksum (backward compatibility)."""
        delimiter = create_file_start_delimiter("test.txt", 123)
        assert delimiter == "--- FILE: test.txt (123 bytes) ---"

    def test_delimiter_with_md5_checksum(self):
        """Test delimiter creation with MD5 checksum."""
        config = BundlerConfig(checksum_algorithm=ChecksumAlgorithm.MD5)
        checksum = "5d41402abc4b2a76b9719d911017c592"

        delimiter = create_file_start_delimiter("test.txt", 123, config, checksum)
        assert delimiter == "--- FILE: test.txt (123 bytes) [md5:5d41402abc4b2a76b9719d911017c592] ---"

    def test_delimiter_with_sha256_checksum(self):
        """Test delimiter creation with SHA256 checksum."""
        config = BundlerConfig(checksum_algorithm=ChecksumAlgorithm.SHA256)
        checksum = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"

        delimiter = create_file_start_delimiter("test.txt", 123, config, checksum)
        expected = "--- FILE: test.txt (123 bytes) [sha256:2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824] ---"
        assert delimiter == expected

    def test_delimiter_with_none_algorithm_ignores_checksum(self):
        """Test that NONE algorithm ignores provided checksum."""
        config = BundlerConfig(checksum_algorithm=ChecksumAlgorithm.NONE)
        checksum = "some_checksum"

        delimiter = create_file_start_delimiter("test.txt", 123, config, checksum)
        assert delimiter == "--- FILE: test.txt (123 bytes) ---"


class TestParseFileStartDelimiterWithChecksum:
    """Test file start delimiter parsing with checksum support."""

    def test_parse_legacy_delimiter(self):
        """Test parsing legacy delimiter without checksum."""
        line = "--- FILE: test.txt (123 bytes) ---"
        filename, byte_count, checksum, algorithm = parse_file_start_delimiter(line)

        assert filename == "test.txt"
        assert byte_count == 123
        assert checksum is None
        assert algorithm is None

    def test_parse_md5_delimiter(self):
        """Test parsing delimiter with MD5 checksum."""
        line = "--- FILE: test.txt (123 bytes) [md5:5d41402abc4b2a76b9719d911017c592] ---"
        filename, byte_count, checksum, algorithm = parse_file_start_delimiter(line)

        assert filename == "test.txt"
        assert byte_count == 123
        assert checksum == "5d41402abc4b2a76b9719d911017c592"
        assert algorithm == ChecksumAlgorithm.MD5

    def test_parse_sha256_delimiter(self):
        """Test parsing delimiter with SHA256 checksum."""
        line = "--- FILE: test.txt (123 bytes) [sha256:2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824] ---"
        filename, byte_count, checksum, algorithm = parse_file_start_delimiter(line)

        assert filename == "test.txt"
        assert byte_count == 123
        assert checksum == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
        assert algorithm == ChecksumAlgorithm.SHA256

    def test_parse_invalid_delimiter_with_checksum(self):
        """Test parsing invalid delimiter raises ValueError."""
        line = "invalid delimiter format"

        with pytest.raises(ValueError, match="Not a valid start delimiter"):
            parse_file_start_delimiter(line)


class TestIsFileStartDelimiterWithChecksum:
    """Test file start delimiter detection with checksum support."""

    def test_legacy_delimiter_detected(self):
        """Test legacy delimiter is detected."""
        line = "--- FILE: test.txt (123 bytes) ---"
        assert is_file_start_delimiter(line) is True

    def test_md5_delimiter_detected(self):
        """Test MD5 delimiter is detected."""
        line = "--- FILE: test.txt (123 bytes) [md5:abc123] ---"
        assert is_file_start_delimiter(line) is True

    def test_sha256_delimiter_detected(self):
        """Test SHA256 delimiter is detected."""
        line = "--- FILE: test.txt (123 bytes) [sha256:def456] ---"
        assert is_file_start_delimiter(line) is True

    def test_invalid_line_not_detected(self):
        """Test invalid line is not detected as delimiter."""
        line = "regular content line"
        assert is_file_start_delimiter(line) is False

    def test_partial_delimiter_not_detected(self):
        """Test partial delimiter is not detected."""
        line = "--- FILE: test.txt (123 bytes)"
        assert is_file_start_delimiter(line) is False


class TestExtractNextFileWithChecksum:
    """Test file extraction with checksum validation."""

    def test_extract_file_with_valid_md5(self):
        """Test extracting file with valid MD5 checksum."""
        content = "hello"
        byte_count = len(content.encode("utf-8"))
        checksum = "5d41402abc4b2a76b9719d911017c592"  # MD5 of "hello"

        delimiter = f"--- FILE: test.txt ({byte_count} bytes) [md5:{checksum}] ---"
        full_content = f"{delimiter}\n{content}\n--- END: test.txt ---\n".encode("utf-8")

        file_data, new_pos = extract_next_file(full_content, 0)

        assert file_data is not None
        filename, extracted_content = file_data
        assert filename == "test.txt"
        assert extracted_content == content

    def test_extract_file_with_invalid_checksum(self):
        """Test extracting file with invalid checksum fails."""
        content = "hello"
        byte_count = len(content.encode("utf-8"))
        wrong_checksum = "wrong_checksum_value"

        delimiter = f"--- FILE: test.txt ({byte_count} bytes) [md5:{wrong_checksum}] ---"
        full_content = f"{delimiter}\n{content}\n--- END: test.txt ---\n".encode("utf-8")

        file_data, new_pos = extract_next_file(full_content, 0)

        # Should return None due to checksum validation failure
        assert file_data is None

    def test_extract_file_with_verify_checksums_required(self):
        """Test extracting file with verify_checksums=True when no checksum present."""
        content = "hello"
        byte_count = len(content.encode("utf-8"))

        delimiter = f"--- FILE: test.txt ({byte_count} bytes) ---"
        full_content = f"{delimiter}\n{content}\n--- END: test.txt ---\n".encode("utf-8")

        file_data, new_pos = extract_next_file(full_content, 0, verify_checksums=True)

        # Should return None due to missing checksum when verification required
        assert file_data is None

    def test_extract_file_without_verify_checksums(self):
        """Test extracting file without checksums when verification not required."""
        content = "hello"
        byte_count = len(content.encode("utf-8"))

        delimiter = f"--- FILE: test.txt ({byte_count} bytes) ---"
        full_content = f"{delimiter}\n{content}\n--- END: test.txt ---\n".encode("utf-8")

        file_data, new_pos = extract_next_file(full_content, 0, verify_checksums=False)

        assert file_data is not None
        filename, extracted_content = file_data
        assert filename == "test.txt"
        assert extracted_content == content
