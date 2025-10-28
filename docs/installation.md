# Installation Guide

This guide covers different ways to install QCrBox Command Tester depending on your environment and needs.

**Note**: QCrBox Command Tester requires access to a QCrBox server. The guide for setting up the dev environment as well as the repo are found here:
- **[QCrBox Documentation: Setting up a dev environment](https://qcrbox.github.io/QCrBox/how_to_guides/set_up_a_dev_environment/)**
- **[QCrBox Repository](https://github.com/QCrBox/QCrBox)**

## Requirements

- **Python**: 3.11 or higher
- **QCrBox API**: A running QCrBox API server (local or remote)
- **Operating System**: Linux, macOS, or Windows

## Installation Methods

Choose the installation method that best fits your workflow.

### Option 1: Using uv

Fast installation / dependency management using [uv](https://github.com/astral-sh/uv):

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install QCrBox Command Tester
uv pip install git+https://github.com/Niolon/qcrbox_cmd_tester.git

# Or for development
git clone https://github.com/Niolon/qcrbox_cmd_tester.git
cd qcrbox_cmd_tester
uv pip install -e ".[dev]"
```

### Option 2: Using pip

Standard installation using pip:

```bash
# Install from the repository
pip install git+https://github.com/Niolon/qcrbox_cmd_tester.git

# Verify installation
qcrbox-test --help
```


#### Install with Development Dependencies

If you plan to contribute or modify the code:

```bash
# Clone the repository
git clone https://github.com/Niolon/qcrbox_cmd_tester.git
cd qcrbox_cmd_tester

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```



### Option 3: Using pixi

For contributors, [Pixi](https://pixi.sh) manages both conda and PyPI packages:

```bash
# Install pixi if you haven't already
curl -fsSL https://pixi.sh/install.sh | bash

# Clone the repository
git clone https://github.com/Niolon/qcrbox_cmd_tester.git
cd qcrbox_cmd_tester

# Install dependencies and create environment
pixi install

# Activate the environment
pixi shell

# Run tests
pixi run test
```

## Verifying Your Installation

After installation, verify everything works:

```bash
# Check the command is available
qcrbox-test --help

# You should see output like:
# usage: qcrbox-test [--test-location DIR] [--qcrbox-url URL] [--debug]
# ...
```

## Setting Up QCrBox API Connection

QCrBox Command Tester requires access to a QCrBox API server.

**Need to set up QCrBox?** See the [QCrBox Installation Guide](https://qcrbox.github.io/QCrBox/) for instructions on running QCrBox locally or deploying it to a server.

### Local Development Server

If running QCrBox locally:

```bash
# Default assumes QCrBox runs on http://localhost:11000
qcrbox-test

# Or specify explicitly
qcrbox-test --qcrbox-url http://localhost:11000
```

### Environment Variable

Set a default QCrBox URL using the `QCRBOX_API_URL` environment variable:

```bash
# Add to your ~/.bashrc or ~/.zshrc
export QCRBOX_API_URL="http://localhost:11000"

# Then use without --qcrbox-url flag
qcrbox-test

# The environment variable is automatically detected
# You can still override it with --qcrbox-url if needed
qcrbox-test --qcrbox-url http://localhost:8000
```

## Installing Dependencies for Specific Features

### For Running Tests

```bash
# Install test dependencies
pip install -e ".[test]"

# Or with pixi
pixi install --feature test
```

### For Development

```bash
# Install all development tools (linting, formatting, testing)
pip install -e ".[dev]"

# Or with pixi
pixi install --feature devtools
```

### For Documentation Building

```bash
pixi run docs-build
```

for serving the documentation

```bash
pixi run docs-serve
```

## Troubleshooting

### Command Not Found

If `qcrbox-test` is not found after installation:

```bash
# Use the module directly
python -m qcrbox_cmd_tester --help

# Or add the scripts directory to PATH
export PATH="$PATH:$(python -m site --user-base)/bin"
```

### Python Version Issues

Ensure you're using Python 3.11+:

```bash
python --version  # Should show 3.11.x or higher
```

### QCrBox API Connection Issues

If you can't connect to the QCrBox API:

```bash
# Test the connection
curl http://localhost:11000

# Verify QCrBox container is running
docker ps | grep qcrbox
```

See the [QCrBox documentation](https://qcrbox.github.io/QCrBox/) for setup help.

## Uninstalling

```bash
# With pip
pip uninstall qcrbox_cmd_tester

# With pixi
cd qcrbox_cmd_tester
pixi clean
```

## Next Steps

After installation:

1. **[Write your first test](yaml-format.md)** - Learn the YAML test format
2. Run your test suites using `qcrbox-test`
3. Use `--debug` flag to troubleshoot failing tests
4. Check example test suites in the `qcrbox_tests/` directory

## Getting Help

- **Documentation**: Check the [full documentation](index.md)
- **Issues**: Report installation problems on [GitHub Issues](https://github.com/Niolon/qcrbox_cmd_tester/issues)
- **Community**: Join discussions and ask questions
