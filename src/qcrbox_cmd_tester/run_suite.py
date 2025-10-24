"""
Test execution framework for running test suites.

This module orchestrates the execution of test suites and test cases,
delegating QCrBox-specific operations to qcrbox_client.py.
"""

from dataclasses import dataclass

from qcrboxapiclient.client import Client

from .models import TestCase, TestSuite
from .qcrbox_client import run_qcrbox_command
from .test_implementations import IndividualTestResult, check_result


@dataclass
class TestCaseResult:
    """Result of executing a single test case."""

    test_case_name: str
    all_passed: bool
    individual_results: list[IndividualTestResult]


@dataclass
class TestSuiteResult:
    """Result of executing an entire test suite."""

    application_name: str
    all_passed: bool
    test_results: list[TestCaseResult]


def run_test_case(client: Client, test_case: TestCase) -> TestCaseResult:
    """
    Execute a single test case against QCrBox.

    Args:
        client: QCrBox API client
        test_case: The test case to execute

    Returns:
        TestCaseResult with test outcomes
    """
    command_result = run_qcrbox_command(
        client,
        test_case.qcrbox_command_name,
        test_case.qcrbox_application_name,
        test_case.qcrbox_application_version,
        test_case.qcrbox_command_parameters,
    )

    # Check expected results against command output
    individual_results = []
    all_passed = True
    for expected_result in test_case.expected_results:
        if command_result.status != "successful":
            individual_results.append(
                IndividualTestResult(
                    test_case_name=test_case.name,
                    passed=False,
                    log=f"Command execution failed; cannot check expected result of type {type(expected_result).__name__}",
                )
            )
            all_passed = False
            continue

        result = check_result(
            cif_text=command_result.result_cif if command_result.result_cif is not None else "",
            expected_result=expected_result,
        )
        individual_results.append(result)
        if not result.passed:
            all_passed = False

    return TestCaseResult(test_case_name=test_case.name, all_passed=all_passed, individual_results=individual_results)


def run_test_suite(client: Client, test_suite: TestSuite) -> TestSuiteResult:
    """
    Execute all test cases in a test suite.

    Args:
        client: QCrBox API client
        test_suite: The test suite to execute

    Returns:
        TestSuiteResult with all test case results
    """
    case_results = [run_test_case(client, test_case) for test_case in test_suite.tests]
    return TestSuiteResult(
        application_name=test_suite.application_name,
        all_passed=all(case.all_passed for case in case_results),
        test_results=case_results,
    )
