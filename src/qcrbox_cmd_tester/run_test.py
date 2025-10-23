from qcrboxapiclient.client import Client
from qcrboxapiclient.models import (
    CreateDatasetBody,
    InvokeCommandParameters,
    InvokeCommandParametersCommandArguments,
    QCrBoxErrorResponse,
    QCrBoxResponseCalculationsResponse,
)
from qcrboxapiclient.api.commands import invoke_command
from qcrboxapiclient.api.datasets import create_dataset, delete_dataset_by_id, download_dataset_by_id
from qcrboxapiclient.api.calculations import get_calculation_by_id
from qcrboxapiclient.types import File

from dataclasses import dataclass
from qcrbox_cmd_tester.models import BaseOutputTest, QCrBoxFileParameter, TestCase, TestSuite
import io
import time

@dataclass
class IndividualTestResult:
    test_case_name: str
    passed: bool
    log: str

@dataclass
class TestCaseResult:
    test_case_name: str
    all_passed: bool
    individual_results: list[IndividualTestResult]

@dataclass
class TestSuiteResult:
    application_name: str
    all_passed: bool
    test_results: list[TestCaseResult]

@dataclass
class CommandRunResult:
    status: str
    result_cif: str | None
    status_events: list['CalculationStatusDetails']


def check_result(cif_text: str, base_output: BaseOutputTest) -> IndividualTestResult:
    ...

def cif2dataset(client: Client, cif_text: str, file_name: str) -> tuple[str, str]:
    cifb = cif_text.encode('utf-8')

    file = File(io.BytesIO(cifb), file_name)
    upload_payload = CreateDatasetBody(file)

    # Uploading the file with this endpoint creates a dataset containing this file.
    # Assuming everything went OK, thn we will get a QCrBoxResponse. If an error
    # occurred then the response is of type QCrBoxErrorResponse
    response = create_dataset.sync(client=client, body=upload_payload)
    if isinstance(response, QCrBoxErrorResponse) or response is None:
        raise TypeError("Failed to upload file", response)
    else:
        print("Created dataset:", response)

    # The response returns the created object in payload.datasets[0]. Note that this
    # doesn't contain any of the file's binary data and instead contains metadata
    # about the dataset and data files in the data set.
    dataset_id = response.payload.datasets[0].qcrbox_dataset_id
    data_file_id = response.payload.datasets[0].data_files[file_name].qcrbox_file_id

    return dataset_id, data_file_id 

def run_command_until_complete(
        client: Client,
        command_name: str,
        application_name: str,
        application_version: str,
        parameter_dict: dict[str, object]
) -> CommandRunResult:
    parameters = InvokeCommandParametersCommandArguments.from_dict(parameter_dict)
    response = invoke_command.sync(
        client=client,
        body=InvokeCommandParameters(
            application_slug=application_name,
            application_version=application_version,
            command_name=command_name,
            command_arguments=parameters
        )
    )

    calculation_id = response.payload.calculation_id

    final_response = None
    while final_response is None:
        response = get_calculation_by_id.sync(id=calculation_id, client=client)
        try:
            final_response = next(response for response in response.payload.calculations if response.status in ("successful", "failed"))
        except StopIteration:
            final_response = None
        time.sleep(1)

    if final_response.status == "successful":
        dataset_bytes = download_dataset_by_id.sync(id=final_response.output_dataset_id, client=client)
        delete_dataset_by_id.sync(id=final_response.output_dataset_id, client=client)

        return CommandRunResult(
            status="successful",
            result_cif=dataset_bytes.decode('utf-8'),
            status_events=final_response.status_events
        )
    else:
        return CommandRunResult(
            status="failed",
            result_cif=None,
            status_events=final_response.status_events
        )
    





def run_test_case(client: Client, test_case: TestCase) -> TestCaseResult:
    # check for dataset parameters
    dataset_params = [
        param for param in test_case.qcrbox_command_parameters
        if isinstance(param, QCrBoxFileParameter)
    ]

    dataset_ids = {}
    data_file_ids = {}
    for param in dataset_params:
        cif_text = param.cif_content
        dataset_id, data_file_id = cif2dataset(client, cif_text, f"{param.name}.cif")
        dataset_ids[param.name] = dataset_id
        data_file_ids[param.name] = data_file_id

    parameter_dict = {
        param.name: (
            {'data_file_id': data_file_ids[param.name]} if param.name in data_file_ids else param.value
        ) for param in test_case.qcrbox_command_parameters
    }

    command_result = run_command_until_complete(
        client,
        test_case.qcrbox_command_name,
        test_case.qcrbox_application_name,
        test_case.qcrbox_application_version,
        parameter_dict
    )
    
    


def run_test_suite(client: Client, test_suite: TestSuite) -> TestSuiteResult:
    case_results = [
        run_test_case(client, test_case) for test_case in test_suite.tests]
    return TestSuiteResult(
        application_name=test_suite.application_name,
        all_passed=all(case.all_passed for case in case_results),
        test_results=case_results
    )
