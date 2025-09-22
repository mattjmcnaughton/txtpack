"""Delimiter processing utilities for file bundling.

This module provides pure functions for creating and parsing file delimiters
used in the pack/unpack workflow. All functions operate on strings/bytes and
return parsed results without side effects.
"""

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class BundlerConfig:
    """Configuration for file bundling operations."""

    file_start_prefix: str = "--- FILE: "
    file_start_middle: str = " ("
    file_start_bytes_suffix: str = " bytes) ---"
    file_end_prefix: str = "--- END: "
    file_end_suffix: str = " ---"

    default_search_path: str = "."


def create_file_start_delimiter(filename: str, byte_count: int, config: Optional[BundlerConfig] = None) -> str:
    """Create a file start delimiter.

    Args:
        filename: Name of the file
        byte_count: Number of bytes in the file content
        config: Optional configuration for delimiter format

    Returns:
        Formatted start delimiter string

    Example:
        >>> create_file_start_delimiter("test.txt", 123)
        '--- FILE: test.txt (123 bytes) ---'
    """
    if config is None:
        config = BundlerConfig()

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
        >>> is_file_start_delimiter("regular content")
        False
    """
    if config is None:
        config = BundlerConfig()

    return (
        line.startswith(config.file_start_prefix)
        and config.file_start_middle in line
        and line.endswith(config.file_start_bytes_suffix)
    )


def parse_file_start_delimiter(line: str, config: Optional[BundlerConfig] = None) -> Tuple[str, int]:
    """Parse filename and byte count from a file start delimiter.

    Args:
        line: Start delimiter line to parse
        config: Optional configuration for delimiter format

    Returns:
        Tuple of (filename, byte_count)

    Raises:
        ValueError: If line is not a valid start delimiter

    Example:
        >>> parse_file_start_delimiter("--- FILE: test.txt (123 bytes) ---")
        ('test.txt', 123)
    """
    if config is None:
        config = BundlerConfig()

    if not is_file_start_delimiter(line, config):
        raise ValueError(f"Not a valid start delimiter: {line}")

    middle_pos = line.find(config.file_start_middle)
    if middle_pos == -1:
        raise ValueError(f"Missing middle delimiter in: {line}")

    filename = line[len(config.file_start_prefix) : middle_pos]

    bytes_start = middle_pos + len(config.file_start_middle)
    bytes_end = line.find(config.file_start_bytes_suffix)
    if bytes_end == -1:
        raise ValueError(f"Missing bytes suffix in: {line}")

    byte_count_str = line[bytes_start:bytes_end]
    try:
        byte_count = int(byte_count_str)
    except ValueError:
        raise ValueError(f"Invalid byte count '{byte_count_str}' in: {line}")

    return filename, byte_count


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
    content_bytes: bytes, pos: int, config: Optional[BundlerConfig] = None
) -> Tuple[Optional[Tuple[str, str]], int]:
    """Extract the next file from concatenated content.

    Args:
        content_bytes: Full concatenated content as bytes
        pos: Current position in content
        config: Optional configuration for delimiter format

    Returns:
        Tuple of ((filename, content), new_position) or (None, new_position) if no valid file found
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
        filename, byte_count = parse_file_start_delimiter(line, config)
        content_start_pos = line_end + 1

        file_content, pos_after_content = extract_file_content_at_position(
            content_bytes, content_start_pos, filename, byte_count
        )

        final_pos = skip_end_delimiter(content_bytes, pos_after_content, filename, config)

        return (filename, file_content), final_pos

    except (ValueError, UnicodeDecodeError):
        return None, line_end + 1
