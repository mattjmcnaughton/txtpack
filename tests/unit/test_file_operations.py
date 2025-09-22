"""Unit tests for file operations module.

Note: These tests interact with the real filesystem using temporary directories.
While file I/O could be considered an "external dependency", we treat these as
unit tests because:
1. File operations are core functionality that must work reliably with real filesystem
2. Temporary directories provide proper isolation between tests
3. The I/O abstraction (FileReader/FileWriter protocols) allows mocking at higher levels
4. This follows common Python testing patterns (pytest tmp_path, pathlib tests, etc.)
"""

from unittest.mock import Mock, patch

import pytest
from hypothesis import given

from txtpack.file_operations import (
    ensure_directory_exists,
    get_file_byte_count,
    read_file_content,
    read_input_content,
    read_multiple_files,
    write_file_content,
)
from .conftest import file_content_strategy


class TestReadFileContent:
    """Test file reading functionality."""

    def test_read_existing_file(self, temp_dir):
        """Test reading content from existing file."""
        test_file = temp_dir / "test.txt"
        expected_content = "Hello, world!\nLine 2"
        test_file.write_text(expected_content, encoding="utf-8")

        result = read_file_content(test_file)
        assert result == expected_content

    def test_read_empty_file(self, temp_dir):
        """Test reading empty file."""
        test_file = temp_dir / "empty.txt"
        test_file.write_text("", encoding="utf-8")

        result = read_file_content(test_file)
        assert result == ""

    def test_read_unicode_file(self, temp_dir):
        """Test reading file with unicode content."""
        test_file = temp_dir / "unicode.txt"
        unicode_content = "Hello 🌍! 测试 content"
        test_file.write_text(unicode_content, encoding="utf-8")

        result = read_file_content(test_file)
        assert result == unicode_content

    def test_read_nonexistent_file(self, temp_dir):
        """Test error handling for nonexistent file."""
        nonexistent_file = temp_dir / "does_not_exist.txt"

        with pytest.raises(IOError, match="Failed to read file"):
            read_file_content(nonexistent_file)


class TestWriteFileContent:
    """Test file writing functionality."""

    def test_write_file_content(self, temp_dir):
        """Test writing content to file."""
        test_file = temp_dir / "output.txt"
        content = "Hello, world!"

        write_file_content(test_file, content)

        assert test_file.exists()
        assert test_file.read_text(encoding="utf-8") == content

    def test_write_empty_content(self, temp_dir):
        """Test writing empty content."""
        test_file = temp_dir / "empty.txt"

        write_file_content(test_file, "")

        assert test_file.exists()
        assert test_file.read_text(encoding="utf-8") == ""

    def test_write_unicode_content(self, temp_dir):
        """Test writing unicode content."""
        test_file = temp_dir / "unicode.txt"
        unicode_content = "Hello 🌍! 测试 content"

        write_file_content(test_file, unicode_content)

        assert test_file.read_text(encoding="utf-8") == unicode_content

    def test_overwrite_existing_file(self, temp_dir):
        """Test overwriting existing file."""
        test_file = temp_dir / "overwrite.txt"
        test_file.write_text("original content", encoding="utf-8")

        new_content = "new content"
        write_file_content(test_file, new_content)

        assert test_file.read_text(encoding="utf-8") == new_content


class TestReadInputContent:
    """Test input content reading functionality."""

    def test_read_from_file(self, temp_dir):
        """Test reading content from specified file."""
        test_file = temp_dir / "input.txt"
        content = "Input file content"
        test_file.write_text(content, encoding="utf-8")

        result = read_input_content(str(test_file))
        assert result == content

    def test_read_from_stdin_with_reader(self):
        """Test reading from stdin using custom reader."""
        stdin_content = "stdin content"
        mock_stdin_reader = Mock(return_value=stdin_content)

        result = read_input_content(stdin_reader=mock_stdin_reader)

        assert result == stdin_content
        mock_stdin_reader.assert_called_once()

    @patch("txtpack.file_operations.sys.stdin")
    def test_read_from_stdin_default(self, mock_stdin):
        """Test reading from stdin using default sys.stdin."""
        stdin_content = "default stdin content"
        mock_stdin.read.return_value = stdin_content

        result = read_input_content()

        assert result == stdin_content
        mock_stdin.read.assert_called_once()

    def test_read_nonexistent_input_file(self):
        """Test error handling for nonexistent input file."""
        with pytest.raises(IOError):
            read_input_content("/does/not/exist.txt")


class TestGetFileByteCount:
    """Test byte count calculation."""

    def test_ascii_content_byte_count(self):
        """Test byte count for ASCII content."""
        content = "Hello, world!"
        result = get_file_byte_count(content)
        assert result == len(content.encode("utf-8"))
        assert result == 13  # ASCII characters are 1 byte each

    def test_unicode_content_byte_count(self):
        """Test byte count for unicode content."""
        content = "Hello 🌍!"
        result = get_file_byte_count(content)
        expected = len(content.encode("utf-8"))
        assert result == expected
        assert result > len(content)  # Unicode characters take more bytes

    def test_empty_content_byte_count(self):
        """Test byte count for empty content."""
        result = get_file_byte_count("")
        assert result == 0

    @given(content=file_content_strategy())
    def test_byte_count_property(self, content):
        """Property test: byte count should match UTF-8 encoding length."""
        result = get_file_byte_count(content)
        expected = len(content.encode("utf-8"))
        assert result == expected


class TestEnsureDirectoryExists:
    """Test directory creation functionality."""

    def test_create_new_directory(self, temp_dir):
        """Test creating new directory."""
        new_dir = temp_dir / "new_directory"
        assert not new_dir.exists()

        ensure_directory_exists(new_dir)

        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_create_nested_directories(self, temp_dir):
        """Test creating nested directory structure."""
        nested_dir = temp_dir / "level1" / "level2" / "level3"
        assert not nested_dir.exists()

        ensure_directory_exists(nested_dir)

        assert nested_dir.exists()
        assert nested_dir.is_dir()

    def test_existing_directory_no_error(self, temp_dir):
        """Test that existing directory doesn't cause error."""
        existing_dir = temp_dir / "existing"
        existing_dir.mkdir()

        # Should not raise error
        ensure_directory_exists(existing_dir)

        assert existing_dir.exists()
        assert existing_dir.is_dir()


class TestReadMultipleFiles:
    """Test reading multiple files functionality."""

    def test_read_multiple_files_default_reader(self, temp_dir):
        """Test reading multiple files with default reader."""
        # Create test files
        files_data = [
            ("file1.txt", "Content 1"),
            ("file2.txt", "Content 2"),
            ("file3.txt", "Content 3"),
        ]

        file_paths = []
        for filename, content in files_data:
            file_path = temp_dir / filename
            file_path.write_text(content, encoding="utf-8")
            file_paths.append(file_path)

        result = read_multiple_files(file_paths)

        assert len(result) == 3
        assert result == files_data

    def test_read_multiple_files_custom_reader(self, temp_dir):
        """Test reading multiple files with custom reader."""
        file_paths = [temp_dir / "file1.txt", temp_dir / "file2.txt"]

        # Create a mock reader that returns modified content
        mock_reader = Mock(side_effect=lambda path: f"mock_{path.name}")

        result = read_multiple_files(file_paths, file_reader=mock_reader)

        assert len(result) == 2
        assert result[0] == ("file1.txt", "mock_file1.txt")
        assert result[1] == ("file2.txt", "mock_file2.txt")
        assert mock_reader.call_count == 2

    def test_read_empty_file_list(self):
        """Test reading empty list of files."""
        result = read_multiple_files([])
        assert result == []
