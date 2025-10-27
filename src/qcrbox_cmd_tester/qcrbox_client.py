"""
QCrBox-specific client functionality.

This module contains all QCrBox API-specific code for uploading datasets,
running commands, and retrieving results.
"""

import io
import time
from dataclasses import dataclass

from qcrboxapiclient.api.calculations import get_calculation_by_id
from qcrboxapiclient.api.commands import invoke_command
from qcrboxapiclient.api.datasets import (
    create_dataset,
    delete_dataset_by_id,
    download_dataset_by_id,
)
from qcrboxapiclient.client import Client
from qcrboxapiclient.models import (
    CreateDatasetBody,
    InvokeCommandParameters,
    InvokeCommandParametersCommandArguments,
    QCrBoxErrorResponse,
)
from qcrboxapiclient.types import File


@dataclass
class CommandRunResult:
    """Result of running a QCrBox command."""

    status: str
    result_cif: str | None
    status_events: list  # List of CalculationStatusDetails


def upload_cif_as_dataset(client: Client, cif_text: str, file_name: str) -> tuple[str, str]:
    """
    Upload a CIF file to QCrBox and create a dataset.

    Args:
        client: The QCrBox API client
        cif_text: The CIF file content as a string
        file_name: The name for the uploaded file

    Returns:
        Tuple of (dataset_id, data_file_id)

    Raises:
        TypeError: If the upload fails
    """
    cifb = cif_text.encode("utf-8")
    file = File(io.BytesIO(cifb), file_name)
    upload_payload = CreateDatasetBody(file)

    response = create_dataset.sync(client=client, body=upload_payload)
    if isinstance(response, QCrBoxErrorResponse) or response is None:
        raise TypeError("Failed to upload file", response)

    dataset_id = response.payload.datasets[0].qcrbox_dataset_id
    data_file_id = response.payload.datasets[0].data_files[file_name].qcrbox_file_id

    return dataset_id, data_file_id


def run_qcrbox_command(
    client: Client,
    command_name: str,
    application_name: str,
    application_version: str,
    command_parameters: list,
) -> CommandRunResult:
    """
    Run a QCrBox command and wait for completion.

    Args:
        client: The QCrBox API client
        command_name: Name of the command to run
        application_name: Name of the QCrBox application
        application_version: Version of the application
        parameter_dict: Dictionary of command parameters

    Returns:
        CommandRunResult with status and output
    """
    parameter_dict, input_file_dataset_ids = prepare_qcrbox_parameters(client, command_parameters)

    parameters = InvokeCommandParametersCommandArguments.from_dict(parameter_dict)
    response = invoke_command.sync(
        client=client,
        body=InvokeCommandParameters(
            application_slug=application_name,
            application_version=application_version,
            command_name=command_name,
            command_arguments=parameters,
        ),
    )

    if isinstance(response, QCrBoxErrorResponse) or response is None:
        raise TypeError("Failed to invoke command", response)

    calculation_id = response.payload.calculation_id

    # Poll until completion
    final_response = None
    while final_response is None:
        calc_response = get_calculation_by_id.sync(id=calculation_id, client=client)
        if isinstance(calc_response, QCrBoxErrorResponse) or calc_response is None:
            raise TypeError("Failed to get calculation status", calc_response)

        try:
            final_response = next(
                resp for resp in calc_response.payload.calculations if resp.status in ("successful", "failed")
            )
        except StopIteration:
            final_response = None
        time.sleep(1)

    for dataset_id in input_file_dataset_ids:
        delete_dataset_by_id.sync(id=dataset_id, client=client)

    if final_response.status == "successful":
        output_dataset_id = final_response.output_dataset_id
        if not output_dataset_id:
            raise ValueError("No output dataset ID in successful response")

        dataset_bytes = download_dataset_by_id.sync(id=output_dataset_id, client=client)
        delete_dataset_by_id.sync(id=output_dataset_id, client=client)

        if isinstance(dataset_bytes, (QCrBoxErrorResponse, type(None), str)):
            raise TypeError("Unexpected dataset bytes type", type(dataset_bytes))

        return CommandRunResult(
            status="successful",
            result_cif=dataset_bytes.decode("utf-8"),
            status_events=final_response.status_events,
        )
    else:
        return CommandRunResult(status="failed", result_cif=None, status_events=final_response.status_events)


def prepare_qcrbox_parameters(client: Client, parameters: list) -> dict[str, object]:
    """
    Prepare QCrBox command parameters, uploading files as needed.

    Args:
        client: The QCrBox API client
        parameters: List of QCrBoxParameter or QCrBoxFileParameter objects

    Returns:
        Dictionary of parameter names to values (with file parameters
        converted to {'data_file_id': file_id})
    """
    from .models import QCrBoxFileParameter

    # Separate file and non-file parameters
    dataset_params = [param for param in parameters if isinstance(param, QCrBoxFileParameter)]

    # Upload files and get their IDs
    data_file_ids = {}
    dataset_ids = []
    for param in dataset_params:
        cif_text = param.cif_content
        dataset_id, data_file_id = upload_cif_as_dataset(client, cif_text, f"{param.name}.cif")
        data_file_ids[param.name] = data_file_id
        dataset_ids.append(dataset_id)

    # Build parameter dictionary
    parameter_dict = {
        param.name: ({"data_file_id": data_file_ids[param.name]} if param.name in data_file_ids else param.value)
        for param in parameters
    }

    return parameter_dict, dataset_ids
