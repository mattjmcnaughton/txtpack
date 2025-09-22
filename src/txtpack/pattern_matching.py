"""Pattern matching utilities for file discovery.

This module provides pure functions for converting glob patterns to regex
and finding files that match patterns in directories.
"""

import re
from pathlib import Path
from typing import List


def convert_pattern_to_regex(pattern: str) -> str:
    """Convert glob-style pattern to regex if needed.

    Args:
        pattern: Glob pattern like "*.txt" or existing regex pattern

    Returns:
        Regex pattern string that can be compiled

    Examples:
        >>> convert_pattern_to_regex("*.txt")
        '^.*\\.txt$'
        >>> convert_pattern_to_regex("^custom.*")
        '^custom.*'
    """
    if "*" in pattern and not pattern.startswith("^"):
        regex_pattern = pattern.replace("*", ".*")
        return f"^{regex_pattern}$"
    return pattern


def find_matching_files(search_dir: Path, pattern: str) -> List[Path]:
    """Find files matching the given pattern in the search directory.

    Args:
        search_dir: Directory to search for files
        pattern: Glob or regex pattern to match against filenames

    Returns:
        List of matching file paths, sorted by filename

    Raises:
        ValueError: If pattern is invalid regex
        FileNotFoundError: If search_dir doesn't exist
    """
    if not search_dir.exists():
        raise FileNotFoundError(f"Search directory does not exist: {search_dir}")

    if not search_dir.is_dir():
        raise ValueError(f"Search path is not a directory: {search_dir}")

    regex_pattern = convert_pattern_to_regex(pattern)

    try:
        compiled_pattern = re.compile(regex_pattern)
    except re.error as e:
        raise ValueError(f"Invalid regex pattern '{pattern}': {e}")

    matching_files = []
    for file_path in search_dir.iterdir():
        if file_path.is_file() and compiled_pattern.match(file_path.name):
            matching_files.append(file_path)

    return sorted(matching_files)
