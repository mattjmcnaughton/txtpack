"""Shared test fixtures and utilities for unit tests."""

import tempfile
from pathlib import Path
from typing import List, Tuple

import pytest
from hypothesis import strategies as st

from txtpack.cli import BundlerConfig


@pytest.fixture
def default_config():
    """Provide the default BundlerConfig for tests."""
    return BundlerConfig()


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_files(temp_dir):
    """Create sample test files in temp directory."""
    files = [
        ("test1.txt", "Hello world"),
        ("test2.md", "# Header\nContent"),
        ("data.json", '{"key": "value"}'),
    ]

    file_paths = []
    for filename, content in files:
        file_path = temp_dir / filename
        file_path.write_text(content, encoding="utf-8")
        file_paths.append(file_path)

    return file_paths


# Hypothesis strategies for property-based testing
@st.composite
def file_content_strategy(draw):
    """Generate file content including edge cases."""
    # Basic text content
    basic_text = st.text(
        alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd", "Pc", "Pd", "Ps", "Pe", "Po"), whitelist_characters=" \n\t"
        ),
        min_size=0,
        max_size=1000,
    )

    # Content that looks like delimiters
    delimiter_like = st.just("--- FILE: fake.txt (100 bytes) ---\nFake content\n--- END: fake.txt ---")

    # Unicode content
    unicode_text = st.text(min_size=0, max_size=100)

    # Empty content
    empty = st.just("")

    return draw(st.one_of(basic_text, delimiter_like, unicode_text, empty))


@st.composite
def filename_strategy(draw):
    """Generate valid filenames."""
    # Basic ASCII filenames
    basic_names = st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-_."),
        min_size=1,
        max_size=50,
    ).filter(lambda x: x and not x.startswith("."))

    # Common extensions
    extensions = st.sampled_from([".txt", ".md", ".py", ".json", ".yml", ""])

    name = draw(basic_names)
    ext = draw(extensions)

    return f"{name}{ext}"


@st.composite
def file_data_strategy(draw):
    """Generate (filename, content) pairs."""
    filename = draw(filename_strategy())
    content = draw(file_content_strategy())
    return filename, content


@st.composite
def file_list_strategy(draw):
    """Generate lists of (filename, content) pairs with unique filenames."""
    files = draw(st.lists(file_data_strategy(), min_size=0, max_size=10))

    # Ensure unique filenames
    seen_names = set()
    unique_files = []
    for filename, content in files:
        if filename not in seen_names:
            seen_names.add(filename)
            unique_files.append((filename, content))

    return unique_files


@st.composite
def glob_pattern_strategy(draw):
    """Generate glob patterns for testing."""
    patterns = ["*.txt", "*.md", "test*", "*data*", "*.py", "file?.txt", "*", "specific_file.txt"]
    return draw(st.sampled_from(patterns))


def create_test_files(temp_dir: Path, file_data: List[Tuple[str, str]]) -> List[Path]:
    """Helper to create test files from (filename, content) pairs."""
    file_paths = []
    for filename, content in file_data:
        file_path = temp_dir / filename
        file_path.write_text(content, encoding="utf-8")
        file_paths.append(file_path)
    return file_paths


def assert_files_identical(original_files: List[Tuple[str, str]], restored_dir: Path):
    """Assert that restored files match original file data."""
    for filename, expected_content in original_files:
        restored_file = restored_dir / filename
        assert restored_file.exists(), f"File {filename} was not restored"

        actual_content = restored_file.read_text(encoding="utf-8")
        assert actual_content == expected_content, f"Content mismatch in {filename}"
