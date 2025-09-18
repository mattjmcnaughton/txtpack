"""File bundling tool for prompt library.

Provides pack and unpack commands for bundling files matching regex patterns
into a single stream and reconstructing the original files.
"""

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import structlog
import typer

# Configure structlog to log to stderr
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    logger_factory=lambda name: structlog.PrintLogger(file=sys.stderr),
    wrapper_class=structlog.BoundLogger,
    context_class=dict,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@dataclass
class BundlerConfig:
    """Configuration for file bundling operations."""

    # Delimiter configuration
    file_start_prefix: str = "--- FILE: "
    file_start_middle: str = " ("
    file_start_bytes_suffix: str = " bytes) ---"
    file_end_prefix: str = "--- END: "
    file_end_suffix: str = " ---"

    # Default paths
    default_search_path: str = "."


# Module-level default configuration
_DEFAULT_CONFIG = BundlerConfig()

app = typer.Typer(
    name="txtpack",
    help="""Bundle and unbundle files using pattern matching for prompt library workflows.

Examples:
  # Pack all sacf-* files to stdout
  uv run txtpack pack "sacf-*"

  # Save packed files to a bundle
  uv run txtpack pack "*.md" > bundle.txt

  # Unpack bundle back to individual files
  uv run txtpack unpack --input bundle.txt

  # Round-trip example
  uv run txtpack pack "sacf-*" | \\
  uv run txtpack unpack --output-dir ./restored/""",
    rich_markup_mode="markdown",
)


def _resolve_search_directory(directory: Optional[str], config: BundlerConfig = _DEFAULT_CONFIG) -> Path:
    """Resolve the directory to search for files."""
    if directory:
        return Path(directory)

    return Path.cwd() / config.default_search_path


def _convert_pattern_to_regex(pattern: str) -> str:
    """Convert glob-style pattern to regex if needed."""
    if "*" in pattern and not pattern.startswith("^"):
        regex_pattern = pattern.replace("*", ".*")
        return f"^{regex_pattern}$"
    return pattern


def _find_matching_files(search_dir: Path, pattern: str) -> List[Path]:
    """Find files matching the given pattern in the search directory."""
    regex_pattern = _convert_pattern_to_regex(pattern)

    try:
        compiled_pattern = re.compile(regex_pattern)
    except re.error as e:
        logger.error("invalid_regex_pattern", pattern=pattern, error=str(e))
        raise typer.Exit(1)

    matching_files = []
    for file_path in search_dir.iterdir():
        if file_path.is_file() and compiled_pattern.match(file_path.name):
            matching_files.append(file_path)

    return sorted(matching_files)


