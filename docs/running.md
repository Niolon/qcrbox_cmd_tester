# Running the Tester

This guide covers how to run QCrBox Command Tester with different options and configurations.

## Basic Usage

### Running All Tests in a Directory

By default, the tester looks for YAML test files in the `qcrbox_tests/` directory:

```bash
qcrbox-test
```

This will:
- Find all `.yaml` and `.yml` files in the `qcrbox_tests/` directory
- Execute each test suite sequentially
- Display results for each test case
- Show a summary at the end

### Running Tests from a Custom Directory

Specify a different directory containing test suites:

```bash
qcrbox-test --test-location /path/to/my/tests/
```

### Running a Single Test File

Run a specific test suite file:

```bash
qcrbox-test --test-location qcrbox_tests/olex2.yaml
```

## Command-Line Options

### Full Syntax

```bash
qcrbox-test [--test-location PATH] [--qcrbox-url URL] [--debug]
```

### Options Reference

| Option | Description | Default |
|--------|-------------|---------|
| `--test-location` | Path to a YAML test file or directory | `qcrbox_tests` |
| `--qcrbox-url` | URL of the QCrBox API server | `$QCRBOX_API_URL` or `http://localhost:11000` |
| `--debug` | Enable debug mode with detailed logging | Disabled |
| `--help` | Show help message and exit | - |

## Configuring the QCrBox API URL

There are three ways to specify the QCrBox API URL (in order of priority):

### 1. Command-Line Flag (Highest Priority)

```bash
qcrbox-test --qcrbox-url http://localhost:8000
```

### 2. Environment Variable

Set the `QCRBOX_API_URL` environment variable:

```bash
# One-time use
export QCRBOX_API_URL="http://localhost:11000"
qcrbox-test

# Persistent (add to ~/.bashrc or ~/.zshrc)
echo 'export QCRBOX_API_URL="http://localhost:11000"' >> ~/.bashrc
source ~/.bashrc
```

### 3. Default Value (Lowest Priority)

If neither the flag nor environment variable is set, the default is `http://localhost:11000`.

## Debug Mode

### Enabling Debug Mode

```bash
qcrbox-test --debug
```

### What Debug Mode Does

When enabled, debug mode saves detailed information for **failed tests** to the `logs/` directory:

1. **Summary Log**: A text file with detailed failure information
2. **CIF Outputs**: The actual CIF files returned by QCrBox commands
3. **Test Metadata**: Command parameters, expected vs. actual values

### Debug Output Structure

```
logs/
└── 20251027_143022_olex2/       # Timestamp + application slug
    ├── summary.log              # Detailed test results
    └── test_result.cif          # Output CIF file
```

### Example Debug Log

```
================================================================================
Test Suite: olex2
Timestamp: 20251027_143022
Status: FAILED
================================================================================

Test Case: test_olex2_refine
Status: FAILED
Command: refine
Parameters:
  - input_cif: structure.cif
  - refinement_type: xyz

Failed Checks:
  [✗] CIF Entry Match: _refine.ls_R_factor_gt
      Expected: 0.0234
      Actual: 0.0245
      
CIF output saved to: test_result.cif
```

## Understanding Test Output

### Successful Test Run

```
Running test suite from: qcrboxtools.yaml
  Application: qcrboxtools v0.0.5
  Tests: 2

  [✓] iso2aniso epoxide - PASSED
  [✓] replace_structure_from_cif - PASSED

================================================================================
SUMMARY
================================================================================
Total test suites: 1
Passed: 1
Failed: 0
Overall Status: ✓ PASSED
================================================================================
```

### Failed Test Run

```
Running test suite from: olex2.yaml
  Application: olex2 v1.5
  Tests: 3

  [✓] test_basic_refine - PASSED
  [✗] test_advanced_refine - FAILED
      Failed checks:
        [✗] CIF Entry Match: _refine.ls_R_factor_gt
            Expected: 0.0234
            Actual: 0.0245
  [✓] test_structure_validation - PASSED

================================================================================
SUMMARY
================================================================================
Total test suites: 1
Passed: 0
Failed: 1
Overall Status: ✗ FAILED
================================================================================

Debug logs saved to: logs/20251027_143022_olex2/
```

## Running with Different Python Environments

### Using pip/uv

```bash
# After installing with pip
qcrbox-test --test-location tests/

# Or run as a Python module
python -m qcrbox_cmd_tester --test-location tests/
```

### Using pixi

```bash
# Run in pixi environment
pixi run python -m qcrbox_cmd_tester --test-location tests/
```


## Common Usage Patterns

### Development Workflow

```bash
# Run all tests during development
qcrbox-test --debug

# Run specific test file after making changes
qcrbox-test --test-location qcrbox_tests/myapp.yaml --debug

# Quick test without debug output
qcrbox-test --test-location qcrbox_tests/myapp.yaml
```


## Troubleshooting

### Connection Refused

```
Error: Connection refused to http://localhost:11000
```

**Solutions:**
- Verify QCrBox server is running: `docker ps | grep qcrbox`
- Check the URL: `curl http://localhost:11000`
- Verify firewall settings

### YAML Syntax Errors

```
Error parsing YAML file: ...
```

**Solutions:**
- Check YAML syntax using a validator
- Ensure proper indentation (spaces, not tabs)
- Verify all required fields are present
- See [YAML Format Documentation](yaml-format.md)

### Test Failures

```
[✗] CIF Entry Match: _refine.ls_R_factor_gt
```

**Solutions:**
- Enable `--debug` mode to see detailed output
- Check the saved CIF file in `logs/`
- Verify expected values are correct
- Check for numerical precision issues (use range tests instead of exact matches)

## Next Steps

- **[Write Test Suites](yaml-format.md)** - Learn the YAML test format
- **[Installation Guide](installation.md)** - Set up your environment
- **[Example Tests](https://github.com/Niolon/qcrbox_cmd_tester/tree/main/qcrbox_tests)** - See real-world examples
