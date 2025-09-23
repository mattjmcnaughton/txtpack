"""Content parsing utilities for extracting files from concatenated content.

This module provides pure functions for parsing concatenated content that contains
multiple files separated by delimiters. Functions operate on strings and return
parsed file data without side effects.
"""

from typing import List, Optional, Tuple

from txtpack.delimiter_processing import BundlerConfig, extract_next_file


def parse_concatenated_content(
    content: str, config: Optional[BundlerConfig] = None, verify_checksums: bool = False
) -> List[Tuple[str, str]]:
    """Parse concatenated content and extract filename-content pairs using byte-accurate parsing.

    This is the core parsing function that replicates the functionality of
    _parse_concatenated_content from the original CLI module.

    Args:
        content: Concatenated content containing multiple files with delimiters
        config: Optional configuration for delimiter format
        verify_checksums: Whether to require checksum validation for all files

    Returns:
        List of (filename, content) tuples for successfully parsed files

    Example:
        >>> content = '''--- FILE: test.txt (5 bytes) ---
        ... Hello
        ... --- END: test.txt ---
        ... --- FILE: data.json (13 bytes) ---
        ... {"key": "value"}
        ... --- END: data.json ---'''
        >>> parse_concatenated_content(content)
        [('test.txt', 'Hello'), ('data.json', '{"key": "value"}')]
    """
    if config is None:
        config = BundlerConfig()

    files = []
    content_bytes = content.encode("utf-8")
    pos = 0

    while pos < len(content_bytes):
        file_data, new_pos = extract_next_file(content_bytes, pos, config, verify_checksums=verify_checksums)

        if file_data is not None:
            files.append(file_data)

        if new_pos <= pos:
            break

        pos = new_pos

    return files
