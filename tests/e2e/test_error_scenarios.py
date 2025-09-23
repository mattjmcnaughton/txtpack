"""Error scenario and edge case tests for txtpack CLI."""

from .conftest import create_test_file


class TestPackErrorScenarios:
    """Test error handling in pack command."""

    def test_pack_no_matching_files(self, temp_dir, cli_runner):
        """Test pack command when no files match the pattern."""
        # Arrange - Create some files that won't match
        create_test_file(temp_dir / "test.txt", "content")

        # Act - Try to pack files with non-matching pattern
        pack_result = cli_runner(["pack", "*.nonexistent"], cwd=temp_dir)

        # Assert
        assert pack_result.returncode == 1

    def test_pack_nonexistent_directory(self, temp_dir, cli_runner):
        """Test pack command with non-existent directory."""
        # Act
        nonexistent_dir = temp_dir / "does_not_exist"
        pack_result = cli_runner(["pack", "*.txt", "--directory", str(nonexistent_dir)])

        # Assert
        assert pack_result.returncode == 1

    def test_pack_invalid_regex_pattern(self, temp_dir, cli_runner):
        """Test pack command with invalid regex pattern."""
        # Arrange
        create_test_file(temp_dir / "test.txt", "content")

        # Act - Use invalid regex pattern
        pack_result = cli_runner(["pack", "^[invalid"], cwd=temp_dir)

        # Assert
        assert pack_result.returncode == 1

    def test_pack_permission_denied_file(self, temp_dir, cli_runner):
        """Test pack command with file that cannot be read."""
        # Arrange
        test_file = temp_dir / "restricted.txt"
        create_test_file(test_file, "content")

        # Make file unreadable (on systems that support it)
        try:
            test_file.chmod(0o000)

            # Act
            pack_result = cli_runner(["pack", "restricted.txt"], cwd=temp_dir)

            # Assert
            assert pack_result.returncode == 1

        finally:
            # Restore permissions for cleanup
            test_file.chmod(0o644)

    def test_pack_empty_directory(self, temp_dir, cli_runner):
        """Test pack command in empty directory."""
        # Act - Try to pack from empty directory
        pack_result = cli_runner(["pack", "*.txt"], cwd=temp_dir)

        # Assert
        assert pack_result.returncode == 1


class TestUnpackErrorScenarios:
    """Test error handling in unpack command."""

    def test_unpack_empty_input(self, temp_dir, cli_runner):
        """Test unpack command with empty input."""
        # Arrange
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Act - Unpack empty input
        unpack_result = cli_runner(["unpack", "--output-dir", str(output_dir)], input_data="", cwd=temp_dir)

        # Assert
        assert unpack_result.returncode == 1

    def test_unpack_whitespace_only_input(self, temp_dir, cli_runner):
        """Test unpack command with whitespace-only input."""
        # Arrange
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Act - Unpack whitespace-only input
        unpack_result = cli_runner(
            ["unpack", "--output-dir", str(output_dir)], input_data="   \n\n  \t  \n", cwd=temp_dir
        )

        # Assert
        assert unpack_result.returncode == 1

    def test_unpack_invalid_delimiters(self, temp_dir, cli_runner):
        """Test unpack command with invalid delimiter format."""
        # Arrange
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        invalid_content = (
            "This is not valid packed content\n--- INVALID: format ---\nSome content\n--- NOT_A_DELIMITER ---\n"
        )

        # Act
        unpack_result = cli_runner(
            ["unpack", "--output-dir", str(output_dir)], input_data=invalid_content, cwd=temp_dir
        )

        # Assert
        assert unpack_result.returncode == 1

    def test_unpack_malformed_file_delimiter(self, temp_dir, cli_runner):
        """Test unpack with malformed file start delimiter."""
        # Arrange
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        malformed_content = "--- FILE: test.txt MISSING_MIDDLE_PART ---\nSome content\n--- END: test.txt ---\n"

        # Act
        unpack_result = cli_runner(
            ["unpack", "--output-dir", str(output_dir)], input_data=malformed_content, cwd=temp_dir
        )

        # Assert
        assert unpack_result.returncode == 1

    def test_unpack_byte_count_mismatch(self, temp_dir, cli_runner):
        """Test unpack when declared byte count doesn't match actual content."""
        # Arrange
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Content claims 100 bytes but only has ~12
        mismatched_content = "--- FILE: test.txt (100 bytes) ---\nShort content\n--- END: test.txt ---\n"

        # Act
        unpack_result = cli_runner(
            ["unpack", "--output-dir", str(output_dir)], input_data=mismatched_content, cwd=temp_dir
        )

        # Assert - should succeed but skip the malformed file (more robust behavior)
        assert unpack_result.returncode == 0
        # Should not create any files due to byte count mismatch
        assert len(list(output_dir.iterdir())) == 0

    def test_unpack_nonexistent_input_file(self, temp_dir, cli_runner):
        """Test unpack with non-existent input file."""
        # Arrange
        output_dir = temp_dir / "output"
        output_dir.mkdir()
        nonexistent_file = temp_dir / "does_not_exist.txt"

        # Act
        unpack_result = cli_runner(["unpack", "--input", str(nonexistent_file), "--output-dir", str(output_dir)])

        # Assert
        assert unpack_result.returncode == 1


class TestEdgeCases:
    """Test various edge cases and boundary conditions."""

    def test_file_ending_without_newline(self, temp_dir, cli_runner):
        """Test file that doesn't end with newline."""
        # Arrange
        no_newline_content = "Content without final newline"
        create_test_file(temp_dir / "no_newline.txt", no_newline_content)

        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Act
        pack_result = cli_runner(["pack", "no_newline.txt"], cwd=temp_dir)
        assert pack_result.returncode == 0

        unpack_result = cli_runner(
            ["unpack", "--output-dir", str(output_dir)], input_data=pack_result.stdout, cwd=temp_dir
        )

        # Assert
        assert unpack_result.returncode == 0
        reconstructed = output_dir / "no_newline.txt"
        assert reconstructed.read_text(encoding="utf-8") == no_newline_content
