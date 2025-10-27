# QCrBox Command Tester

A command-line test suite runner for testing QCrBox API functionality.

## Installation

### Using pip/uv

```bash
# Install from source
pip install -e .

# Or with uv
uv pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

### Using pixi

```bash
pixi install
```

## Usage

Run test suites from YAML files:

```bash
# Run tests from default directory (qcrbox_tests)
qcrbox-test

# Or using Python module
python -m qcrbox_cmd_tester

# Run tests from custom directory
qcrbox-test --test-location /path/to/tests

# Run a single test file
qcrbox-test --test-location qcrbox_tests/olex2.yaml

# Specify custom QCrBox API URL
qcrbox-test --qcrbox-url http://localhost:8000

# Enable debug mode to save logs for failing tests
qcrbox-test --debug
```

For detailed information on writing YAML test suites, see the [YAML Format Documentation](docs/yaml-format.md).

## Development

### Running tests

```bash
# With pip/uv
pytest tests/

# With pixi
pixi run test
```

### Code formatting and linting

```bash
# With pip/uv
ruff check src/ tests/
ruff format src/ tests/

# With pixi
pixi run lint
pixi run format
```

## Features

- Run test suites defined in YAML files
- Test QCrBox command execution and results
- Validate CIF file outputs
- Check expected values against actual results
- Debug mode for detailed logging of failures
- Support for running single test files or entire directories

## License

MPL-2.0 (Mozilla Public License 2.0)
