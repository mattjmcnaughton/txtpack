"""Unit tests for pipeline orchestration module."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from txtpack.delimiter_processing import BundlerConfig, ChecksumAlgorithm
from txtpack.pipeline import pack_files, unpack_content
from .conftest import create_test_files


class TestPackFiles:
    """Test file packing pipeline functionality."""

    def test_pack_single_file(self, temp_dir):
        """Test packing single file."""
        # Create test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello, world!", encoding="utf-8")

        result = pack_files("test.txt", temp_dir)

        # Should contain delimited content
        assert "--- FILE: test.txt (13 bytes) ---" in result
        assert "Hello, world!" in result
        assert "--- END: test.txt ---" in result

    def test_pack_multiple_files(self, temp_dir):
        """Test packing multiple files."""
        # Create test files
        (temp_dir / "file1.txt").write_text("Content 1", encoding="utf-8")
        (temp_dir / "file2.txt").write_text("Content 2", encoding="utf-8")

        result = pack_files("*.txt", temp_dir)

        # Should contain both files
        assert "--- FILE: file1.txt (9 bytes) ---" in result
        assert "Content 1" in result
        assert "--- END: file1.txt ---" in result

        assert "--- FILE: file2.txt (9 bytes) ---" in result
        assert "Content 2" in result
        assert "--- END: file2.txt ---" in result

    def test_pack_no_matching_files(self, temp_dir):
        """Test error when no files match pattern."""
        with pytest.raises(ValueError, match="No files found"):
            pack_files("*.nonexistent", temp_dir)

    def test_pack_nonexistent_directory(self):
        """Test error when search directory doesn't exist."""
        nonexistent_dir = Path("/does/not/exist")
        with pytest.raises(FileNotFoundError):
            pack_files("*", nonexistent_dir)

    def test_pack_with_custom_config(self, temp_dir):
        """Test packing with custom delimiter configuration."""
        config = BundlerConfig(
            file_start_prefix="### START: ",
            file_start_middle=" [",
            file_start_bytes_suffix=" bytes] ###",
            file_end_prefix="### END: ",
            file_end_suffix=" ###",
        )

        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello", encoding="utf-8")

        result = pack_files("test.txt", temp_dir, config)

        assert "### START: test.txt [5 bytes] ###" in result
        assert "Hello" in result
        assert "### END: test.txt ###" in result

    def test_pack_with_custom_reader(self, temp_dir):
        """Test packing with custom file reader."""
        # Create test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("Original content", encoding="utf-8")

        # Mock reader that returns different content
        mock_reader = Mock(return_value="Mocked content")

        result = pack_files("test.txt", temp_dir, file_reader=mock_reader)

        # Should use mocked content
        assert "Mocked content" in result
        assert "Original content" not in result
        mock_reader.assert_called_once_with(test_file)

    def test_pack_empty_file(self, temp_dir):
        """Test packing empty file."""
        empty_file = temp_dir / "empty.txt"
        empty_file.write_text("", encoding="utf-8")

        result = pack_files("empty.txt", temp_dir)

        assert "--- FILE: empty.txt (0 bytes) ---" in result
        assert "--- END: empty.txt ---" in result

    def test_pack_unicode_content(self, temp_dir):
        """Test packing file with unicode content."""
        unicode_file = temp_dir / "unicode.txt"
        unicode_content = "Hello 🌍! 测试"
        unicode_file.write_text(unicode_content, encoding="utf-8")

        result = pack_files("unicode.txt", temp_dir)

        expected_bytes = len(unicode_content.encode("utf-8"))
        assert f"--- FILE: unicode.txt ({expected_bytes} bytes) ---" in result
        assert unicode_content in result


