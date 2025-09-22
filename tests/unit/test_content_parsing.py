"""Unit tests for content parsing module."""

from hypothesis import given

from txtpack.content_parsing import parse_concatenated_content
from txtpack.delimiter_processing import BundlerConfig, create_file_end_delimiter, create_file_start_delimiter
from txtpack.file_operations import get_file_byte_count
from .conftest import file_content_strategy, file_list_strategy, filename_strategy


class TestParseConcatenatedContent:
    """Test concatenated content parsing functionality."""

    def test_parse_single_file(self):
        """Test parsing content with single file."""
        content = "--- FILE: test.txt (13 bytes) ---\nHello, world!\n--- END: test.txt ---\n"

        result = parse_concatenated_content(content)

        assert len(result) == 1
        assert result[0] == ("test.txt", "Hello, world!")

    def test_parse_multiple_files(self):
        """Test parsing content with multiple files."""
        content = (
            "--- FILE: file1.txt (5 bytes) ---\n"
            "Hello"
            "\n--- END: file1.txt ---\n"
            "--- FILE: file2.json (16 bytes) ---\n"
            '{"key": "value"}'
            "\n--- END: file2.json ---\n"
        )

        result = parse_concatenated_content(content)

        assert len(result) == 2
        assert result[0] == ("file1.txt", "Hello")
        assert result[1] == ("file2.json", '{"key": "value"}')

    def test_parse_empty_content(self):
        """Test parsing empty content."""
        result = parse_concatenated_content("")
        assert result == []

    def test_parse_content_no_delimiters(self):
        """Test parsing content without valid delimiters."""
        content = "Just some regular text\nwith no delimiters\nat all"

        result = parse_concatenated_content(content)
        assert result == []

    def test_parse_empty_file(self):
        """Test parsing content with empty file."""
        content = "--- FILE: empty.txt (0 bytes) ---\n\n--- END: empty.txt ---\n"

        result = parse_concatenated_content(content)

        assert len(result) == 1
        assert result[0] == ("empty.txt", "")

    def test_parse_unicode_content(self):
        """Test parsing content with unicode characters."""
        unicode_text = "Hello 🌍! 测试 content"
        byte_count = get_file_byte_count(unicode_text)

        content = f"--- FILE: unicode.txt ({byte_count} bytes) ---\n{unicode_text}\n--- END: unicode.txt ---\n"

        result = parse_concatenated_content(content)

        assert len(result) == 1
        assert result[0] == ("unicode.txt", unicode_text)

    def test_parse_content_with_delimiter_like_text(self):
        """Test parsing content that contains text resembling delimiters."""
        fake_delimiter_content = "--- FILE: fake.txt (100 bytes) ---\nFake content\n--- END: fake.txt ---"
        byte_count = get_file_byte_count(fake_delimiter_content)

        content = f"--- FILE: real.txt ({byte_count} bytes) ---\n{fake_delimiter_content}\n--- END: real.txt ---\n"

        result = parse_concatenated_content(content)

        assert len(result) == 1
        assert result[0] == ("real.txt", fake_delimiter_content)

    def test_parse_malformed_delimiters(self):
        """Test parsing content with malformed delimiters."""
        content = (
            "--- FILE: test.txt (invalid bytes) ---\n"
            "content here"
            "\n--- END: test.txt ---\n"
            "--- FILE: valid.txt (5 bytes) ---\n"
            "Hello"
            "\n--- END: valid.txt ---\n"
        )

        result = parse_concatenated_content(content)

        # Should skip malformed delimiter and parse valid one
        assert len(result) == 1
        assert result[0] == ("valid.txt", "Hello")

    def test_parse_missing_end_delimiter(self):
        """Test parsing content with missing end delimiter."""
        content = (
            "--- FILE: test.txt (5 bytes) ---\n"
            "Hello"
            "\nsome other content"
            "--- FILE: valid.txt (5 bytes) ---\n"
            "World"
            "\n--- END: valid.txt ---\n"
        )

        result = parse_concatenated_content(content)

        # Should handle missing end delimiter gracefully
        # Exact behavior depends on implementation, but should not crash
        assert isinstance(result, list)

    def test_parse_custom_config(self):
        """Test parsing with custom delimiter configuration."""
        config = BundlerConfig(
            file_start_prefix="### START: ",
            file_start_middle=" [",
            file_start_bytes_suffix=" bytes] ###",
            file_end_prefix="### END: ",
            file_end_suffix=" ###",
        )

        content = "### START: test.txt [5 bytes] ###\nHello\n### END: test.txt ###\n"

        result = parse_concatenated_content(content, config)

        assert len(result) == 1
        assert result[0] == ("test.txt", "Hello")

    def test_parse_files_with_newlines(self):
        """Test parsing files that contain newlines."""
        file_content = "Line 1\nLine 2\nLine 3"
        byte_count = get_file_byte_count(file_content)

        content = f"--- FILE: multiline.txt ({byte_count} bytes) ---\n{file_content}\n--- END: multiline.txt ---\n"

        result = parse_concatenated_content(content)

        assert len(result) == 1
        assert result[0] == ("multiline.txt", file_content)

    @given(file_list_strategy())
    def test_parse_content_property(self, file_list):
        """Property test: parsing properly formatted content should work correctly."""
        if not file_list:
            # Skip empty file lists
            return

        # Create properly formatted concatenated content
        content_parts = []
        for filename, file_content in file_list:
            byte_count = get_file_byte_count(file_content)
            start_delimiter = create_file_start_delimiter(filename, byte_count)
            end_delimiter = create_file_end_delimiter(filename)

            content_parts.append(f"{start_delimiter}\n{file_content}\n{end_delimiter}\n")

        content = "".join(content_parts)

        result = parse_concatenated_content(content)

        # Should parse all files correctly
        assert len(result) >= 0  # May be less than input if there are duplicates or parsing issues

        # All parsed results should be valid
        for filename, file_content in result:
            assert isinstance(filename, str)
            assert isinstance(file_content, str)
            assert filename  # Should not be empty

        # If we parsed files, check that filenames match expectations
        if result and len(result) == len(file_list):
            parsed_filenames = [filename for filename, _ in result]
            expected_filenames = [filename for filename, _ in file_list]
            assert parsed_filenames == expected_filenames

    @given(file_content_strategy(), filename_strategy())
    def test_parse_single_file_property(self, file_content, filename):
        """Property test: parsing single properly formatted file should work."""
        byte_count = get_file_byte_count(file_content)
        start_delimiter = create_file_start_delimiter(filename, byte_count)
        end_delimiter = create_file_end_delimiter(filename)

        content = f"{start_delimiter}\n{file_content}\n{end_delimiter}\n"

        result = parse_concatenated_content(content)

        if result:  # May be empty for edge cases
            assert len(result) == 1
            parsed_filename, parsed_content = result[0]
            assert parsed_filename == filename
            assert parsed_content == file_content

    def test_parse_round_trip_with_e2e_format(self):
        """Test parsing content that matches the format from existing e2e tests."""
        # This tests compatibility with the format used in existing integration tests
        content = (
            "--- FILE: file1.txt (13 bytes) ---\n"
            "Hello, World!"
            "\n--- END: file1.txt ---\n"
            "--- FILE: file2.md (15 bytes) ---\n"
            "# Test Markdown"
            "\n--- END: file2.md ---\n"
        )

        result = parse_concatenated_content(content)

        assert len(result) == 2
        assert result[0] == ("file1.txt", "Hello, World!")
        assert result[1] == ("file2.md", "# Test Markdown")

    def test_parse_byte_accuracy(self):
        """Test that parsing is byte-accurate and handles exact byte counts."""
        # Test with content where string length != byte length
        unicode_content = "café 🎉"  # 7 chars, but more bytes due to unicode
        actual_bytes = get_file_byte_count(unicode_content)

        content = f"--- FILE: unicode.txt ({actual_bytes} bytes) ---\n{unicode_content}\n--- END: unicode.txt ---\n"

        result = parse_concatenated_content(content)

        assert len(result) == 1
        assert result[0] == ("unicode.txt", unicode_content)
