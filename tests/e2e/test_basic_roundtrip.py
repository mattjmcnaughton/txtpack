"""Basic round-trip tests for txtpack CLI."""

from .conftest import verify_files_identical, create_test_file


class TestBasicRoundTrip:
    """Test basic pack and unpack workflows."""

    def test_single_file_roundtrip(self, temp_dir, cli_runner):
        """Test packing and unpacking a single file preserves content exactly."""
        # Arrange
        test_content = "Hello, world!\nThis is a test file with\nmultiple lines."
        test_file = temp_dir / "test.txt"
        create_test_file(test_file, test_content)

        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Act - Pack the file
        pack_result = cli_runner(["pack", "test.txt"], cwd=temp_dir)

        # Assert pack succeeded
        assert pack_result.returncode == 0
        assert pack_result.stdout
        assert "--- FILE: test.txt" in pack_result.stdout
        assert "--- END: test.txt ---" in pack_result.stdout

        # Act - Unpack the content
        unpack_result = cli_runner(
            ["unpack", "--output-dir", str(output_dir)], input_data=pack_result.stdout, cwd=temp_dir
        )

        # Assert unpack succeeded
        assert unpack_result.returncode == 0

        # Assert file was reconstructed identically
        reconstructed_file = output_dir / "test.txt"
        assert reconstructed_file.exists()
        assert reconstructed_file.read_text(encoding="utf-8") == test_content

    def test_empty_file_roundtrip(self, temp_dir, cli_runner):
        """Test packing and unpacking an empty file."""
        # Arrange
        test_file = temp_dir / "empty.txt"
        create_test_file(test_file, "")

        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Act - Pack the file
        pack_result = cli_runner(["pack", "empty.txt"], cwd=temp_dir)

        # Assert pack succeeded
        assert pack_result.returncode == 0
        assert "--- FILE: empty.txt (0 bytes) ---" in pack_result.stdout

        # Act - Unpack the content
        unpack_result = cli_runner(
            ["unpack", "--output-dir", str(output_dir)], input_data=pack_result.stdout, cwd=temp_dir
        )

        # Assert unpack succeeded and file is empty
        assert unpack_result.returncode == 0
        reconstructed_file = output_dir / "empty.txt"
        assert reconstructed_file.exists()
        assert reconstructed_file.read_text(encoding="utf-8") == ""

    def test_file_with_special_characters(self, temp_dir, cli_runner):
        """Test files with unicode and special characters."""
        # Arrange
        special_content = (
            "Unicode: café, naïve, résumé\nSymbols: @#$%^&*()\nQuotes: 'single' \"double\"\nNewlines:\n\n\nEnd."
        )
        test_file = temp_dir / "special.txt"
        create_test_file(test_file, special_content)

        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Act - Round trip
        pack_result = cli_runner(["pack", "special.txt"], cwd=temp_dir)
        assert pack_result.returncode == 0

        unpack_result = cli_runner(
            ["unpack", "--output-dir", str(output_dir)], input_data=pack_result.stdout, cwd=temp_dir
        )

        # Assert
        assert unpack_result.returncode == 0
        reconstructed_file = output_dir / "special.txt"
        assert reconstructed_file.read_text(encoding="utf-8") == special_content

    def test_file_with_delimiter_like_content(self, temp_dir, cli_runner):
        """Test files containing text that looks like delimiters."""
        # Arrange
        tricky_content = (
            "--- FILE: fake.txt (100 bytes) ---\n"
            "This content looks like a delimiter!\n"
            "--- END: fake.txt ---\n"
            "But it's just regular file content.\n"
            "--- FILE: another.txt (50 bytes) ---\n"
            "More fake delimiter content."
        )
        test_file = temp_dir / "tricky.txt"
        create_test_file(test_file, tricky_content)

        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Act - Round trip
        pack_result = cli_runner(["pack", "tricky.txt"], cwd=temp_dir)
        assert pack_result.returncode == 0

        unpack_result = cli_runner(
            ["unpack", "--output-dir", str(output_dir)], input_data=pack_result.stdout, cwd=temp_dir
        )

        # Assert
        assert unpack_result.returncode == 0
        reconstructed_file = output_dir / "tricky.txt"
        assert reconstructed_file.read_text(encoding="utf-8") == tricky_content

    def test_multiple_files_roundtrip(self, temp_dir, cli_runner):
        """Test packing and unpacking multiple files."""
        # Arrange
        files = {
            "file1.txt": "Content of file 1\nWith multiple lines",
            "file2.txt": "Different content in file 2",
            "file3.txt": "",  # Empty file
        }

        for filename, content in files.items():
            create_test_file(temp_dir / filename, content)

        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Act - Pack all txt files
        pack_result = cli_runner(["pack", "*.txt"], cwd=temp_dir)
        assert pack_result.returncode == 0

        # Verify all files are in the output
        for filename in files.keys():
            assert f"--- FILE: {filename}" in pack_result.stdout
            assert f"--- END: {filename} ---" in pack_result.stdout

        # Act - Unpack
        unpack_result = cli_runner(
            ["unpack", "--output-dir", str(output_dir)], input_data=pack_result.stdout, cwd=temp_dir
        )

        # Assert
        assert unpack_result.returncode == 0
        assert verify_files_identical(files, output_dir)

    def test_pack_with_directory_option(self, temp_dir, cli_runner):
        """Test pack command with explicit directory option."""
        # Arrange
        test_dir = temp_dir / "testdir"
        test_dir.mkdir()
        test_content = "Content in subdirectory"
        create_test_file(test_dir / "subfile.txt", test_content)

        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Act
        pack_result = cli_runner(["pack", "*.txt", "--directory", str(test_dir)])
        assert pack_result.returncode == 0
        assert "--- FILE: subfile.txt" in pack_result.stdout

        unpack_result = cli_runner(["unpack", "--output-dir", str(output_dir)], input_data=pack_result.stdout)

        # Assert
        assert unpack_result.returncode == 0
        reconstructed_file = output_dir / "subfile.txt"
        assert reconstructed_file.read_text(encoding="utf-8") == test_content

    def test_unpack_from_file(self, temp_dir, cli_runner):
        """Test unpack command reading from file instead of stdin."""
        # Arrange
        test_content = "File content for file input test"
        test_file = temp_dir / "test.txt"
        create_test_file(test_file, test_content)

        packed_file = temp_dir / "packed.txt"
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Pack to file
        pack_result = cli_runner(["pack", "test.txt"], cwd=temp_dir)
        assert pack_result.returncode == 0
        packed_file.write_text(pack_result.stdout, encoding="utf-8")

        # Act - Unpack from file
        unpack_result = cli_runner(
            ["unpack", "--input", str(packed_file), "--output-dir", str(output_dir)], cwd=temp_dir
        )

        # Assert
        assert unpack_result.returncode == 0
        reconstructed_file = output_dir / "test.txt"
        assert reconstructed_file.read_text(encoding="utf-8") == test_content


class TestExitCodes:
    """Test CLI exit codes for various scenarios."""

    def test_pack_success_exit_code(self, temp_dir, cli_runner):
        """Test pack command returns 0 on success."""
        create_test_file(temp_dir / "test.txt", "content")
        result = cli_runner(["pack", "test.txt"], cwd=temp_dir)
        assert result.returncode == 0

    def test_unpack_success_exit_code(self, temp_dir, cli_runner):
        """Test unpack command returns 0 on success."""
        create_test_file(temp_dir / "test.txt", "content")
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Get packed content
        pack_result = cli_runner(["pack", "test.txt"], cwd=temp_dir)

        # Test unpack exit code
        unpack_result = cli_runner(
            ["unpack", "--output-dir", str(output_dir)], input_data=pack_result.stdout, cwd=temp_dir
        )
        assert unpack_result.returncode == 0
