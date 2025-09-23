"""Delimiter processing utilities for file bundling.

This module provides pure functions for creating and parsing file delimiters
used in the pack/unpack workflow. All functions operate on strings/bytes and
return parsed results without side effects.
"""

import hashlib
import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


class ChecksumAlgorithm(Enum):
    """Supported checksum algorithms for file integrity validation."""

    NONE = "none"
    MD5 = "md5"
    SHA256 = "sha256"


@dataclass
class BundlerConfig:
    """Configuration for file bundling operations."""

    file_start_prefix: str = "--- FILE: "
    file_start_middle: str = " ("
    file_start_bytes_suffix: str = " bytes) ---"
    file_end_prefix: str = "--- END: "
    file_end_suffix: str = " ---"

    default_search_path: str = "."
    checksum_algorithm: ChecksumAlgorithm = ChecksumAlgorithm.NONE


def calculate_file_checksum(content: str, algorithm: ChecksumAlgorithm) -> Optional[str]:
    """Calculate checksum for file content using the specified algorithm.

    Args:
        content: File content as string
        algorithm: Checksum algorithm to use

    Returns:
        Hex-encoded checksum string, or None if algorithm is NONE

    Example:
        >>> calculate_file_checksum("hello", ChecksumAlgorithm.MD5)
        '5d41402abc4b2a76b9719d911017c592'
    """
    if algorithm == ChecksumAlgorithm.NONE:
        return None

    content_bytes = content.encode("utf-8")

    if algorithm == ChecksumAlgorithm.MD5:
        hasher = hashlib.md5()
    elif algorithm == ChecksumAlgorithm.SHA256:
        hasher = hashlib.sha256()
    else:
        raise ValueError(f"Unsupported checksum algorithm: {algorithm}")

    hasher.update(content_bytes)
    return hasher.hexdigest()


def validate_file_checksum(content: str, expected_checksum: str, algorithm: ChecksumAlgorithm) -> bool:
    """Validate file content against expected checksum.

    Args:
        content: File content as string
        expected_checksum: Expected checksum value
        algorithm: Checksum algorithm to use for validation

    Returns:
        True if checksum matches, False otherwise

    Example:
        >>> validate_file_checksum("hello", "5d41402abc4b2a76b9719d911017c592", ChecksumAlgorithm.MD5)
        True
    """
    if algorithm == ChecksumAlgorithm.NONE:
        return True

    actual_checksum = calculate_file_checksum(content, algorithm)
    return actual_checksum == expected_checksum


def _build_start_delimiter_pattern(config: BundlerConfig) -> re.Pattern:
    """Build regex pattern for parsing start delimiters with given config.

    Args:
        config: Configuration defining delimiter format

    Returns:
        Compiled regex pattern that captures (filename, byte_count, algorithm, checksum)
    """
    # Escape special regex characters in config strings
    prefix = re.escape(config.file_start_prefix)
    middle = re.escape(config.file_start_middle)

    # Handle bytes suffix - extract the part before " ---" for checksum support
    bytes_suffix = config.file_start_bytes_suffix
    if bytes_suffix.endswith(" ---"):
        bytes_pattern = re.escape(bytes_suffix[:-4])  # Remove " ---" part
        end_pattern = r"(?: \[(\w+):([a-f0-9]+)\])? ---"
    else:
        bytes_pattern = re.escape(bytes_suffix)
        end_pattern = ""

    # Build pattern: prefix + (filename) + middle + (digits) + bytes_pattern + optional_checksum + end
    pattern = f"{prefix}(.+?){middle}(\\d+){bytes_pattern}{end_pattern}"
    return re.compile(pattern)


