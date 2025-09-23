"""End-to-end tests for checksum validation functionality."""

from txtpack.delimiter_processing import BundlerConfig, ChecksumAlgorithm
from txtpack.pipeline import pack_files, unpack_content


class TestChecksumRoundTripIntegration:
    """Test complete round-trip integration with checksums."""

    def test_md5_round_trip_integrity(self, temp_dir):
        """Test MD5 checksum round-trip maintains file integrity."""
        # Create test files with various content types
        original_files = [
            ("text.txt", "Simple text content"),
            ("unicode.txt", "Unicode content: 世界 🌍"),
            ("json.json", '{"nested": {"data": [1, 2, 3]}}'),
            ("empty.txt", ""),
        ]

        for filename, content in original_files:
            (temp_dir / filename).write_text(content, encoding="utf-8")

        # Pack with MD5 checksums
        config = BundlerConfig(checksum_algorithm=ChecksumAlgorithm.MD5)
        packed_content = pack_files("*", temp_dir, config)

        # Verify checksums are present
        assert "[md5:" in packed_content

        # Unpack to new directory
        restore_dir = temp_dir / "restored"
        result = unpack_content(packed_content, restore_dir)

        # Should restore all files with identical content
        assert len(result) == 4
        for filename, expected_content in original_files:
            restored_file = restore_dir / filename
            assert restored_file.exists()
            assert restored_file.read_text(encoding="utf-8") == expected_content

    def test_sha256_round_trip_integrity(self, temp_dir):
        """Test SHA256 checksum round-trip maintains file integrity."""
        # Create test files
        original_files = [
            ("data1.txt", "First file content"),
            ("data2.txt", "Second file content with special chars: !@#$%^&*()"),
        ]

        for filename, content in original_files:
            (temp_dir / filename).write_text(content, encoding="utf-8")

        # Pack with SHA256 checksums
        config = BundlerConfig(checksum_algorithm=ChecksumAlgorithm.SHA256)
        packed_content = pack_files("*", temp_dir, config)

        # Verify checksums are present
        assert "[sha256:" in packed_content

        # Unpack to new directory
        restore_dir = temp_dir / "restored"
        result = unpack_content(packed_content, restore_dir)

        # Should restore all files with identical content
        assert len(result) == 2
        for filename, expected_content in original_files:
            restored_file = restore_dir / filename
            assert restored_file.exists()
            assert restored_file.read_text(encoding="utf-8") == expected_content

    def test_corruption_detection(self, temp_dir):
        """Test that corrupted content is detected during round-trip."""
        # Create test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("Original content", encoding="utf-8")

        # Pack with checksums
        config = BundlerConfig(checksum_algorithm=ChecksumAlgorithm.MD5)
        packed_content = pack_files("test.txt", temp_dir, config)

        # Corrupt the content (but keep byte count correct)
        corrupted_content = packed_content.replace("Original content", "Corrupted cont.")

        # Unpack should detect corruption
        restore_dir = temp_dir / "restored"
        result = unpack_content(corrupted_content, restore_dir)

        # Should not unpack any files due to checksum mismatch
        assert len(result) == 0

    def test_backward_compatibility(self, temp_dir):
        """Test that new implementation works with legacy content."""
        # Create legacy packed content (without checksums)
        legacy_content = """--- FILE: legacy.txt (12 bytes) ---
Legacy file!
--- END: legacy.txt ---
"""

        # Should unpack successfully
        result = unpack_content(legacy_content, temp_dir)

        assert len(result) == 1
        assert result[0] == ("legacy.txt", "Legacy file!")

        # Check file was written correctly
        restored_file = temp_dir / "legacy.txt"
        assert restored_file.exists()
        assert restored_file.read_text(encoding="utf-8") == "Legacy file!"

    def test_strict_validation_mode(self, temp_dir):
        """Test strict checksum validation mode."""
        # Create content without checksums
        content = """--- FILE: test.txt (13 bytes) ---
Hello, world!
--- END: test.txt ---
"""

        # Should fail when verify_checksums=True and no checksums present
        result = unpack_content(content, temp_dir, verify_checksums=True)
        assert len(result) == 0

        # Should succeed when verify_checksums=False (default)
        result = unpack_content(content, temp_dir, verify_checksums=False)
        assert len(result) == 1
