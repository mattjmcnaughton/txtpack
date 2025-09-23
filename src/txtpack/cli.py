"""File bundling tool for prompt library.

Provides pack and unpack commands for bundling files matching regex patterns
into a single stream and reconstructing the original files.
"""

import sys
from pathlib import Path
from typing import Optional

import structlog
import typer

from txtpack.delimiter_processing import BundlerConfig, ChecksumAlgorithm
from txtpack.file_operations import read_input_content
from txtpack.pipeline import pack_files, unpack_content

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

_DEFAULT_CONFIG = BundlerConfig()

app = typer.Typer(
    name="txtpack",
    help="""Bundle and unbundle files using pattern matching for prompt library workflows.

Examples:

  uv run txtpack pack "sacf-*"


  uv run txtpack pack "*.md" > bundle.txt


  uv run txtpack unpack --input bundle.txt


  uv run txtpack pack "sacf-*" | \\
  uv run txtpack unpack --output-dir ./restored/""",
    rich_markup_mode="markdown",
)


def _resolve_search_directory(directory: Optional[str]) -> Path:
    """Resolve the directory to search for files."""
    if directory:
        return Path(directory)
    return Path.cwd() / _DEFAULT_CONFIG.default_search_path


def _resolve_output_directory(output_dir: Optional[str]) -> Path:
    """Resolve the output directory for split files."""
    if output_dir:
        return Path(output_dir)
    return Path.cwd()


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
    checksum_algorithm: ChecksumAlgorithm = typer.Option(
        ChecksumAlgorithm.NONE,
        "--checksum-algorithm",
        "-c",
        help="Checksum algorithm for file integrity validation (none, md5, sha256)",
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

    try:
        config = BundlerConfig(checksum_algorithm=checksum_algorithm)
        packed_content = pack_files(pattern, search_dir, config)

        file_count = packed_content.count("--- FILE:")
        logger.info("found_matching_files", count=file_count, pattern=pattern)

        sys.stdout.write(packed_content)

    except ValueError:
        logger.error("no_files_found", pattern=pattern, search_dir=str(search_dir))
        raise typer.Exit(1)
    except Exception as e:
        logger.error("pack_failed", error=str(e))
        raise typer.Exit(1)


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
    verify_checksums: bool = typer.Option(
        False,
        "--verify-checksums",
        help="Require checksum validation for all files (fails if checksums missing)",
    ),
) -> None:
    """Unpack concatenated input back into individual files.

    Parses input with file delimiters created by the pack command and
    reconstructs the original individual files. Supports both file input
    and stdin for pipeline compatibility.

    The output directory will be created if it doesn't exist.
    """
    content = read_input_content(input_file)

    if not content.strip():
        logger.error("no_input_content_to_unpack")
        raise typer.Exit(1)

    output_directory = _resolve_output_directory(output_dir)

    try:
        config = BundlerConfig()
        files = unpack_content(content, output_directory, config, verify_checksums=verify_checksums)

        logger.info("unpacking_files_to_directory", count=len(files), output_directory=str(output_directory))

        for filename, _ in files:
            logger.info("wrote_file", filename=filename, output_path=str(output_directory / filename))

    except ValueError:
        logger.error("no_valid_file_delimiters_found")
        raise typer.Exit(1)
    except OSError as e:
        logger.error(
            "failed_to_create_output_directory",
            output_directory=str(output_directory),
            error=str(e),
        )
        raise typer.Exit(1)
    except Exception as e:
        logger.error("unpack_failed", error=str(e))
        raise typer.Exit(1)