class TestUnpackContent:
    """Test content unpacking pipeline functionality."""

    def test_unpack_single_file(self, temp_dir):
        """Test unpacking single file."""
        content = "--- FILE: test.txt (13 bytes) ---\nHello, world!\n--- END: test.txt ---\n"

        result = unpack_content(content, temp_dir)

        # Should return file data
        assert len(result) == 1
        assert result[0] == ("test.txt", "Hello, world!")

        # Should create actual file
        output_file = temp_dir / "test.txt"
        assert output_file.exists()
        assert output_file.read_text(encoding="utf-8") == "Hello, world!"

    def test_unpack_multiple_files(self, temp_dir):
        """Test unpacking multiple files."""
        content = (
            "--- FILE: file1.txt (9 bytes) ---\n"
            "Content 1"
            "\n--- END: file1.txt ---\n"
            "--- FILE: file2.txt (9 bytes) ---\n"
            "Content 2"
            "\n--- END: file2.txt ---\n"
        )

        result = unpack_content(content, temp_dir)

        # Should return both files
        assert len(result) == 2
        assert result[0] == ("file1.txt", "Content 1")
        assert result[1] == ("file2.txt", "Content 2")

        # Should create actual files
        assert (temp_dir / "file1.txt").read_text(encoding="utf-8") == "Content 1"
        assert (temp_dir / "file2.txt").read_text(encoding="utf-8") == "Content 2"

    def test_unpack_empty_content(self, temp_dir):
        """Test error when content is empty."""
        with pytest.raises(ValueError, match="No valid file delimiters"):
            unpack_content("", temp_dir)

    def test_unpack_invalid_content(self, temp_dir):
        """Test error when content has no valid delimiters."""
        content = "Just some regular text\nwith no delimiters"

        with pytest.raises(ValueError, match="No valid file delimiters"):
            unpack_content(content, temp_dir)

    def test_unpack_to_nonexistent_directory(self, temp_dir):
        """Test unpacking to nonexistent directory (should create it)."""
        nested_dir = temp_dir / "new" / "nested" / "dir"
        content = "--- FILE: test.txt (5 bytes) ---\nHello\n--- END: test.txt ---\n"

        result = unpack_content(content, nested_dir)

        # Should create directory and file
        assert nested_dir.exists()
        assert (nested_dir / "test.txt").read_text(encoding="utf-8") == "Hello"
        assert result == [("test.txt", "Hello")]

    def test_unpack_with_custom_config(self, temp_dir):
        """Test unpacking with custom delimiter configuration."""
        config = BundlerConfig(
            file_start_prefix="### START: ",
            file_start_middle=" [",
            file_start_bytes_suffix=" bytes] ###",
            file_end_prefix="### END: ",
            file_end_suffix=" ###",
        )

        content = "### START: test.txt [5 bytes] ###\nHello\n### END: test.txt ###\n"

        result = unpack_content(content, temp_dir, config)

        assert result == [("test.txt", "Hello")]
        assert (temp_dir / "test.txt").read_text(encoding="utf-8") == "Hello"

    def test_unpack_with_custom_writer(self, temp_dir):
        """Test unpacking with custom file writer."""
        content = "--- FILE: test.txt (5 bytes) ---\nHello\n--- END: test.txt ---\n"

        mock_writer = Mock()

        result = unpack_content(content, temp_dir, file_writer=mock_writer)

        # Should call custom writer
        assert result == [("test.txt", "Hello")]
        mock_writer.assert_called_once_with(temp_dir / "test.txt", "Hello")

    def test_unpack_empty_file(self, temp_dir):
        """Test unpacking empty file."""
        content = "--- FILE: empty.txt (0 bytes) ---\n\n--- END: empty.txt ---\n"

        result = unpack_content(content, temp_dir)

        assert result == [("empty.txt", "")]
        assert (temp_dir / "empty.txt").read_text(encoding="utf-8") == ""

    def test_unpack_unicode_content(self, temp_dir):
        """Test unpacking file with unicode content."""
        unicode_content = "Hello 🌍! 测试"
        byte_count = len(unicode_content.encode("utf-8"))

        content = f"--- FILE: unicode.txt ({byte_count} bytes) ---\n{unicode_content}\n--- END: unicode.txt ---\n"

        result = unpack_content(content, temp_dir)

        assert result == [("unicode.txt", unicode_content)]
        assert (temp_dir / "unicode.txt").read_text(encoding="utf-8") == unicode_content


class TestPackUnpackRoundTrip:
    """Test round-trip compatibility between pack and unpack."""

    def test_simple_round_trip(self, temp_dir):
        """Test packing then unpacking produces identical files."""
        # Create original files
        original_files = [
            ("file1.txt", "Hello, world!"),
            ("file2.md", "# Markdown\nContent"),
            ("data.json", '{"key": "value"}'),
        ]

        create_test_files(temp_dir, original_files)

        # Pack files
        packed_content = pack_files("*", temp_dir)

        # Unpack to new directory
        restore_dir = temp_dir / "restored"
        result = unpack_content(packed_content, restore_dir)

        # Should restore all files with identical content
        assert len(result) == 3
        for filename, expected_content in original_files:
            restored_file = restore_dir / filename
            assert restored_file.exists()
            assert restored_file.read_text(encoding="utf-8") == expected_content


class TestPackFilesWithChecksums:
    """Test file packing with checksum functionality."""

    def test_pack_with_md5_checksum(self, temp_dir):
        """Test packing files with MD5 checksums includes checksum in output."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello", encoding="utf-8")

        config = BundlerConfig(checksum_algorithm=ChecksumAlgorithm.MD5)
        result = pack_files("test.txt", temp_dir, config)

        assert "[md5:" in result
        assert "8b1a9953c4611296a827abf8c47804d7" in result  # MD5 of "Hello"

    def test_pack_with_sha256_checksum(self, temp_dir):
        """Test packing files with SHA256 checksums includes checksum in output."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello", encoding="utf-8")

        config = BundlerConfig(checksum_algorithm=ChecksumAlgorithm.SHA256)
        result = pack_files("test.txt", temp_dir, config)

        assert "[sha256:" in result
        assert "185f8db32271fe25f561a6fc938b2e264306ec304eda518007d1764826381969" in result  # SHA256 of "Hello"

    def test_pack_without_checksum(self, temp_dir):
        """Test packing files without checksums (default behavior)."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello", encoding="utf-8")

        config = BundlerConfig(checksum_algorithm=ChecksumAlgorithm.NONE)
        result = pack_files("test.txt", temp_dir, config)

        assert "[md5:" not in result
        assert "[sha256:" not in result
        assert "--- FILE: test.txt (5 bytes) ---" in result


class TestUnpackContentWithChecksums:
    """Test content unpacking with checksum validation."""

    def test_unpack_with_valid_checksums(self, temp_dir):
        """Test unpacking content with valid checksums succeeds."""
        content = """--- FILE: test.txt (5 bytes) [md5:8b1a9953c4611296a827abf8c47804d7] ---
Hello
--- END: test.txt ---
"""

        result = unpack_content(content, temp_dir)
        assert len(result) == 1
        assert result[0] == ("test.txt", "Hello")

    def test_unpack_with_verify_checksums_required(self, temp_dir):
        """Test unpacking with verify_checksums=True requires checksums."""
        content = """--- FILE: test.txt (5 bytes) ---
Hello
--- END: test.txt ---
"""

        result = unpack_content(content, temp_dir, verify_checksums=True)
        assert len(result) == 0  # Should fail due to missing checksum
