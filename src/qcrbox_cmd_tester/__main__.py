"""
Command-line interface for running QCrBox test suites.

Usage:
    python -m qcrbox_cmd_tester [--tests-dir DIR] [--qcrbox-url URL] [--debug]
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

from qcrboxapiclient.client import Client

from .models import TestSuite
from .run_suite import TestSuiteResult, run_test_suite


def print_test_results(result: TestSuiteResult, debug_dir: Path | None = None) -> None:
    """Print test results in a readable format."""
    print(f"\n{'=' * 80}")
    print(f"Test Suite: {result.application_name}")
    print(f"Status: {'✓ PASSED' if result.all_passed else '✗ FAILED'}")
    print(f"{'=' * 80}\n")

    for test_result in result.test_results:
        status_symbol = "✓" if test_result.all_passed else "✗"
        print(f"{status_symbol} Test Case: {test_result.test_case_name}")

        for individual_result in test_result.individual_results:
            indent = "    "
            if individual_result.passed:
                print(f"{indent}✓ {individual_result.test_case_name}")
            else:
                print(f"{indent}✗ {individual_result.test_case_name}")
                if individual_result.log:
                    print(f"{indent}  Log: {individual_result.log}")
                if debug_dir:
                    print(f"{indent}  Debug logs saved to: {debug_dir}")
        print()


def save_debug_logs(
    result: TestSuiteResult, test_suite: TestSuite, debug_base_dir: Path, timestamp: str
) -> Path | None:
    """
    Save debug logs and CIF files for failing tests.

    Args:
        result: Test suite result
        test_suite: The test suite that was run
        debug_base_dir: Base directory for debug logs
        timestamp: Timestamp string for this test run

    Returns:
        Path to the debug directory for this suite, or None if no failures
    """
    # Check if there are any failures
    has_failures = not result.all_passed

    if not has_failures:
        return None

    # Create debug directory for this suite
    safe_app_name = result.application_name.replace("/", "_").replace(" ", "_")
    suite_debug_dir = debug_base_dir / f"{timestamp}_{safe_app_name}"
    suite_debug_dir.mkdir(parents=True, exist_ok=True)

    # Create summary log file
    log_file = suite_debug_dir / "summary.log"
    with open(log_file, "w") as f:
        f.write(f"Test Suite: {result.application_name}\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Status: {'PASSED' if result.all_passed else 'FAILED'}\n")
        f.write("=" * 80 + "\n\n")

        for test_result in result.test_results:
            f.write(f"Test Case: {test_result.test_case_name}\n")
            f.write(f"Status: {'PASSED' if test_result.all_passed else 'FAILED'}\n")

            if not test_result.all_passed:
                # Find the corresponding test case
                test_case = next((tc for tc in test_suite.tests if tc.name == test_result.test_case_name), None)

                if test_case:
                    f.write(f"Command: {test_case.qcrbox_command_name}\n")
                    f.write(
                        f"Application: {test_case.qcrbox_application_name} v{test_case.qcrbox_application_version}\n"
                    )
                    f.write(f"Command Status: {test_result.command_status}\n")

                # Save CIF file if available
                if test_result.result_cif:
                    safe_test_name = test_result.test_case_name.replace("/", "_").replace(" ", "_")
                    cif_file = suite_debug_dir / f"{safe_test_name}_result.cif"
                    cif_file.write_text(test_result.result_cif)
                    f.write(f"Result CIF saved to: {cif_file.name}\n")
                elif test_result.command_status == "failed":
                    f.write("No result CIF available (command failed)\n")

                f.write("\nFailed Checks:\n")
                for individual_result in test_result.individual_results:
                    if not individual_result.passed:
                        f.write(f"  - {individual_result.test_case_name}\n")
                        if individual_result.log:
                            f.write(f"    Log: {individual_result.log}\n")

            f.write("\n" + "-" * 80 + "\n\n")

    return suite_debug_dir


def run_test_suites_from_directory(tests_dir: Path, qcrbox_url: str, debug: bool = False) -> bool:
    """
    Run all test suites found in the specified directory.

    Args:
        tests_dir: Directory containing YAML test suite files
        qcrbox_url: URL of the QCrBox API
        debug: If True, save detailed debug logs for failing tests

    Returns:
        True if all tests passed, False otherwise
    """
    client = Client(qcrbox_url)

    # Set up debug directory if needed
    debug_base_dir = None
    timestamp = None
    if debug:
        debug_base_dir = Path("logs")
        debug_base_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Find all YAML files in the directory
    yaml_files = list(tests_dir.glob("*.yaml")) + list(tests_dir.glob("*.yml"))

    if not yaml_files:
        print(f"No YAML test files found in {tests_dir}", file=sys.stderr)
        return False

    print(f"Found {len(yaml_files)} test suite(s) in {tests_dir}")

    all_passed = True
    results = []
    test_suites = []

    for yaml_file in sorted(yaml_files):
        print(f"\nLoading test suite from: {yaml_file.name}")
        try:
            test_suite = TestSuite.from_yaml_file(yaml_file)
            print(f"  Application: {test_suite.application_name} v{test_suite.application_version}")
            print(f"  Tests: {len(test_suite.tests)}")

            result = run_test_suite(client, test_suite)
            results.append(result)
            test_suites.append(test_suite)

            if not result.all_passed:
                all_passed = False

        except Exception as e:
            print(f"  ✗ Error loading or running test suite: {e}", file=sys.stderr)
            all_passed = False
            continue

    # Save debug logs and print detailed results
    for result, test_suite in zip(results, test_suites, strict=True):
        debug_dir = None
        if debug and debug_base_dir and timestamp:
            debug_dir = save_debug_logs(result, test_suite, debug_base_dir, timestamp)
        print_test_results(result, debug_dir)

    # Print summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    passed_count = sum(1 for r in results if r.all_passed)
    total_count = len(results)
    print(f"Test Suites: {passed_count}/{total_count} passed")
    print(f"Overall Status: {'✓ PASSED' if all_passed else '✗ FAILED'}")
    print(f"{'=' * 80}\n")

    return all_passed


def main() -> int:
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(
        description="Run QCrBox test suites from YAML files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run tests from default directory (qcrbox_tests)
  python -m qcrbox_cmd_tester

  # Run tests from custom directory
  python -m qcrbox_cmd_tester --tests-dir /path/to/tests

  # Specify custom QCrBox API URL
  python -m qcrbox_cmd_tester --qcrbox-url http://localhost:8000
        """,
    )

    parser.add_argument(
        "--tests-dir",
        type=Path,
        default=Path("qcrbox_tests"),
        help="Directory containing YAML test suite files (default: qcrbox_tests)",
    )

    parser.add_argument(
        "--qcrbox-url",
        type=str,
        default="http://localhost:11000",
        help="URL of the QCrBox API (default: http://localhost:11000)",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode: save detailed logs and CIF files for failing tests to ./logs directory",
    )

    args = parser.parse_args()

    # Validate tests directory
    if not args.tests_dir.exists():
        print(f"Error: Tests directory '{args.tests_dir}' does not exist", file=sys.stderr)
        return 1

    if not args.tests_dir.is_dir():
        print(f"Error: '{args.tests_dir}' is not a directory", file=sys.stderr)
        return 1

    # Run tests
    try:
        all_passed = run_test_suites_from_directory(args.tests_dir, args.qcrbox_url, args.debug)
        return 0 if all_passed else 1
    except KeyboardInterrupt:
        print("\n\nTest run interrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"\n\nFatal error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
