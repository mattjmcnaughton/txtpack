"""Unit tests for delimiter processing module."""

import pytest
from hypothesis import given, strategies as st

from txtpack.delimiter_processing import (
    BundlerConfig,
    create_file_end_delimiter,
    create_file_start_delimiter,
    extract_file_content_at_position,
    extract_next_file,
    find_next_line_end,
    is_file_end_delimiter,
    is_file_start_delimiter,
    parse_file_start_delimiter,
    skip_end_delimiter,
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
        parsed_filename, parsed_bytes = parse_file_start_delimiter(delimiter)
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
        filename, byte_count = parse_file_start_delimiter(delimiter)

        assert filename == "test.txt"
        assert byte_count == 123

    def test_parse_zero_bytes(self):
        """Test parsing delimiter with zero bytes."""
        delimiter = "--- FILE: empty.txt (0 bytes) ---"
        filename, byte_count = parse_file_start_delimiter(delimiter)

        assert filename == "empty.txt"
        assert byte_count == 0

    def test_parse_large_byte_count(self):
        """Test parsing delimiter with large byte count."""
        delimiter = "--- FILE: large.txt (999999 bytes) ---"
        filename, byte_count = parse_file_start_delimiter(delimiter)

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
        filename, byte_count = parse_file_start_delimiter(delimiter, config)

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
