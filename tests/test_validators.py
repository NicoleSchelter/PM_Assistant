"""
Unit tests for validation utilities.
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from utils.validators import (
    validate_file_path, validate_directory_path, validate_operation_mode,
    validate_file_format, validate_config_structure, validate_email,
    validate_date_format, validate_non_empty_string, validate_positive_number,
    validate_percentage, validate_probability, validate_wbs_code,
    validate_risk_id, validate_stakeholder_id, validate_phone_number,
    validate_enum_value, validate_list_of_strings, validate_date_string,
    validate_currency_amount
)
from utils.exceptions import ValidationError
from core.domain import RiskPriority


class TestFilePathValidation:
    """Test cases for file path validation."""
    
    def test_validate_existing_file(self):
        """Test validation of existing file."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
        # File is now closed and can be accessed
        try:
            result = validate_file_path(tmp_path)
            assert result == tmp_path
            assert isinstance(result, Path)
        finally:
            try:
                os.unlink(tmp_path)
            except (PermissionError, FileNotFoundError):
                pass  # Ignore cleanup errors on Windows
    
    def test_validate_nonexistent_file(self):
        """Test validation of non-existent file."""
        with pytest.raises(ValidationError, match="File does not exist"):
            validate_file_path("nonexistent_file.txt")
    
    def test_validate_empty_path(self):
        """Test validation of empty file path."""
        with pytest.raises(ValidationError, match="File path cannot be empty"):
            validate_file_path("")
    
    def test_validate_directory_as_file(self):
        """Test validation when directory is passed as file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            with pytest.raises(ValidationError, match="Path is not a file"):
                validate_file_path(tmp_dir)
    
    @patch('os.access')
    def test_validate_unreadable_file(self, mock_access):
        """Test validation of unreadable file."""
        mock_access.return_value = False
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
        # File is now closed and can be accessed
        try:
            with pytest.raises(ValidationError, match="File is not readable"):
                validate_file_path(tmp_path)
        finally:
            try:
                os.unlink(tmp_path)
            except (PermissionError, FileNotFoundError):
                pass  # Ignore cleanup errors on Windows


class TestDirectoryPathValidation:
    """Test cases for directory path validation."""
    
    def test_validate_existing_directory(self):
        """Test validation of existing directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = validate_directory_path(tmp_dir)
            assert result == Path(tmp_dir)
            assert isinstance(result, Path)
    
    def test_validate_nonexistent_directory(self):
        """Test validation of non-existent directory."""
        with pytest.raises(ValidationError, match="Directory does not exist"):
            validate_directory_path("nonexistent_directory")
    
    def test_validate_empty_directory_path(self):
        """Test validation of empty directory path."""
        with pytest.raises(ValidationError, match="Directory path cannot be empty"):
            validate_directory_path("")
    
    def test_validate_file_as_directory(self):
        """Test validation when file is passed as directory."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
        # File is now closed and can be accessed
        try:
            with pytest.raises(ValidationError, match="Path is not a directory"):
                validate_directory_path(tmp_path)
        finally:
            try:
                os.unlink(tmp_path)
            except (PermissionError, FileNotFoundError):
                pass  # Ignore cleanup errors on Windows


class TestOperationModeValidation:
    """Test cases for operation mode validation."""
    
    def test_validate_valid_modes(self):
        """Test validation of valid operation modes."""
        valid_modes = ['document_check', 'status_analysis', 'learning_module']
        for mode in valid_modes:
            result = validate_operation_mode(mode)
            assert result == mode
    
    def test_validate_case_insensitive(self):
        """Test case-insensitive mode validation."""
        result = validate_operation_mode('DOCUMENT_CHECK')
        assert result == 'document_check'
        
        result = validate_operation_mode('Status_Analysis')
        assert result == 'status_analysis'
    
    def test_validate_invalid_mode(self):
        """Test validation of invalid operation mode."""
        with pytest.raises(ValidationError, match="Invalid operation mode"):
            validate_operation_mode('invalid_mode')
    
    def test_validate_empty_mode(self):
        """Test validation of empty operation mode."""
        with pytest.raises(ValidationError, match="Operation mode cannot be empty"):
            validate_operation_mode('')


class TestFileFormatValidation:
    """Test cases for file format validation."""
    
    def test_validate_valid_formats(self):
        """Test validation of valid file formats."""
        test_cases = [
            ('test.xlsx', ['xlsx', 'xls'], 'xlsx'),
            ('test.md', ['md', 'txt'], 'md'),
            ('test.PDF', ['pdf'], 'pdf')  # Case insensitive
        ]
        
        for file_path, expected_formats, expected_result in test_cases:
            result = validate_file_format(file_path, expected_formats)
            assert result == expected_result
    
    def test_validate_invalid_format(self):
        """Test validation of invalid file format."""
        with pytest.raises(ValidationError, match="Invalid file format"):
            validate_file_format('test.txt', ['xlsx', 'pdf'])
    
    def test_validate_no_extension(self):
        """Test validation of file with no extension."""
        with pytest.raises(ValidationError, match="File has no extension"):
            validate_file_format('test_file', ['txt'])


class TestConfigStructureValidation:
    """Test cases for configuration structure validation."""
    
    def test_validate_valid_config(self):
        """Test validation of valid configuration."""
        config = {'key1': 'value1', 'key2': 'value2'}
        required_keys = ['key1', 'key2']
        # Should not raise exception
        validate_config_structure(config, required_keys)
    
    def test_validate_missing_keys(self):
        """Test validation with missing required keys."""
        config = {'key1': 'value1'}
        required_keys = ['key1', 'key2', 'key3']
        with pytest.raises(ValidationError, match="Missing required configuration keys"):
            validate_config_structure(config, required_keys)
    
    def test_validate_non_dict_config(self):
        """Test validation of non-dictionary configuration."""
        with pytest.raises(ValidationError, match="Configuration must be a dictionary"):
            validate_config_structure("not a dict", ['key1'])


class TestEmailValidation:
    """Test cases for email validation."""
    
    def test_validate_valid_emails(self):
        """Test validation of valid email addresses."""
        valid_emails = [
            'test@example.com',
            'user.name@domain.co.uk',
            'user+tag@example.org',
            'user123@test-domain.com'
        ]
        
        for email in valid_emails:
            result = validate_email(email)
            assert result == email
    
    def test_validate_invalid_emails(self):
        """Test validation of invalid email addresses."""
        invalid_emails = [
            'invalid-email',
            '@example.com',
            'user@',
            'user@domain',
            'user name@example.com'
        ]
        
        for email in invalid_emails:
            with pytest.raises(ValidationError, match="Invalid email format"):
                validate_email(email)
    
    def test_validate_empty_email(self):
        """Test validation of empty email."""
        with pytest.raises(ValidationError, match="Email address cannot be empty"):
            validate_email('')


class TestStringValidation:
    """Test cases for string validation."""
    
    def test_validate_non_empty_string(self):
        """Test validation of non-empty strings."""
        result = validate_non_empty_string('  test string  ', 'test_field')
        assert result == 'test string'  # Should be stripped
    
    def test_validate_empty_string(self):
        """Test validation of empty string."""
        with pytest.raises(ValidationError, match="test_field cannot be empty"):
            validate_non_empty_string('', 'test_field')
    
    def test_validate_whitespace_only_string(self):
        """Test validation of whitespace-only string."""
        with pytest.raises(ValidationError, match="test_field cannot be empty"):
            validate_non_empty_string('   ', 'test_field')
    
    def test_validate_non_string_input(self):
        """Test validation of non-string input."""
        with pytest.raises(ValidationError, match="test_field must be a string"):
            validate_non_empty_string(123, 'test_field')


class TestNumberValidation:
    """Test cases for number validation."""
    
    def test_validate_positive_number(self):
        """Test validation of positive numbers."""
        assert validate_positive_number(5, 'test_field') == 5
        assert validate_positive_number(3.14, 'test_field') == 3.14
    
    def test_validate_zero_or_negative(self):
        """Test validation of zero or negative numbers."""
        with pytest.raises(ValidationError, match="test_field must be positive"):
            validate_positive_number(0, 'test_field')
        
        with pytest.raises(ValidationError, match="test_field must be positive"):
            validate_positive_number(-5, 'test_field')
    
    def test_validate_non_number(self):
        """Test validation of non-numeric input."""
        with pytest.raises(ValidationError, match="test_field must be a number"):
            validate_positive_number('not a number', 'test_field')


class TestPercentageValidation:
    """Test cases for percentage validation."""
    
    def test_validate_valid_percentages(self):
        """Test validation of valid percentages."""
        assert validate_percentage(0, 'test_field') == 0.0
        assert validate_percentage(50, 'test_field') == 50.0
        assert validate_percentage(100, 'test_field') == 100.0
        assert validate_percentage(75.5, 'test_field') == 75.5
    
    def test_validate_invalid_percentages(self):
        """Test validation of invalid percentages."""
        with pytest.raises(ValidationError, match="test_field must be between 0 and 100"):
            validate_percentage(-1, 'test_field')
        
        with pytest.raises(ValidationError, match="test_field must be between 0 and 100"):
            validate_percentage(101, 'test_field')


class TestProbabilityValidation:
    """Test cases for probability validation."""
    
    def test_validate_valid_probabilities(self):
        """Test validation of valid probabilities."""
        assert validate_probability(0.0, 'test_field') == 0.0
        assert validate_probability(0.5, 'test_field') == 0.5
        assert validate_probability(1.0, 'test_field') == 1.0
    
    def test_validate_invalid_probabilities(self):
        """Test validation of invalid probabilities."""
        with pytest.raises(ValidationError, match="test_field must be between 0.0 and 1.0"):
            validate_probability(-0.1, 'test_field')
        
        with pytest.raises(ValidationError, match="test_field must be between 0.0 and 1.0"):
            validate_probability(1.1, 'test_field')


class TestWBSCodeValidation:
    """Test cases for WBS code validation."""
    
    def test_validate_valid_wbs_codes(self):
        """Test validation of valid WBS codes."""
        valid_codes = ['1', '1.1', '1.2.3', 'A.1.2', 'A1.B2.C3']
        
        for code in valid_codes:
            result = validate_wbs_code(code)
            assert result == code
    
    def test_validate_invalid_wbs_codes(self):
        """Test validation of invalid WBS codes."""
        # Test empty code separately since it has a different error message
        with pytest.raises(ValidationError, match="WBS code cannot be empty"):
            validate_wbs_code('')
        
        # Test other invalid codes
        invalid_codes = ['1.', '.1', '1..2', '1.2.', 'A.B.C.']
        for code in invalid_codes:
            with pytest.raises(ValidationError, match="Invalid WBS code format"):
                validate_wbs_code(code)


class TestRiskIdValidation:
    """Test cases for risk ID validation."""
    
    def test_validate_valid_risk_ids(self):
        """Test validation of valid risk IDs."""
        valid_ids = ['RISK-001', 'R001', 'RISK_001', 'risk123']
        
        for risk_id in valid_ids:
            result = validate_risk_id(risk_id)
            assert result == risk_id
    
    def test_validate_invalid_risk_ids(self):
        """Test validation of invalid risk IDs."""
        invalid_ids = ['', 'RISK 001', 'RISK@001', 'RISK.001']
        
        for risk_id in invalid_ids:
            with pytest.raises(ValidationError):
                validate_risk_id(risk_id)


class TestPhoneNumberValidation:
    """Test cases for phone number validation."""
    
    def test_validate_valid_phone_numbers(self):
        """Test validation of valid phone numbers."""
        valid_phones = [
            '+1-555-123-4567',
            '(555) 123-4567',
            '555.123.4567',
            '+44 20 7946 0958',
            '1234567890'
        ]
        
        for phone in valid_phones:
            result = validate_phone_number(phone)
            assert result == phone
    
    def test_validate_empty_phone(self):
        """Test validation of empty phone number (should be allowed)."""
        result = validate_phone_number('')
        assert result == ''
    
    def test_validate_invalid_phone_numbers(self):
        """Test validation of invalid phone numbers."""
        invalid_phones = ['123', 'abc-def-ghij', '123456789012345678901']
        
        for phone in invalid_phones:
            with pytest.raises(ValidationError, match="Invalid phone number format"):
                validate_phone_number(phone)


class TestEnumValidation:
    """Test cases for enum validation."""
    
    def test_validate_valid_enum_value(self):
        """Test validation of valid enum values."""
        result = validate_enum_value('high', RiskPriority, 'priority')
        assert result == RiskPriority.HIGH
        
        result = validate_enum_value('LOW', RiskPriority, 'priority')
        assert result == RiskPriority.LOW
    
    def test_validate_invalid_enum_value(self):
        """Test validation of invalid enum values."""
        with pytest.raises(ValidationError, match="Invalid priority"):
            validate_enum_value('invalid', RiskPriority, 'priority')
    
    def test_validate_empty_enum_value(self):
        """Test validation of empty enum value."""
        with pytest.raises(ValidationError, match="priority cannot be empty"):
            validate_enum_value('', RiskPriority, 'priority')


class TestListValidation:
    """Test cases for list validation."""
    
    def test_validate_valid_string_list(self):
        """Test validation of valid string lists."""
        input_list = ['  item1  ', 'item2', 'item3  ']
        result = validate_list_of_strings(input_list, 'test_field')
        assert result == ['item1', 'item2', 'item3']  # Should be stripped
    
    def test_validate_empty_list(self):
        """Test validation of empty list."""
        # Should be allowed by default
        result = validate_list_of_strings([], 'test_field')
        assert result == []
        
        # Should fail when not allowed
        with pytest.raises(ValidationError, match="test_field cannot be empty"):
            validate_list_of_strings([], 'test_field', allow_empty=False)
    
    def test_validate_non_list_input(self):
        """Test validation of non-list input."""
        with pytest.raises(ValidationError, match="test_field must be a list"):
            validate_list_of_strings('not a list', 'test_field')
    
    def test_validate_list_with_non_string_items(self):
        """Test validation of list with non-string items."""
        with pytest.raises(ValidationError, match="test_field\\[1\\] must be a string"):
            validate_list_of_strings(['item1', 123, 'item3'], 'test_field')


class TestDateStringValidation:
    """Test cases for date string validation."""
    
    def test_validate_valid_date_strings(self):
        """Test validation of valid date strings."""
        valid_dates = ['2024-01-15', '2023-12-31', '2024-02-29']  # Leap year
        
        for date_str in valid_dates:
            result = validate_date_string(date_str, 'test_field')
            assert result == date_str
    
    def test_validate_invalid_date_format(self):
        """Test validation of invalid date formats."""
        invalid_formats = ['2024/01/15', '01-15-2024', '2024-1-15', '24-01-15']
        
        for date_str in invalid_formats:
            with pytest.raises(ValidationError, match="must be in YYYY-MM-DD format"):
                validate_date_string(date_str, 'test_field')
    
    def test_validate_invalid_date_values(self):
        """Test validation of invalid date values."""
        invalid_dates = ['2024-13-01', '2024-02-30', '2023-02-29']  # Not leap year
        
        for date_str in invalid_dates:
            with pytest.raises(ValidationError, match="is not a valid date"):
                validate_date_string(date_str, 'test_field')
    
    def test_validate_empty_date_string(self):
        """Test validation of empty date string."""
        # Should be allowed when allow_empty=True
        result = validate_date_string('', 'test_field', allow_empty=True)
        assert result is None
        
        # Should fail when allow_empty=False
        with pytest.raises(ValidationError, match="test_field cannot be empty"):
            validate_date_string('', 'test_field', allow_empty=False)


class TestCurrencyAmountValidation:
    """Test cases for currency amount validation."""
    
    def test_validate_valid_currency_amounts(self):
        """Test validation of valid currency amounts."""
        test_cases = [
            (100, 100.0),
            (99.99, 99.99),
            ('$1,234.56', 1234.56),
            ('1234.56', 1234.56),
            ('$1,000', 1000.0)
        ]
        
        for input_value, expected in test_cases:
            result = validate_currency_amount(input_value, 'test_field')
            assert result == expected
    
    def test_validate_negative_currency(self):
        """Test validation of negative currency amounts."""
        # Should fail by default
        with pytest.raises(ValidationError, match="test_field cannot be negative"):
            validate_currency_amount(-100, 'test_field')
        
        # Should pass when allowed
        result = validate_currency_amount(-100, 'test_field', allow_negative=True)
        assert result == -100.0
    
    def test_validate_empty_currency(self):
        """Test validation of empty currency amount."""
        result = validate_currency_amount(None, 'test_field')
        assert result is None
        
        result = validate_currency_amount('', 'test_field')
        assert result is None
    
    def test_validate_invalid_currency_format(self):
        """Test validation of invalid currency formats."""
        with pytest.raises(ValidationError, match="must be a valid currency amount"):
            validate_currency_amount('not a number', 'test_field')