"""E2E test fixtures and utilities for txtpack CLI testing."""

import subprocess
import tempfile
from pathlib import Path
from typing import List, Tuple

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def cli_runner():
    """Fixture for running txtpack CLI commands via subprocess."""

    def run_command(args: List[str], input_data: str = None, cwd: Path = None) -> subprocess.CompletedProcess:
        """Run txtpack CLI command and return result."""
        cmd = ["uv", "run", "txtpack"] + args
        return subprocess.run(cmd, input=input_data, capture_output=True, text=True, cwd=cwd)

    return run_command


@pytest.fixture
def sample_files(temp_dir):
    """Create sample test files in temporary directory."""
    files = {}

    # Text file with simple content
    text_file = temp_dir / "sample.txt"
    text_content = "Hello, world!\nThis is a test file.\n"
    text_file.write_text(text_content, encoding="utf-8")
    files["sample.txt"] = text_content

    # Markdown file
    md_file = temp_dir / "readme.md"
    md_content = "# Test README\n\nThis is a **markdown** file.\n\n- Item 1\n- Item 2\n"
    md_file.write_text(md_content, encoding="utf-8")
    files["readme.md"] = md_content

    # Empty file
    empty_file = temp_dir / "empty.txt"
    empty_file.write_text("", encoding="utf-8")
    files["empty.txt"] = ""

    # File with special characters
    special_file = temp_dir / "special-chars.txt"
    special_content = "Unicode: café, naïve, résumé\nSymbols: @#$%^&*()\nNewlines:\n\n\nEnd."
    special_file.write_text(special_content, encoding="utf-8")
    files["special-chars.txt"] = special_content

    return files


@pytest.fixture
def nested_files(temp_dir):
    """Create nested directory structure with files."""
    # Create subdirectories
    (temp_dir / "subdir1").mkdir()
    (temp_dir / "subdir2").mkdir()

    files = {}

    # Files in root
    root_file = temp_dir / "root.txt"
    root_content = "Root level file"
    root_file.write_text(root_content, encoding="utf-8")
    files["root.txt"] = root_content

    # Files in subdirectories (note: current implementation only searches in specified directory)
    sub1_file = temp_dir / "subdir1" / "sub1.txt"
    sub1_content = "Subdirectory 1 file"
    sub1_file.write_text(sub1_content, encoding="utf-8")

    sub2_file = temp_dir / "subdir2" / "sub2.txt"
    sub2_content = "Subdirectory 2 file"
    sub2_file.write_text(sub2_content, encoding="utf-8")

    return files


def verify_files_identical(original_files: dict, output_dir: Path) -> bool:
    """Verify that files in output_dir match original_files exactly."""
    for filename, expected_content in original_files.items():
        output_file = output_dir / filename
        if not output_file.exists():
            return False

        actual_content = output_file.read_text(encoding="utf-8")
        if actual_content != expected_content:
            return False

    # Check no extra files were created
    actual_files = {f.name for f in output_dir.iterdir() if f.is_file()}
    expected_files = set(original_files.keys())
    if actual_files != expected_files:
        return False

    return True


def create_test_file(path: Path, content: str) -> None:
    """Helper to create a test file with specific content."""
    path.write_text(content, encoding="utf-8")


def get_packed_output_info(stdout: str) -> Tuple[int, List[str]]:
    """Parse packed output to extract file count and filenames."""
    lines = stdout.split("\n")
    filenames = []

    for line in lines:
        if line.startswith("--- FILE: ") and " (" in line and " bytes) ---" in line:
            start = len("--- FILE: ")
            end = line.find(" (")
            if end > start:
                filename = line[start:end]
                filenames.append(filename)

    return len(filenames), filenames
