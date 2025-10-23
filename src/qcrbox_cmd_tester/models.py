from pydantic import BaseModel, field_validator, model_validator, Field
from typing import Literal, Self
import yaml
from pathlib import Path

# ---------------- Input Parameter Models ---------------- #

class QCrBoxParameter(BaseModel):
    model_config = {'str_strip_whitespace': True, 'extra': 'forbid'}
    
    name: str = Field(..., min_length=1)
    value: str|int|float|bool
    
    @classmethod
    def from_yaml_dict(cls, data: dict, base_folder: Path) -> Self:
        """Create parameter from YAML dictionary"""
        param_type = data.get('type', 'str')
        param_data = {'name': data['name'], 'value': data['value']}
        
        if param_type == 'external_file':
            return QCrBoxFileParameter.from_external_file(
                file_path=data['value'],
                name=data['name'],
                base_folder=base_folder
            )
        elif param_type == 'internal_file':
            return QCrBoxFileParameter.from_internal_file(
                file_content=data['value'],
                name=data['name']
            )
        else:
            return cls(**param_data)

class QCrBoxFileParameter(BaseModel):
    name: str = Field(..., min_length=1)
    cif_content: str

    @classmethod
    def from_internal_file(cls, file_content: str, name: str) -> Self:
        return cls(name=name, cif_content=file_content)
    
    @classmethod
    def from_external_file(cls, file_path: str|Path, name: str, base_folder: Path) -> Self:
        file_path = Path(file_path)
        if not file_path.is_absolute():
            file_path = base_folder / file_path
        file_content = file_path.read_text()
        return cls(name=name, cif_content=file_content)

# union of all parameter types
QCrBoxParameterType = QCrBoxParameter | QCrBoxFileParameter


# ---------------- Output Test Models ---------------- #

class BaseOutputTest(BaseModel):
    """Base class for all output tests with common parsing logic"""
    
    @classmethod
    def from_yaml_dict(cls, data: dict) -> 'OutputTestType':
        """Factory method to create the appropriate output test from YAML"""
        result_type = data.get('result_type')
        
        if result_type == 'status':
            return StatusTest(expected_status=data['expected'])
        
        elif result_type == 'cif_value':
            test_data = {'cif_entry_name': data['cif_entry_name']}
            
            # Handle range specifications
            if 'accepted_min_value' in data and 'accepted_max_value' in data:
                # Explicit range
                test_data['accepted_min_value'] = data['accepted_min_value']
                test_data['accepted_max_value'] = data['accepted_max_value']
            elif 'expected_value' in data and 'allowed_deviation' in data:
                # Range from exact value + deviation
                base_value = data['expected_value']
                deviation = data['allowed_deviation']
                test_data['accepted_min_value'] = base_value - deviation
                test_data['accepted_max_value'] = base_value + deviation
            elif 'expected_value' in data:
                # Exact value (string or numerical)
                test_data['accepted_value'] = data['expected_value']
            
            return EntryOutputTest(**test_data)
        
        elif result_type == 'cif_loop_value':
            test_data = {
                'cif_entry_name': data['cif_entry_name'],
                'row_lookup_entry': data['row_lookup_name'],
                'row_lookup_value': data['row_lookup_value']
            }
            
            # Handle range specifications
            if 'accepted_min_value' in data and 'accepted_max_value' in data:
                # Explicit range
                test_data['accepted_min_value'] = data['accepted_min_value']
                test_data['accepted_max_value'] = data['accepted_max_value']
            elif 'expected_value' in data and 'allowed_deviation' in data:
                # Range from exact value + deviation
                base_value = data['expected_value']
                deviation = data['allowed_deviation']
                test_data['accepted_min_value'] = base_value - deviation
                test_data['accepted_max_value'] = base_value + deviation
            elif 'expected_value' in data:
                # Exact value (string or numerical)
                test_data['accepted_value'] = data['expected_value']
            else:
                raise ValueError("Missing expected_value for cif_loop_value")
            
            return LoopEntryOutputTest(**test_data)
        
        else:
            raise ValueError(f"Unknown result type: {result_type}")

