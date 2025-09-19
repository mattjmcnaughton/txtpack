# txtpack

A Python CLI tool for bundling and unbundling files using pattern matching,
featuring `pack` and `unpack` commands that preserve file integrity through byte-accurate delimiters.
The tool supports glob patterns for file selection and enables round-trip
workflows where multiple files can be packed into a single stream
and later reconstructed back to their original individual files.

## Installation

### Via uv (recommended)
```bash
uvx txtpack
```

### Via pip
```bash
pip install txtpack
```

## Usage Examples

### Basic File Packing
```bash
# Pack all Python files to stdout
uv run txtpack pack "*.py"

# Pack files matching a specific pattern
uv run txtpack pack "config-*"

# Save packed files to a bundle file
uv run txtpack pack "*.md" > bundle.txt
```

### File Unpacking
```bash
# Unpack from a bundle file
uv run txtpack unpack --input bundle.txt

# Unpack to a specific directory
uv run txtpack unpack --input bundle.txt --output-dir ./restored/

# Unpack from stdin (pipeline usage)
cat bundle.txt | uv run txtpack unpack
```

### Round-trip Workflows
```bash
# Pack and immediately unpack files
uv run txtpack pack "src/*.py" | uv run txtpack unpack --output-dir ./backup/

# Create a bundle and restore it later
uv run txtpack pack "docs/*.md" > docs-bundle.txt
uv run txtpack unpack --input docs-bundle.txt --output-dir ./restored-docs/
```

### Advanced Usage
```bash
# Pack files from a specific directory
uv run txtpack pack "*.json" --directory ./config/

# Use regex patterns for more complex matching
uv run txtpack pack "test_.*\.py"

# Chain multiple operations
uv run txtpack pack "*.yaml" > config.bundle && \
  uv run txtpack unpack --input config.bundle --output-dir ./deploy/
```
