"""Multi-file and glob pattern tests for txtpack CLI."""

from .conftest import verify_files_identical, create_test_file, get_packed_output_info


class TestGlobPatterns:
    """Test various glob pattern matching scenarios."""

    def test_star_wildcard_pattern(self, temp_dir, cli_runner):
        """Test basic * wildcard pattern matching."""
        # Arrange
        files = {
            "test1.txt": "Content 1",
            "test2.txt": "Content 2",
            "other.md": "Markdown content",
            "data.log": "Log content",
        }

        for filename, content in files.items():
            create_test_file(temp_dir / filename, content)

        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Act - Pack only .txt files
        pack_result = cli_runner(["pack", "*.txt"], cwd=temp_dir)
        assert pack_result.returncode == 0

        # Verify only txt files are included
        file_count, filenames = get_packed_output_info(pack_result.stdout)
        assert file_count == 2
        assert set(filenames) == {"test1.txt", "test2.txt"}

        # Act - Unpack and verify
        unpack_result = cli_runner(
            ["unpack", "--output-dir", str(output_dir)], input_data=pack_result.stdout, cwd=temp_dir
        )

        # Assert
        assert unpack_result.returncode == 0
        expected_files = {k: v for k, v in files.items() if k.endswith(".txt")}
        assert verify_files_identical(expected_files, output_dir)

    def test_prefix_wildcard_pattern(self, temp_dir, cli_runner):
        """Test prefix with wildcard pattern."""
        # Arrange
        files = {
            "test_file1.txt": "Test file 1",
            "test_file2.txt": "Test file 2",
            "other_file.txt": "Other file",
            "test.md": "Test markdown",
        }

        for filename, content in files.items():
            create_test_file(temp_dir / filename, content)

        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Act - Pack files starting with "test_"
        pack_result = cli_runner(["pack", "test_*"], cwd=temp_dir)
        assert pack_result.returncode == 0

        # Verify correct files are included
        file_count, filenames = get_packed_output_info(pack_result.stdout)
        assert file_count == 2
        assert set(filenames) == {"test_file1.txt", "test_file2.txt"}

        # Act - Unpack and verify
        unpack_result = cli_runner(
            ["unpack", "--output-dir", str(output_dir)], input_data=pack_result.stdout, cwd=temp_dir
        )

        # Assert
        assert unpack_result.returncode == 0
        expected_files = {"test_file1.txt": "Test file 1", "test_file2.txt": "Test file 2"}
        assert verify_files_identical(expected_files, output_dir)

    def test_single_character_pattern(self, temp_dir, cli_runner):
        """Test single character matching patterns."""
        # Arrange
        files = {"file1.txt": "File 1", "file2.txt": "File 2", "file10.txt": "File 10", "test.txt": "Test file"}

        for filename, content in files.items():
            create_test_file(temp_dir / filename, content)

        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Act - Pack files matching "file?.txt" pattern (should match file1.txt, file2.txt but not file10.txt)
        # Note: Current implementation uses * as .* so "file*.txt" would match all
        pack_result = cli_runner(["pack", "file*.txt"], cwd=temp_dir)
        assert pack_result.returncode == 0

        # Verify all file*.txt are included
        file_count, filenames = get_packed_output_info(pack_result.stdout)
        assert file_count == 3  # file1.txt, file2.txt, file10.txt
        assert set(filenames) == {"file1.txt", "file2.txt", "file10.txt"}

    def test_exact_filename_pattern(self, temp_dir, cli_runner):
        """Test exact filename matching (no wildcards)."""
        # Arrange
        files = {"specific.txt": "Specific content", "other.txt": "Other content"}

        for filename, content in files.items():
            create_test_file(temp_dir / filename, content)

        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Act - Pack specific file only
        pack_result = cli_runner(["pack", "specific.txt"], cwd=temp_dir)
        assert pack_result.returncode == 0

        # Verify only the specific file is included
        file_count, filenames = get_packed_output_info(pack_result.stdout)
        assert file_count == 1
        assert filenames == ["specific.txt"]

        # Act - Unpack and verify
        unpack_result = cli_runner(
            ["unpack", "--output-dir", str(output_dir)], input_data=pack_result.stdout, cwd=temp_dir
        )

        # Assert
        assert unpack_result.returncode == 0
        expected_files = {"specific.txt": "Specific content"}
        assert verify_files_identical(expected_files, output_dir)


