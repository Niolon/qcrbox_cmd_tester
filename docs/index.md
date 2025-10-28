# QCrBox Command Tester

**A comprehensive testing framework for QCrBox applications and commands**

QCrBox Command Tester is a command-line tool that enables automated testing of crystallographic software applications integrated with the QCrBox platform. It provides a YAML-based test specification format that allows you to define test suites, execute commands, and validate results against expected outcomes.

**About QCrBox**: QCrBox is a platform for running crystallographic software in containerized environments, providing a unified API for executing commands across different crystallographic tools.

- **[QCrBox Documentation](https://qcrbox.github.io/QCrBox/)** - Learn about the QCrBox platform
- **[QCrBox Repository](https://github.com/QCrBox/QCrBox)** - QCrBox source code and development

## Overview

QCrBox Command Tester allows you to:

- **Define test suites** for QCrBox using human-readable YAML files
- **Validate CIF outputs** against expected values with multiple assertion types
- **Run tests** for individual files or entire test suite directories
- **Debug failures** with detailed logging and CIF file outputs

## Key Features

### YAML-Based Test Definitions

Write tests in a clear, declarative format that doesn't require programming knowledge:

```yaml
application_slug: qcrboxtools
application_version: "0.0.5"
test_cases:
  - name: "iso2aniso epoxide"
    command_name: iso2aniso
    input_parameters:
      - name: input_cif
        type: external_file
        value: "./test_cif_files/epoxide_isotropic.cif"
    expected_results:
      - result_type: status
        expected: successful
      - result_type: cif_loop_value
        test_type: match
        cif_entry_name: "_atom_site.adp_type"
        row_lookup:
          - row_entry_name: "_atom_site.label"
            row_entry_value: "O1"
        expected_value: "Uani"
```

### Comprehensive Validation

Test various aspects of command execution and CIF outputs:

- **Status checks**: Verify successful/failed execution
- **CIF value tests**: Match, range, substring, presence/absence checks
- **CIF loop tests**: Validate values in specific rows of CIF loops
- **Numerical tolerances**: Test floating-point values within acceptable ranges

### Flexible Execution Modes

Run tests in different ways:

```bash
# Run all tests in a directory
qcrbox-test --test-location qcrbox_tests/

# Run a single test file
qcrbox-test --test-location qcrbox_tests/olex2.yaml

# Enable debug mode for detailed failure logs
qcrbox-test --debug

# Use a custom QCrBox API endpoint
qcrbox-test --qcrbox-url http://localhost:8000
```

### Debug Mode

When tests fail, debug mode saves:

- Detailed summary logs with failure information
- Actual CIF output files for comparison
- Command execution status and error messages

All debug information is organized in timestamped directories under `./logs/`.

### Multiple Parameter Types

Pass different types of data to QCrBox commands:

- **Simple values**: Strings, numbers, booleans
- **External files**: Reference CIF files in your repository
- **Inline content**: Embed CIF content directly in test definitions

## Use Cases

### Application Developers

Test your QCrBox-integrated applications:

```yaml
# Test a new refinement command
application_slug: myrefine
application_version: "1.0.0"
test_cases:
  - name: "Basic refinement test"
    command_name: refine_structure
    # ... test configuration
```

### Integration Testing

Validate suites of multiple applications:

```bash
# Run tests for all integrated tools
qcrbox-test --test-location integration_tests/
```

### Regression Testing

Ensure new versions don't break existing functionality:

```yaml
# Compare outputs between versions
application_slug: qcrboxtools
application_version: "0.0.6"  # New version
test_cases:
  - name: "iso2aniso backward compatibility"
    # ... ensure same results as v0.0.5
```

## Architecture

```
┌─────────────────┐
│   YAML Test     │
│   Definitions   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Test Runner    │
│  (qcrbox-test)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  QCrBox API     │
│     Client      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  QCrBox API     │
│    Server       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Containerized   │
│  Applications   │
└─────────────────┘
```

## Project Structure

A typical QCrBox test project:

```
my-qcrbox-tests/
├── qcrbox_tests/          # Test suite directory
│   ├── olex2.yaml
│   ├── shelx.yaml
│   └── test_cif_files/    # Test data files
│       ├── structure1.cif
│       └── structure2.cif
├── logs/                  # Debug output (auto-created)
│   └── 20251027_143022_olex2/
│       ├── summary.log
│       └── test_result.cif
└── README.md
```

## Getting Started

1. **[Install](installation.md)** QCrBox Command Tester
2. **[Write](yaml-format.md)** your first test suite
3. Run tests and validate results
4. Debug any failures using the `--debug` flag

## Community and Support

- **Documentation**: [Full documentation](https://github.com/Niolon/qcrbox_cmd_tester)
- **Issues**: [Report bugs or request features](https://github.com/Niolon/qcrbox_cmd_tester/issues)
- **Contributing**: Contributions welcome! See our contribution guidelines.

## License

QCrBox Command Tester is released under the [MPL-2.0 License](https://mozilla.org/MPL/2.0/).
