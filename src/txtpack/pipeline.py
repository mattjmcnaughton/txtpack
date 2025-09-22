"""Pipeline orchestration for pack and unpack workflows.

This module provides high-level functions that compose the extracted modules
into complete pack and unpack workflows. These functions replicate the core
logic from the CLI pack() and unpack() commands.
"""

from pathlib import Path
from typing import List, Optional, Tuple

from txtpack.content_parsing import parse_concatenated_content
from txtpack.delimiter_processing import BundlerConfig, create_file_end_delimiter, create_file_start_delimiter
from txtpack.file_operations import (
    FileReader,
    FileWriter,
    ensure_directory_exists,
    get_file_byte_count,
    read_multiple_files,
)
from txtpack.pattern_matching import find_matching_files


def pack_files(
    pattern: str,
    search_directory: Path,
    config: Optional[BundlerConfig] = None,
    file_reader: Optional[FileReader] = None,
) -> str:
    """Pack files matching a pattern into delimited content.

    This function orchestrates the complete pack workflow from the CLI pack command.

    Args:
        pattern: Pattern to match files (glob or regex)
        search_directory: Directory to search for files
        config: Optional configuration for delimiters
        file_reader: Optional custom file reader function

    Returns:
        Concatenated content with delimiters

    Raises:
        FileNotFoundError: If search directory doesn't exist
        ValueError: If pattern is invalid or no files found
        IOError: If files cannot be read
    """
    if config is None:
        config = BundlerConfig()

    matching_files = find_matching_files(search_directory, pattern)

    if not matching_files:
        raise ValueError(f"No files found matching pattern '{pattern}' in {search_directory}")

    file_data = read_multiple_files(matching_files, file_reader)

    content_parts = []
    for filename, file_content in file_data:
        byte_count = get_file_byte_count(file_content)
        start_delimiter = create_file_start_delimiter(filename, byte_count, config)
        end_delimiter = create_file_end_delimiter(filename, config)

        content_parts.append(f"{start_delimiter}\n{file_content}\n{end_delimiter}\n")

    return "".join(content_parts)


def unpack_content(
    content: str,
    output_directory: Path,
    config: Optional[BundlerConfig] = None,
    file_writer: Optional[FileWriter] = None,
) -> List[Tuple[str, str]]:
    """Unpack delimited content into individual files.

    This function orchestrates the complete unpack workflow from the CLI unpack command.

    Args:
        content: Concatenated content with delimiters
        output_directory: Directory to write files to
        config: Optional configuration for delimiters
        file_writer: Optional custom file writer function

    Returns:
        List of (filename, content) tuples that were written

    Raises:
        ValueError: If content contains no valid files
        OSError: If output directory cannot be created
        IOError: If files cannot be written
    """
    if config is None:
        config = BundlerConfig()

    file_data = parse_concatenated_content(content, config)

    if not file_data:
        raise ValueError("No valid file delimiters found in content")

    ensure_directory_exists(output_directory)

    if file_writer:
        for filename, file_content in file_data:
            file_path = output_directory / filename
            file_writer(file_path, file_content)
    else:
        from txtpack.file_operations import write_file_content

        for filename, file_content in file_data:
            file_path = output_directory / filename
            write_file_content(file_path, file_content)

    return file_data