def _write_file_with_delimiters(file_path: Path, config: BundlerConfig = _DEFAULT_CONFIG) -> None:
    """Write a single file to stdout with delimiters including byte count."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        content_bytes = content.encode("utf-8")
        byte_count = len(content_bytes)

        delimiter_start = f"{config.file_start_prefix}{file_path.name}{config.file_start_middle}{byte_count}{config.file_start_bytes_suffix}\n"
        sys.stdout.write(delimiter_start)

        sys.stdout.write(content)

        sys.stdout.write(f"{config.file_end_prefix}{file_path.name}{config.file_end_suffix}\n")

    except IOError as e:
        logger.error("failed_to_read_file", file_path=str(file_path), error=str(e))
        raise typer.Exit(1)


def _read_input_content(input_file: Optional[str]) -> str:
    """Read content from input file or stdin."""
    try:
        if input_file:
            with open(input_file, "r", encoding="utf-8") as f:
                return f.read()
        else:
            return sys.stdin.read()
    except IOError as e:
        logger.error("failed_to_read_input", input_file=input_file, error=str(e))
        raise typer.Exit(1)


def _is_file_start_delimiter(line: str, config: BundlerConfig = _DEFAULT_CONFIG) -> bool:
    """Check if a line is a file start delimiter."""
    return (
        line.startswith(config.file_start_prefix)
        and config.file_start_middle in line
        and line.endswith(config.file_start_bytes_suffix)
    )


def _parse_file_start_delimiter(line: str, config: BundlerConfig = _DEFAULT_CONFIG) -> tuple[str, int]:
    """Parse filename and byte count from a file start delimiter.

    Returns (filename, byte_count) or raises ValueError if parsing fails.
    """
    middle_pos = line.find(config.file_start_middle)
    if middle_pos == -1:
        raise ValueError(f"Missing middle delimiter in: {line}")

    filename = line[len(config.file_start_prefix) : middle_pos]

    bytes_start = middle_pos + len(config.file_start_middle)
    bytes_end = line.find(config.file_start_bytes_suffix)
    if bytes_end == -1:
        raise ValueError(f"Missing bytes suffix in: {line}")

    byte_count_str = line[bytes_start:bytes_end]
    byte_count = int(byte_count_str)

    return filename, byte_count


def _find_next_line_end(content_bytes: bytes, start_pos: int) -> int:
    """Find the position of the next newline character, or end of content."""
    line_end = content_bytes.find(b"\n", start_pos)
    return line_end if line_end != -1 else len(content_bytes)


def _skip_end_delimiter(content_bytes: bytes, pos: int, filename: str, config: BundlerConfig = _DEFAULT_CONFIG) -> int:
    """Skip the end delimiter line and return new position."""
    if pos >= len(content_bytes):
        return pos

    if content_bytes[pos : pos + 1] == b"\n":
        pos += 1

    line_end = _find_next_line_end(content_bytes, pos)
    if line_end > pos:
        end_line = content_bytes[pos:line_end].decode("utf-8")
        expected_end = f"{config.file_end_prefix}{filename}{config.file_end_suffix}"
        if end_line == expected_end:
            return line_end + 1
        else:
            logger.warning(
                "end_delimiter_not_found",
                filename=filename,
                expected=expected_end,
                found=end_line,
            )

    return pos


def _extract_file_content_at_position(
    content_bytes: bytes, pos: int, filename: str, byte_count: int
) -> tuple[str, int]:
    """Extract file content at position and return content with new position.

    Returns (file_content, new_position) or raises ValueError if validation fails.
    """
    if pos + byte_count > len(content_bytes):
        raise ValueError(
            f"Not enough content for declared byte count in {filename}. "
            f"Declared: {byte_count}, Available: {len(content_bytes) - pos}"
        )

    file_content_bytes = content_bytes[pos : pos + byte_count]
    file_content = file_content_bytes.decode("utf-8")
    new_pos = pos + byte_count

    return file_content, new_pos


def _extract_next_file(
    content_bytes: bytes, pos: int, config: BundlerConfig = _DEFAULT_CONFIG
) -> tuple[Optional[tuple[str, str]], int]:
    """Extract the next file from concatenated content.

    Returns ((filename, content), new_position) or (None, new_position) if no valid file found.
    """
    line_end = _find_next_line_end(content_bytes, pos)
    if line_end == pos:
        return None, pos

    line = content_bytes[pos:line_end].decode("utf-8")

    if not _is_file_start_delimiter(line, config):
        return None, line_end + 1

    try:
        filename, byte_count = _parse_file_start_delimiter(line, config)
        content_start_pos = line_end + 1

        file_content, pos_after_content = _extract_file_content_at_position(
            content_bytes, content_start_pos, filename, byte_count
        )

        final_pos = _skip_end_delimiter(content_bytes, pos_after_content, filename, config)

        return (filename, file_content), final_pos

    except (ValueError, UnicodeDecodeError) as e:
        logger.error("failed_to_parse_file_delimiter", line=line, error=str(e))
        return None, line_end + 1


def _parse_concatenated_content(content: str, config: BundlerConfig = _DEFAULT_CONFIG) -> List[tuple[str, str]]:
    """Parse concatenated content and extract filename-content pairs using byte-accurate parsing."""
    files = []
    content_bytes = content.encode("utf-8")
    pos = 0

    while pos < len(content_bytes):
        file_data, new_pos = _extract_next_file(content_bytes, pos, config)

        if file_data is not None:
            files.append(file_data)

        if new_pos <= pos:
            break

        pos = new_pos

    return files


def _resolve_output_directory(output_dir: Optional[str]) -> Path:
    """Resolve the output directory for split files."""
    if output_dir:
        return Path(output_dir)
    return Path.cwd()


def _write_extracted_file(filename: str, content: str, output_dir: Path) -> None:
    """Write an extracted file to the output directory."""
    try:
        output_path = output_dir / filename
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info("wrote_file", filename=filename, output_path=str(output_path))
    except IOError as e:
        logger.error("failed_to_write_file", filename=filename, error=str(e))
        raise typer.Exit(1)


@app.command()
def pack(
    pattern: str = typer.Argument(
        ...,
        help="Pattern to match files. Supports glob-style patterns (e.g., 'sacf-*', '*.md') or regex",
    ),
    directory: Optional[str] = typer.Option(
        None,
        "--directory",
        "-d",
        help="Directory to search for files (default: prompts/agentic-coding/commands/)",
    ),
) -> None:
    """Pack files matching a pattern to stdout with delimiters.

    The output format uses byte-accurate delimiters to separate each file:
    --- FILE: filename.md (123 bytes) ---
    [exactly 123 bytes of file content]
    --- END: filename.md ---

    This format ensures round-trip compatibility and handles files that
    contain delimiter-like text in their content.
    """
    search_dir = _resolve_search_directory(directory)

    if not search_dir.exists():
        logger.error("search_directory_not_found", search_dir=str(search_dir))
        raise typer.Exit(1)

    matching_files = _find_matching_files(search_dir, pattern)

    if not matching_files:
        logger.error(
            "no_files_found",
            pattern=pattern,
            search_dir=str(search_dir),
        )
        raise typer.Exit(1)

    logger.info("found_matching_files", count=len(matching_files), pattern=pattern)

    for file_path in matching_files:
        _write_file_with_delimiters(file_path)


@app.command()
def unpack(
    input_file: Optional[str] = typer.Option(
        None, "--input", "-i", help="Input file to unpack (default: reads from stdin)"
    ),
    output_dir: Optional[str] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Output directory for unpacked files (default: current directory)",
    ),
) -> None:
    """Unpack concatenated input back into individual files.

    Parses input with file delimiters created by the pack command and
    reconstructs the original individual files. Supports both file input
    and stdin for pipeline compatibility.

    The output directory will be created if it doesn't exist.
    """
    content = _read_input_content(input_file)

    if not content.strip():
        logger.error("no_input_content_to_unpack")
        raise typer.Exit(1)

    files = _parse_concatenated_content(content)

    if not files:
        logger.error("no_valid_file_delimiters_found")
        raise typer.Exit(1)

    output_directory = _resolve_output_directory(output_dir)

    try:
        output_directory.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error(
            "failed_to_create_output_directory",
            output_directory=str(output_directory),
            error=str(e),
        )
        raise typer.Exit(1)

    logger.info("unpacking_files_to_directory", count=len(files), output_directory=str(output_directory))

    for filename, file_content in files:
        _write_extracted_file(filename, file_content, output_directory)