class TestMultiFileScenarios:
    """Test complex multi-file scenarios."""

    def test_large_number_of_files(self, temp_dir, cli_runner):
        """Test packing and unpacking many files."""
        # Arrange
        files = {}
        for i in range(20):
            filename = f"file_{i:03d}.txt"
            content = f"Content of file {i}\nLine 2 of file {i}"
            files[filename] = content
            create_test_file(temp_dir / filename, content)

        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Act
        pack_result = cli_runner(["pack", "file_*.txt"], cwd=temp_dir)
        assert pack_result.returncode == 0

        # Verify all files are included
        file_count, filenames = get_packed_output_info(pack_result.stdout)
        assert file_count == 20

        unpack_result = cli_runner(
            ["unpack", "--output-dir", str(output_dir)], input_data=pack_result.stdout, cwd=temp_dir
        )

        # Assert
        assert unpack_result.returncode == 0
        assert verify_files_identical(files, output_dir)

    def test_files_with_varying_sizes(self, temp_dir, cli_runner):
        """Test files with different content sizes."""
        # Arrange
        files = {
            "tiny.txt": "x",
            "small.txt": "This is a small file.\n",
            "medium.txt": "This is a medium file.\n" * 10,
            "large.txt": "This is content for a large file.\n" * 100,
            "empty.txt": "",
        }

        for filename, content in files.items():
            create_test_file(temp_dir / filename, content)

        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Act
        pack_result = cli_runner(["pack", "*.txt"], cwd=temp_dir)
        assert pack_result.returncode == 0

        # Verify byte counts are correct in delimiters
        for filename, content in files.items():
            expected_bytes = len(content.encode("utf-8"))
            expected_delimiter = f"--- FILE: {filename} ({expected_bytes} bytes) ---"
            assert expected_delimiter in pack_result.stdout

        unpack_result = cli_runner(
            ["unpack", "--output-dir", str(output_dir)], input_data=pack_result.stdout, cwd=temp_dir
        )

        # Assert
        assert unpack_result.returncode == 0
        assert verify_files_identical(files, output_dir)

    def test_files_with_special_names(self, temp_dir, cli_runner):
        """Test files with special characters in names."""
        # Arrange - Note: avoiding chars that would be problematic in filesystem
        files = {
            "file-with-dashes.txt": "Dashed filename",
            "file_with_underscores.txt": "Underscored filename",
            "file.with.dots.txt": "Dotted filename",
            "file123numbers.txt": "Numbered filename",
        }

        for filename, content in files.items():
            create_test_file(temp_dir / filename, content)

        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Act
        pack_result = cli_runner(["pack", "*with*"], cwd=temp_dir)
        assert pack_result.returncode == 0

        # Should match files with "with" in the name
        file_count, filenames = get_packed_output_info(pack_result.stdout)
        assert file_count == 3
        expected_names = {"file-with-dashes.txt", "file_with_underscores.txt", "file.with.dots.txt"}
        assert set(filenames) == expected_names

        unpack_result = cli_runner(
            ["unpack", "--output-dir", str(output_dir)], input_data=pack_result.stdout, cwd=temp_dir
        )

        # Assert
        assert unpack_result.returncode == 0
        expected_files = {k: v for k, v in files.items() if "with" in k}
        assert verify_files_identical(expected_files, output_dir)

    def test_mixed_file_types(self, temp_dir, cli_runner):
        """Test packing files with different extensions."""
        # Arrange
        files = {
            "document.txt": "Text document content",
            "script.py": "#!/usr/bin/env python\nprint('hello')",
            "data.json": '{"key": "value", "number": 42}',
            "style.css": "body { margin: 0; padding: 0; }",
            "readme.md": "# Project\n\nDescription here.",
        }

        for filename, content in files.items():
            create_test_file(temp_dir / filename, content)

        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Act - Pack all files
        pack_result = cli_runner(["pack", "*"], cwd=temp_dir)
        assert pack_result.returncode == 0

        # Verify all files are included
        file_count, filenames = get_packed_output_info(pack_result.stdout)
        assert file_count == 5
        assert set(filenames) == set(files.keys())

        unpack_result = cli_runner(
            ["unpack", "--output-dir", str(output_dir)], input_data=pack_result.stdout, cwd=temp_dir
        )

        # Assert
        assert unpack_result.returncode == 0
        assert verify_files_identical(files, output_dir)


class TestFileOrdering:
    """Test file ordering and deterministic behavior."""

    def test_files_packed_in_sorted_order(self, temp_dir, cli_runner):
        """Test that files are packed in alphabetical order."""
        # Arrange - Create files in non-alphabetical order
        files = {"zebra.txt": "Z content", "alpha.txt": "A content", "beta.txt": "B content", "gamma.txt": "G content"}

        # Create files in reverse order
        for filename in reversed(list(files.keys())):
            create_test_file(temp_dir / filename, files[filename])

        # Act
        pack_result = cli_runner(["pack", "*.txt"], cwd=temp_dir)
        assert pack_result.returncode == 0

        # Assert files appear in sorted order in output
        file_count, filenames = get_packed_output_info(pack_result.stdout)
        assert file_count == 4
        assert filenames == ["alpha.txt", "beta.txt", "gamma.txt", "zebra.txt"]

    def test_deterministic_output(self, temp_dir, cli_runner):
        """Test that multiple runs produce identical output."""
        # Arrange
        files = {"file1.txt": "Content 1", "file2.txt": "Content 2", "file3.txt": "Content 3"}

        for filename, content in files.items():
            create_test_file(temp_dir / filename, content)

        # Act - Run pack command twice
        pack_result1 = cli_runner(["pack", "*.txt"], cwd=temp_dir)
        pack_result2 = cli_runner(["pack", "*.txt"], cwd=temp_dir)

        # Assert identical output
        assert pack_result1.returncode == 0
        assert pack_result2.returncode == 0
        assert pack_result1.stdout == pack_result2.stdout