def create_file_start_delimiter(
    filename: str, byte_count: int, config: Optional[BundlerConfig] = None, checksum: Optional[str] = None
) -> str:
    """Create a file start delimiter.

    Args:
        filename: Name of the file
        byte_count: Number of bytes in the file content
        config: Optional configuration for delimiter format
        checksum: Optional checksum string to include in delimiter

    Returns:
        Formatted start delimiter string

    Example:
        >>> create_file_start_delimiter("test.txt", 123)
        '--- FILE: test.txt (123 bytes) ---'
        >>> create_file_start_delimiter("test.txt", 123, checksum="abc123")
        '--- FILE: test.txt (123 bytes) [checksum:abc123] ---'
    """
    if config is None:
        config = BundlerConfig()

    # Direct template formatting based on checksum presence
    if checksum is not None and config.checksum_algorithm != ChecksumAlgorithm.NONE:
        # Format with checksum - handle both default and custom configs
        if config.file_start_bytes_suffix.endswith(" ---"):
            # Default config or similar - insert checksum before final " ---"
            bytes_part = config.file_start_bytes_suffix[:-4]  # Remove " ---"
            return f"{config.file_start_prefix}{filename}{config.file_start_middle}{byte_count}{bytes_part} [{config.checksum_algorithm.value}:{checksum}] ---"
        else:
            # Custom config - append checksum info
            return f"{config.file_start_prefix}{filename}{config.file_start_middle}{byte_count}{config.file_start_bytes_suffix} [{config.checksum_algorithm.value}:{checksum}]"
    else:
        # Standard format without checksum
        return f"{config.file_start_prefix}{filename}{config.file_start_middle}{byte_count}{config.file_start_bytes_suffix}"


def create_file_end_delimiter(filename: str, config: Optional[BundlerConfig] = None) -> str:
    """Create a file end delimiter.

    Args:
        filename: Name of the file
        config: Optional configuration for delimiter format

    Returns:
        Formatted end delimiter string

    Example:
        >>> create_file_end_delimiter("test.txt")
        '--- END: test.txt ---'
    """
    if config is None:
        config = BundlerConfig()

    return f"{config.file_end_prefix}{filename}{config.file_end_suffix}"


def is_file_start_delimiter(line: str, config: Optional[BundlerConfig] = None) -> bool:
    """Check if a line is a file start delimiter.

    Args:
        line: Line to check
        config: Optional configuration for delimiter format

    Returns:
        True if line matches start delimiter pattern

    Example:
        >>> is_file_start_delimiter("--- FILE: test.txt (123 bytes) ---")
        True
        >>> is_file_start_delimiter("--- FILE: test.txt (123 bytes) [checksum:abc123] ---")
        True
        >>> is_file_start_delimiter("regular content")
        False
    """
    if config is None:
        config = BundlerConfig()

    # Use regex pattern for validation - simply try to parse and catch exceptions
    try:
        pattern = _build_start_delimiter_pattern(config)
        return pattern.match(line) is not None
    except Exception:
        return False


def parse_file_start_delimiter(
    line: str, config: Optional[BundlerConfig] = None
) -> Tuple[str, int, Optional[str], Optional[ChecksumAlgorithm]]:
    """Parse filename, byte count, and optional checksum from a file start delimiter.

    Args:
        line: Start delimiter line to parse
        config: Optional configuration for delimiter format

    Returns:
        Tuple of (filename, byte_count, checksum, algorithm) where checksum and algorithm may be None

    Raises:
        ValueError: If line is not a valid start delimiter

    Example:
        >>> parse_file_start_delimiter("--- FILE: test.txt (123 bytes) ---")
        ('test.txt', 123, None, None)
        >>> parse_file_start_delimiter("--- FILE: test.txt (123 bytes) [md5:abc123] ---")
        ('test.txt', 123, 'abc123', ChecksumAlgorithm.MD5)
    """
    if config is None:
        config = BundlerConfig()

    # Use regex pattern to parse the delimiter
    pattern = _build_start_delimiter_pattern(config)
    match = pattern.match(line)

    if not match:
        raise ValueError(f"Not a valid start delimiter: {line}")

    # Extract matched groups
    groups = match.groups()
    filename = groups[0]

    try:
        byte_count = int(groups[1])
    except (ValueError, IndexError):
        raise ValueError(f"Invalid byte count in: {line}")

    # Extract checksum info if present (groups 2 and 3)
    checksum = None
    algorithm = None

    if len(groups) >= 4 and groups[2] and groups[3]:
        algorithm_str = groups[2]
        checksum = groups[3]

        # Convert algorithm string to enum
        try:
            algorithm = ChecksumAlgorithm(algorithm_str)
        except ValueError:
            raise ValueError(f"Unknown checksum algorithm '{algorithm_str}' in: {line}")

    return filename, byte_count, checksum, algorithm


def is_file_end_delimiter(line: str, filename: str, config: Optional[BundlerConfig] = None) -> bool:
    """Check if a line is the expected file end delimiter.

    Args:
        line: Line to check
        filename: Expected filename in the delimiter
        config: Optional configuration for delimiter format

    Returns:
        True if line matches expected end delimiter

    Example:
        >>> is_file_end_delimiter("--- END: test.txt ---", "test.txt")
        True
        >>> is_file_end_delimiter("--- END: other.txt ---", "test.txt")
        False
    """
    if config is None:
        config = BundlerConfig()

    expected_end = f"{config.file_end_prefix}{filename}{config.file_end_suffix}"
    return line == expected_end


