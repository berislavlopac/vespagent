# List available recipes.
help:
    @just --list --unsorted


# --- Tests ---

# Run unit tests with coverage (Layer 1 & 2 — see CLAUDE.md §5).
test:
    uv run pytest tests --spec --cov


# --- Checks ---

# Run linting and formatting checks.
lint:
    uv run deptry .
    uv run ruff format --check .
    uv run ruff check .

# Run static typing analysis.
type:
    uv run pyrefly check

# Run security and safety checks.
safety:
    uvx vulture --exclude .venv --min-confidence 100 .
    uvx radon mi --show --multi --min B .
    uvx complexipy --quiet .

# Run all checks.
check: lint safety type

# Run checks and unit tests.
ready: lint safety type test


# --- Code & run ---

# Reformat the code using ruff.
[confirm]
reformat:
    uv run ruff format .
    uv run ruff check --select I --fix .

# Extract current production requirements. Save to a file by appending `> requirements.txt`.
reqs:
    uv export --no-dev

# Run the VESPA interview (CLI adapter).
chat:
    uv run vespa
