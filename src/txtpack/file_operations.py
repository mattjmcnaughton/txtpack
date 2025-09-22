"""File operations with I/O abstraction for testing.

This module provides pure functions for file reading and writing operations
with abstractions that allow for easy testing without filesystem dependencies.
"""

import sys
from pathlib import Path
from typing import Callable, Optional, Protocol


class FileReader(Protocol):
    """Protocol for file reading operations."""

    def __call__(self, file_path: Path) -> str:
        """Read content from a file path."""
        ...


class FileWriter(Protocol):
    """Protocol for file writing operations."""

    def __call__(self, file_path: Path, content: str) -> None:
        """Write content to a file path."""
        ...


def read_file_content(file_path: Path) -> str:
    """Read content from a file.

    Args:
        file_path: Path to the file to read

    Returns:
        File content as string

    Raises:
        IOError: If file cannot be read
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except IOError as e:
        raise IOError(f"Failed to read file {file_path}: {e}")


def write_file_content(file_path: Path, content: str) -> None:
    """Write content to a file.

    Args:
        file_path: Path to the file to write
        content: Content to write

    Raises:
        IOError: If file cannot be written
    """
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
    except IOError as e:
        raise IOError(f"Failed to write file {file_path}: {e}")


def read_input_content(input_file: Optional[str] = None, stdin_reader: Optional[Callable[[], str]] = None) -> str:
    """Read content from input file or stdin.

    Args:
        input_file: Path to input file, if None reads from stdin
        stdin_reader: Function to read from stdin (for testing)

    Returns:
        Content as string

    Raises:
        IOError: If content cannot be read
    """
    if input_file:
        return read_file_content(Path(input_file))
    else:
        if stdin_reader:
            return stdin_reader()
        else:
            return sys.stdin.read()


def get_file_byte_count(content: str) -> int:
    """Get byte count of string content when encoded as UTF-8.

    Args:
        content: String content

    Returns:
        Number of bytes when encoded as UTF-8
    """
    return len(content.encode("utf-8"))


def ensure_directory_exists(directory: Path) -> None:
    """Ensure a directory exists, creating it if necessary.

    Args:
        directory: Directory path to ensure exists

    Raises:
        OSError: If directory cannot be created
    """
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise OSError(f"Failed to create directory {directory}: {e}")


def read_multiple_files(file_paths: list[Path], file_reader: FileReader = None) -> list[tuple[str, str]]:
    """Read multiple files and return filename-content pairs.

    Args:
        file_paths: List of file paths to read
        file_reader: Optional custom file reader function

    Returns:
        List of (filename, content) tuples

    Raises:
        IOError: If any file cannot be read
    """
    reader = file_reader or read_file_content
    results = []

    for file_path in file_paths:
        content = reader(file_path)
        results.append((file_path.name, content))

    return results
