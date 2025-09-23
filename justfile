# Install dependencies
install:
     uv sync --group dev

dev:
     uv run txtpack

lint:
     uv run ruff check .

lint-fix:
     uv run ruff check . --fix

format:
     uv run ruff format .

format-check:
     uv run ruff format --check .

typecheck:
     uv run ty check

test:
     uv run pytest

test-unit:
     uv run pytest tests/unit/

test-e2e:
     uv run pytest tests/e2e/

ci: lint format-check typecheck test
