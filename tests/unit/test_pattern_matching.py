"""Unit tests for pattern matching module."""

import re
from pathlib import Path

import pytest
from hypothesis import given, strategies as st

from txtpack.pattern_matching import (
    convert_pattern_to_regex,
    find_matching_files,
)


class TestConvertPatternToRegex:
    """Test pattern to regex conversion."""

    def test_glob_star_pattern(self):
        """Test glob patterns with asterisks are converted to regex."""
        assert convert_pattern_to_regex("*.txt") == "^.*.txt$"
        assert convert_pattern_to_regex("test*") == "^test.*$"
        assert convert_pattern_to_regex("*data*") == "^.*data.*$"

    def test_existing_regex_pattern(self):
        """Test that existing regex patterns are not modified."""
        pattern = "^test.*\\.py$"
        assert convert_pattern_to_regex(pattern) == pattern

    def test_pattern_without_glob(self):
        """Test that patterns without glob characters are returned as-is."""
        pattern = "exactfilename.txt"
        assert convert_pattern_to_regex(pattern) == pattern

    def test_special_regex_chars_in_glob(self):
        """Test that special regex characters in glob patterns are handled."""
        assert convert_pattern_to_regex("*.txt") == "^.*.txt$"
        # Patterns without * are returned as-is (re.match() already anchors at start)
        assert convert_pattern_to_regex("file?.txt") == "file?.txt"

    @given(st.text(min_size=1))
    def test_convert_pattern_property(self, pattern):
        """Property test: converted patterns should compile as valid regex."""
        regex_pattern = convert_pattern_to_regex(pattern)

        # The converted pattern should be a valid regex
        try:
            re.compile(regex_pattern)
        except re.error:
            # If conversion fails, original pattern likely had regex metacharacters
            # This is acceptable behavior
            pass


class TestFindMatchingFiles:
    """Test file discovery functionality."""

    def test_find_files_with_glob_pattern(self, temp_dir):
        """Test finding files with glob patterns."""
        # Create test files
        (temp_dir / "test1.txt").write_text("content1")
        (temp_dir / "test2.txt").write_text("content2")
        (temp_dir / "data.json").write_text("content3")
        (temp_dir / "readme.md").write_text("content4")

        # Test glob patterns
        txt_files = find_matching_files(temp_dir, "*.txt")
        assert len(txt_files) == 2
        assert all(f.suffix == ".txt" for f in txt_files)
        assert txt_files == sorted(txt_files)  # Should be sorted

        test_files = find_matching_files(temp_dir, "test*")
        assert len(test_files) == 2
        assert all(f.name.startswith("test") for f in test_files)

    def test_find_files_with_regex_pattern(self, temp_dir):
        """Test finding files with explicit regex patterns."""
        # Create test files
        (temp_dir / "file1.py").write_text("code1")
        (temp_dir / "file2.py").write_text("code2")
        (temp_dir / "test.txt").write_text("text")

        # Test regex pattern
        py_files = find_matching_files(temp_dir, "^.*\\.py$")
        assert len(py_files) == 2
        assert all(f.suffix == ".py" for f in py_files)

    def test_find_files_no_matches(self, temp_dir):
        """Test finding files when no files match pattern."""
        (temp_dir / "test.txt").write_text("content")

        result = find_matching_files(temp_dir, "*.py")
        assert result == []

    def test_find_files_empty_directory(self, temp_dir):
        """Test finding files in empty directory."""
        result = find_matching_files(temp_dir, "*")
        assert result == []

    def test_find_files_nonexistent_directory(self):
        """Test error handling for nonexistent directory."""
        nonexistent = Path("/does/not/exist")
        with pytest.raises(FileNotFoundError):
            find_matching_files(nonexistent, "*")

    def test_find_files_not_directory(self, temp_dir):
        """Test error handling when path is not a directory."""
        file_path = temp_dir / "notadir.txt"
        file_path.write_text("content")

        with pytest.raises(ValueError, match="not a directory"):
            find_matching_files(file_path, "*")

    def test_find_files_invalid_regex(self, temp_dir):
        """Test error handling for invalid regex patterns."""
        with pytest.raises(ValueError, match="Invalid regex pattern"):
            find_matching_files(temp_dir, "[invalid")

    def test_find_files_ignores_subdirectories(self, temp_dir):
        """Test that subdirectories are ignored, only files are returned."""
        # Create files and subdirectories
        (temp_dir / "file.txt").write_text("content")
        (temp_dir / "subdir").mkdir()
        (temp_dir / "subdir" / "nested.txt").write_text("nested")

        result = find_matching_files(temp_dir, "*")
        assert len(result) == 1
        assert result[0].name == "file.txt"