def find_next_line_end(content_bytes: bytes, start_pos: int) -> int:
    """Find the position of the next newline character, or end of content.

    Args:
        content_bytes: Byte content to search
        start_pos: Position to start searching from

    Returns:
        Position of next newline or end of content
    """
    line_end = content_bytes.find(b"\n", start_pos)
    return line_end if line_end != -1 else len(content_bytes)


def extract_file_content_at_position(content_bytes: bytes, pos: int, filename: str, byte_count: int) -> Tuple[str, int]:
    """Extract file content at position and return content with new position.

    Args:
        content_bytes: Full byte content
        pos: Current position in content
        filename: Name of file being extracted (for error messages)
        byte_count: Expected number of bytes to extract

    Returns:
        Tuple of (file_content, new_position)

    Raises:
        ValueError: If not enough content available or decoding fails
    """
    if pos + byte_count > len(content_bytes):
        raise ValueError(
            f"Not enough content for declared byte count in {filename}. "
            f"Declared: {byte_count}, Available: {len(content_bytes) - pos}"
        )

    file_content_bytes = content_bytes[pos : pos + byte_count]
    try:
        file_content = file_content_bytes.decode("utf-8")
    except UnicodeDecodeError as e:
        raise ValueError(f"Failed to decode content for {filename}: {e}")

    new_pos = pos + byte_count
    return file_content, new_pos


def skip_end_delimiter(content_bytes: bytes, pos: int, filename: str, config: Optional[BundlerConfig] = None) -> int:
    """Skip the end delimiter line and return new position.

    Args:
        content_bytes: Full byte content
        pos: Current position in content
        filename: Expected filename in end delimiter
        config: Optional configuration for delimiter format

    Returns:
        New position after skipping end delimiter

    Note:
        If end delimiter is not found or incorrect, logs warning but continues
    """
    if config is None:
        config = BundlerConfig()

    if pos >= len(content_bytes):
        return pos

    if pos < len(content_bytes) and content_bytes[pos : pos + 1] == b"\n":
        pos += 1

    line_end = find_next_line_end(content_bytes, pos)
    if line_end > pos:
        try:
            end_line = content_bytes[pos:line_end].decode("utf-8")
            if is_file_end_delimiter(end_line, filename, config):
                return line_end + 1
            else:
                pass
        except UnicodeDecodeError:
            pass

    return pos


def extract_next_file(
    content_bytes: bytes, pos: int, config: Optional[BundlerConfig] = None, verify_checksums: bool = False
) -> Tuple[Optional[Tuple[str, str]], int]:
    """Extract the next file from concatenated content.

    Args:
        content_bytes: Full concatenated content as bytes
        pos: Current position in content
        config: Optional configuration for delimiter format
        verify_checksums: Whether to require checksum validation for all files

    Returns:
        Tuple of ((filename, content), new_position) or (None, new_position) if no valid file found

    Raises:
        ValueError: If verify_checksums is True and checksum validation fails
    """
    if config is None:
        config = BundlerConfig()

    line_end = find_next_line_end(content_bytes, pos)
    if line_end == pos:
        return None, pos

    try:
        line = content_bytes[pos:line_end].decode("utf-8")
    except UnicodeDecodeError:
        return None, line_end + 1

    if not is_file_start_delimiter(line, config):
        return None, line_end + 1

    try:
        filename, byte_count, checksum, algorithm = parse_file_start_delimiter(line, config)
        content_start_pos = line_end + 1

        file_content, pos_after_content = extract_file_content_at_position(
            content_bytes, content_start_pos, filename, byte_count
        )

        # Validate checksum if present or required
        if checksum is not None and algorithm is not None:
            if not validate_file_checksum(file_content, checksum, algorithm):
                raise ValueError(f"Checksum validation failed for {filename}")
        elif verify_checksums:
            raise ValueError(f"Checksum validation required but not found for {filename}")

        final_pos = skip_end_delimiter(content_bytes, pos_after_content, filename, config)

        return (filename, file_content), final_pos

    except (ValueError, UnicodeDecodeError):
        return None, line_end + 1
