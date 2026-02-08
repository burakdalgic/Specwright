# Installation

## Requirements

- **Python 3.11** or newer
- pip, Poetry, or any PEP 517-compatible installer

## Install from PyPI

=== "pip"

    ```bash
    pip install specwright
    ```

=== "Poetry"

    ```bash
    poetry add specwright
    ```

=== "uv"

    ```bash
    uv add specwright
    ```

## Optional Extras

### State Diagrams

To generate Graphviz DOT diagrams for state machines:

```bash
pip install "specwright[diagrams]"
```

This adds the `graphviz` Python package. You'll also need the Graphviz system binary installed (`brew install graphviz` on macOS, `apt install graphviz` on Debian/Ubuntu).

## Verify Installation

```bash
python -c "import specwright; print(specwright.__version__)"
```

Or use the CLI:

```bash
specwright --version
```

## Development Installation

To work on Specwright itself:

```bash
git clone https://github.com/specwright/specwright.git
cd specwright
poetry install
poetry run pytest
```

## What Gets Installed

Specwright brings in these dependencies:

| Package | Purpose |
|---------|---------|
| `pydantic` | Runtime type validation engine |
| `typing-extensions` | Backported typing features |
| `click` | CLI framework |
| `rich` | Colorized terminal output |
| `jinja2` | Template rendering for code generation |

All are widely-used, stable packages with no exotic system requirements.
