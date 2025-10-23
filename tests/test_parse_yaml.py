import pytest 

from qcrbox_cmd_tester.models import TestSuite, TestCase, QCrBoxParameter

@pytest.fixture()
def test_yaml_dict():
    data = {
        'application_name': 'TestApp',
        'application_version': '0.1.0',
        'description': 'A test application',
        'test_cases': [
            {
                'name': 'Test1',
                'description': 'First test case',
                'command_name': 'Cmd1',
                'input_parameters': [
                    {'name': 'param1', 'value': 'value1', 'type': 'str'},
                    {'name': 'param2', 'value': 'path/to/external/file.txt', 'type': 'external_file'}
                ],
                'expected_results': [
                    {'result_type': 'status', 'expected': 'successful'},
                ]
            }
        ]
    }
    return data

def test_create_test_suite_from_yaml(test_yaml_dict):
    test_suite = TestSuite.from_yaml_dict(test_yaml_dict)
    
    assert isinstance(test_suite, TestSuite)
    assert test_suite.application_name == 'TestApp'
    assert len(test_suite.tests) == 1
    
    test_case = test_suite.tests[0]
    assert isinstance(test_case, TestCase)
    assert test_case.name == 'Test1'
    assert len(test_case.qcrbox_command_parameters) == 2
    
    param1 = test_case.qcrbox_command_parameters[0]
    assert isinstance(param1, QCrBoxParameter)
    assert param1.name == 'param1'
    assert param1.value == 'value1'
    
    param2 = test_case.qcrbox_command_parameters[1]
    assert param2.name == 'param2'
    assert param2.value == 'path/to/external/file.txt'