class EntryOutputTest(BaseOutputTest):
    """Unified test for CIF entry values - handles both numerical ranges and exact values"""
    cif_entry_name: str = Field(..., min_length=1)
    result_type: Literal['cif_value'] = 'cif_value'
    
    # Optional fields - either range OR exact value must be specified
    accepted_value: str | int | float | None = Field(default=None, description="Exact value to match")
    accepted_min_value: float | None = Field(default=None, description="Minimum accepted value for numerical range")
    accepted_max_value: float | None = Field(default=None, description="Maximum accepted value for numerical range")
    
    @model_validator(mode='after')
    def validate_value_specifications(self):
        has_exact = self.accepted_value is not None
        has_min = self.accepted_min_value is not None
        has_max = self.accepted_max_value is not None
        has_range = has_min or has_max
        
        # Condition: either a range or an exact value need to be defined
        if not has_exact and not has_range:
            raise ValueError('Either accepted_value or a range (accepted_min_value/accepted_max_value) must be specified')
        
        # Condition: cannot have both exact value and range
        if has_exact and has_range:
            raise ValueError('Cannot specify both accepted_value and range values (accepted_min_value/accepted_max_value)')
        
        # Condition: A string value cannot have a range
        if has_exact and isinstance(self.accepted_value, str):
            if has_range:
                raise ValueError('String values cannot have a range')
        
        # If range is specified, both min and max must be present
        if has_range and not (has_min and has_max):
            raise ValueError('Both accepted_min_value and accepted_max_value must be specified for a range')
        
        # Validate min <= max
        if has_range:
            # Type narrowing: we know both are not None if has_range is True and we passed the previous check
            assert self.accepted_min_value is not None and self.accepted_max_value is not None
            if self.accepted_min_value > self.accepted_max_value:
                raise ValueError(
                    f'accepted_min_value ({self.accepted_min_value}) cannot be greater than '
                    f'accepted_max_value ({self.accepted_max_value})'
                )
        
        return self

class WasAddedOutputTest(BaseOutputTest):
    """Test to check if a CIF entry was added"""
    cif_entry_name: str = Field(..., min_length=1)
    result_type: Literal['cif_value'] = 'cif_value'
    none_value_accepted: bool = False

class DeletedOutputTest(BaseOutputTest):
    """Test to check if a CIF entry was deleted"""
    cif_entry_name: str = Field(..., min_length=1)
    result_type: Literal['cif_value'] = 'cif_value'

class LoopEntryOutputTest(BaseOutputTest):
    """Unified test for CIF loop entry values - handles both numerical ranges and exact values"""
    row_lookup_entry: str = Field(..., min_length=1)
    row_lookup_value: str | int | float | bool
    cif_entry_name: str = Field(..., min_length=1)
    result_type: Literal['cif_loop_value'] = 'cif_loop_value'
    
    # Optional fields - either range OR exact value must be specified
    accepted_value: str | int | float | None = Field(default=None, description="Exact value to match")
    accepted_min_value: float | None = Field(default=None, description="Minimum accepted value for numerical range")
    accepted_max_value: float | None = Field(default=None, description="Maximum accepted value for numerical range")
    
    @model_validator(mode='after')
    def validate_value_specifications(self):
        has_exact = self.accepted_value is not None
        has_min = self.accepted_min_value is not None
        has_max = self.accepted_max_value is not None
        has_range = has_min or has_max
        
        # Condition: either a range or an exact value need to be defined
        if not has_exact and not has_range:
            raise ValueError('Either accepted_value or a range (accepted_min_value/accepted_max_value) must be specified')
        
        # Condition: cannot have both exact value and range
        if has_exact and has_range:
            raise ValueError('Cannot specify both accepted_value and range values (accepted_min_value/accepted_max_value)')
        
        # Condition: A string value cannot have a range
        if has_exact and isinstance(self.accepted_value, str):
            if has_range:
                raise ValueError('String values cannot have a range')
        
        # If range is specified, both min and max must be present
        if has_range and not (has_min and has_max):
            raise ValueError('Both accepted_min_value and accepted_max_value must be specified for a range')
        
        # Validate min <= max
        if has_range:
            # Type narrowing: we know both are not None if has_range is True and we passed the previous check
            assert self.accepted_min_value is not None and self.accepted_max_value is not None
            if self.accepted_min_value > self.accepted_max_value:
                raise ValueError(
                    f'accepted_min_value ({self.accepted_min_value}) cannot be greater than '
                    f'accepted_max_value ({self.accepted_max_value})'
                )
        
        return self

class LoopWasAddedOutputTest(BaseOutputTest):
    """Test to check if a CIF loop entry was added"""
    row_lookup_entry: str = Field(..., min_length=1)
    row_lookup_value: str | int | float | bool
    cif_entry_name: str = Field(..., min_length=1)
    result_type: Literal['cif_loop_value'] = 'cif_loop_value'
    none_value_accepted: bool = False

