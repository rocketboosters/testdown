# testdown

Markdown-driven testing in Python. Write test scenarios as readable `.md` files
with named fenced code blocks, then extract and exercise those blocks in your
pytest suite.

## Overview

`testdown` lets you embed structured test data directly in Markdown files. Each
fenced code block carries a **language** tag and a **name**, and
`extract_blocks()` returns a collection you can query, iterate, and convert in
your test code.

This approach keeps test inputs, expected outputs, and documentation together in
a single human-readable file — making scenario-based test suites easy to read,
review, and extend.

## Installation

```bash
pip install testdown
```

For DataFrame conversion support (pandas, polars, dftxt):

```bash
pip install "testdown[data]"
```

## Block Naming Convention

Named fenced code blocks use the format `<language> <name>` on the opening fence
line:

<!-- prettier-ignore -->
```
```python setup
x = 1 + 1
```

```json expected_result
{ "status": "ok" }
```

```csv sample_data
name,score
Alice,95
Bob,87
```

````

Names can be any whitespace-free string. A common convention for scenario files
is `expected_<category>_<metric>` so blocks can be discovered with
`find_all("expected_*_*")` — mirroring how parametrized test suites verify
multiple output categories per scenario.

## Quick Start

Given a Markdown scenario file `tests/scenarios/my_feature.md` with the named
blocks above, extract and use them in a test:

```python
import testdown

blocks = testdown.extract_blocks("tests/scenarios/my_feature.md")

# Run Python setup code and access its module namespace
setup = blocks["setup"].exec_python_code()
assert setup.threshold == 0.5

# Convert a JSON block to a dict
result = blocks["expected_result"].to_dict()
assert result["status"] == "ok"

# Check which blocks are present
assert "sample_data" in blocks

# Find all blocks matching a wildcard pattern
expected_blocks = blocks.find_all("expected_*")
````

## API Reference

### `extract_blocks(markdown_contents)`

Parses a Markdown string or file path and returns a `MarkdownBlocks` collection.

```python
import pathlib
import testdown

# From a file path
blocks = testdown.extract_blocks(pathlib.Path("scenarios/my_test.md"))

# From an inline string
blocks = testdown.extract_blocks(markdown_string)
```

### `MarkdownBlocks`

A dict-like collection of extracted blocks.

| Method / Operation             | Description                   |
| ------------------------------ | ----------------------------- |
| `blocks["name"]`               | Get a block by name           |
| `"name" in blocks`             | Check if a block exists       |
| `del blocks["name"]`           | Remove a block                |
| `len(blocks)`                  | Number of blocks              |
| `iter(blocks)`                 | Iterate over block names      |
| `blocks.keys()`                | All block names               |
| `blocks.values()`              | All `MarkdownBlock` instances |
| `blocks.items()`               | Name/block pairs              |
| `blocks.get("name", default)`  | Get with optional default     |
| `blocks.find_all("pattern_*")` | Wildcard search (fnmatch)     |

### `MarkdownBlock`

Represents a single extracted code block with attributes `name`, `language`,
`index`, and `contents`.

| Method                               | Description                                    |
| ------------------------------------ | ---------------------------------------------- |
| `block.to_dict()`                    | Parse `json`, `yaml`, or `yml` block to `dict` |
| `block.to_dict(safe_load=False)`     | Parse YAML with `yaml.full_load`               |
| `block.exec_python_code(**kwargs)`   | Execute `python` block, returns a module       |
| `block.to_pandas_frame(csv_options)` | Convert `csv` or `df` block to `pd.DataFrame`  |
| `block.to_frame(csv_options)`        | Convert `csv` or `df` block to `pl.DataFrame`  |
| `block.to_polars_frame(csv_options)` | Alias for `to_frame()`                         |

`to_pandas_frame` and `to_frame`/`to_polars_frame` require the `data` extras.
`df` blocks use the [dftxt](https://github.com/rocketboosters/dftxt)
column-typed text format.

## Usage Patterns

### Parametrized scenario tests

The most common pattern — mirror what's shown in `example/`:

```python
import pathlib
import pytest
import testdown

_SCENARIOS_DIR = pathlib.Path(__file__).parent / "scenarios"
_SCENARIOS = [f.name for f in _SCENARIOS_DIR.glob("*.md")]


@pytest.mark.parametrize("scenario_name", _SCENARIOS)
def test_my_feature(scenario_name):
    blocks = testdown.extract_blocks(_SCENARIOS_DIR / scenario_name)

    # Run setup code defined in the scenario
    setup = blocks["setup"].exec_python_code()

    # Verify each expected_* block
    for block in blocks.find_all("expected_*"):
        expected = block.to_dict()
        observed = run_my_feature(setup)
        assert observed == expected
```

### Executable setup blocks

```python
blocks = testdown.extract_blocks("scenario.md")

# Pass variables into the execution context
module = blocks["setup"].exec_python_code(env="staging")
config = module.configuration
```

### DataFrame assertions (requires `data` extras)

```python
blocks = testdown.extract_blocks("scenario.md")

# polars
expected_df = blocks["expected_output"].to_frame()

# pandas
expected_df = blocks["expected_output"].to_pandas_frame()

# Pass options to the underlying CSV reader
df = blocks["data"].to_pandas_frame(csv_options={"sep": "|"})
df = blocks["data"].to_frame(csv_options={"separator": "|"})
```

### Wildcard block discovery

```python
blocks = testdown.extract_blocks("scenario.md")

# Find all blocks whose names match a pattern
for block in blocks.find_all("expected_actual_*"):
    category = block.name.split("_", 2)[2]
    assert run_actual(category) == block.to_dict()
```

---

## Development

### Setup

```bash
# Install all dependencies including dev and data extras
uv sync --all-extras
```

### Linting and formatting

```bash
# Check for lint errors
uvx ruff check .

# Auto-fix lint errors where possible
uvx ruff check --fix .

# Check formatting
uvx ruff format --check .

# Apply formatting
uvx ruff format .

# Check non-Python file formatting (JSON, YAML, Markdown, etc.)
npx prettier --check .

# Apply Prettier formatting
npx prettier --write .
```

### Type checking

```bash
uv run mypy testdown
```

### Tests and coverage

```bash
# Run tests with coverage report (fails below 80%)
uv run pytest

# Run a specific test file
uv run pytest tests/test_testdown.py

# Run a specific test by name
uv run pytest -k test_extract_blocks_from_path
```
