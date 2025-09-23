"""Pipeline orchestration for pack and unpack workflows.

This module provides high-level functions that compose the extracted modules
into complete pack and unpack workflows. These functions replicate the core
logic from the CLI pack() and unpack() commands.
"""

from pathlib import Path
from typing import List, Optional, Tuple

from txtpack.content_parsing import parse_concatenated_content
from txtpack.delimiter_processing import (
    BundlerConfig,
    ChecksumAlgorithm,
    calculate_file_checksum,
    create_file_end_delimiter,
    create_file_start_delimiter,
)
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

        # Calculate checksum if algorithm is specified
        checksum = None
        if config.checksum_algorithm != ChecksumAlgorithm.NONE:
            checksum = calculate_file_checksum(file_content, config.checksum_algorithm)

        start_delimiter = create_file_start_delimiter(filename, byte_count, config, checksum)
        end_delimiter = create_file_end_delimiter(filename, config)

        content_parts.append(f"{start_delimiter}\n{file_content}\n{end_delimiter}\n")

    return "".join(content_parts)


def unpack_content(
    content: str,
    output_directory: Path,
    config: Optional[BundlerConfig] = None,
    file_writer: Optional[FileWriter] = None,
    verify_checksums: bool = False,
) -> List[Tuple[str, str]]:
    """Unpack delimited content into individual files.

    This function orchestrates the complete unpack workflow from the CLI unpack command.

    Args:
        content: Concatenated content with delimiters
        output_directory: Directory to write files to
        config: Optional configuration for delimiters
        file_writer: Optional custom file writer function
        verify_checksums: Whether to require checksum validation for all files

    Returns:
        List of (filename, content) tuples that were written

    Raises:
        ValueError: If content contains no valid files or checksum validation fails
        OSError: If output directory cannot be created
        IOError: If files cannot be written
    """
    if config is None:
        config = BundlerConfig()

    file_data = parse_concatenated_content(content, config, verify_checksums=verify_checksums)

    # Only raise exception if no valid file delimiters were found at all
    # Check if content contains any lines that are valid file delimiters
    if not file_data:
        from txtpack.delimiter_processing import is_file_start_delimiter

        lines = content.splitlines()
        has_any_valid_delimiters = any(is_file_start_delimiter(line.strip(), config) for line in lines)

        if not has_any_valid_delimiters:
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