class LoopDeletedOutputTest(BaseOutputTest):
    """Test to check if a CIF loop entry was deleted"""
    row_lookup_entry: str = Field(..., min_length=1)
    row_lookup_value: str | int | float | bool
    cif_entry_name: str = Field(..., min_length=1)
    result_type: Literal['cif_loop_value'] = 'cif_loop_value'

class StatusTest(BaseOutputTest):
    expected_status: Literal['successful', 'failed', 'warning'] = Field(
        ..., 
        description="Expected execution status"
    )
    result_type: Literal['status'] = 'status'


# Type alias for all output test types
OutputTestType = StatusTest | EntryOutputTest | LoopEntryOutputTest


# ---------------- Test Case and Suite Models ---------------- #

class TestCase(BaseModel):
    model_config = {'extra': 'forbid'}
    
    name: str = Field(..., min_length=1)
    description: str = Field(default="")

    qcrbox_application_name: str = Field(..., min_length=1)
    qcrbox_application_version: str = Field(..., min_length=1)
    qcrbox_command_name: str = Field(..., min_length=1)
    qcrbox_command_parameters: list[QCrBoxParameterType] = Field(default_factory=list)

    expected_results: list[OutputTestType] = Field(default_factory=list)
    
    @classmethod
    def from_yaml_dict(cls, data: dict, application_name: str, application_version: str, base_folder: Path) -> Self:
        """Create TestCase from YAML dictionary"""
        # Parse parameters
        parameters = [
            QCrBoxParameter.from_yaml_dict(param, base_folder=base_folder)
            for param in data.get('input_parameters', [])
        ]
        
        # Parse expected results
        expected_results = [
            BaseOutputTest.from_yaml_dict(result)
            for result in data.get('expected_results', [])
        ]
        
        return cls(
            name=data['name'],
            description=data.get('description', ''),
            qcrbox_application_name=application_name,
            qcrbox_application_version=application_version,
            qcrbox_command_name=data['command_name'],
            qcrbox_command_parameters=parameters,
            expected_results=expected_results
        )
    
    @field_validator('expected_results')
    @classmethod
    def must_have_at_least_one_result(cls, v):
        if not v:
            raise ValueError('Test case must have at least one expected result')
        return v
    
    @model_validator(mode='after')
    def validate_parameter_names_unique(self):
        names = [p.name for p in self.qcrbox_command_parameters]
        if len(names) != len(set(names)):
            duplicates = {n for n in names if names.count(n) > 1}
            raise ValueError(f'Duplicate parameter names found: {duplicates}')
        return self


class TestSuite(BaseModel):
    model_config = {'extra': 'forbid'}
    
    application_name: str = Field(..., min_length=1)
    application_version: str = Field(..., min_length=1)
    description: str = Field(default="")
    tests: list[TestCase] = Field(default_factory=list)
    
    @classmethod
    def from_yaml_dict(cls, data: dict, base_folder: Path) -> Self:
        """Create TestSuite from parsed YAML dictionary"""
        application_name = data['application_name']
        application_version = data['application_version']
        
        tests = [
            TestCase.from_yaml_dict(test_data, application_name, application_version, base_folder)
            for test_data in data.get('test_cases', [])
        ]
        
        return cls(
            application_name=application_name,
            application_version=application_version,
            description=data.get('description', ''),
            tests=tests
        )
    
    @classmethod
    def from_yaml_file(cls, file_path: str|Path) -> Self:
        """Load TestSuite directly from YAML file"""
        file_path = Path(file_path)
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)
        return cls.from_yaml_dict(data, base_folder=file_path.parent)
    
    @field_validator('tests')
    @classmethod
    def must_have_tests(cls, v):
        if not v:
            raise ValueError('Test suite must contain at least one test')
        return v
    
    @model_validator(mode='after')
    def validate_test_names_unique(self):
        names = [t.name for t in self.tests]
        if len(names) != len(set(names)):
            duplicates = {n for n in names if names.count(n) > 1}
            raise ValueError(f'Duplicate test names found: {duplicates}')
        return self
    
    def to_json_file(self, file_path: str):
        """Export test suite to JSON"""
        with open(file_path, 'w') as f:
            f.write(self.model_dump_json(indent=2))
    
    def to_dict(self) -> dict:
        """Export to dictionary"""
        return self.model_dump(mode='json')