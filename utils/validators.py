"""
Input validation utilities for PM Analysis Tool.

This module provides validation functions for various inputs used throughout
the application, ensuring data integrity and proper error handling.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .exceptions import ValidationError


def validate_file_path(file_path: Union[str, Path]) -> Path:
    """
    Validate that a file path exists and is accessible.

    Args:
        file_path: Path to validate

    Returns:
        Validated Path object

    Raises:
        ValidationError: If path is invalid or inaccessible
    """
    if not file_path:
        raise ValidationError("File path cannot be empty")

    path = Path(file_path)

    if not path.exists():
        raise ValidationError(f"File does not exist: {path}")

    if not path.is_file():
        raise ValidationError(f"Path is not a file: {path}")

    if not os.access(path, os.R_OK):
        raise ValidationError(f"File is not readable: {path}")

    return path


def validate_directory_path(dir_path: Union[str, Path]) -> Path:
    """
    Validate that a directory path exists and is accessible.

    Args:
        dir_path: Directory path to validate

    Returns:
        Validated Path object

    Raises:
        ValidationError: If path is invalid or inaccessible
    """
    if not dir_path:
        raise ValidationError("Directory path cannot be empty")

    path = Path(dir_path)

    if not path.exists():
        raise ValidationError(f"Directory does not exist: {path}")

    if not path.is_dir():
        raise ValidationError(f"Path is not a directory: {path}")

    if not os.access(path, os.R_OK):
        raise ValidationError(f"Directory is not readable: {path}")

    return path


def validate_operation_mode(mode: str) -> str:
    """
    Validate operation mode selection.

    Args:
        mode: Operation mode to validate

    Returns:
        Validated mode string

    Raises:
        ValidationError: If mode is invalid
    """
    valid_modes = ["document_check", "status_analysis", "learning_module"]

    if not mode:
        raise ValidationError("Operation mode cannot be empty")

    mode = mode.lower().strip()

    if mode not in valid_modes:
        raise ValidationError(
            f"Invalid operation mode: {mode}. " f"Valid modes are: {', '.join(valid_modes)}"
        )

    return mode


def validate_file_format(file_path: Union[str, Path], expected_formats: List[str]) -> str:
    """
    Validate that a file has one of the expected formats.

    Args:
        file_path: Path to the file
        expected_formats: List of expected file extensions (without dots)

    Returns:
        The file's format/extension

    Raises:
        ValidationError: If file format is not in expected formats
    """
    path = Path(file_path)
    file_extension = path.suffix.lower().lstrip(".")

    if not file_extension:
        raise ValidationError(f"File has no extension: {path}")

    expected_formats_lower = [fmt.lower() for fmt in expected_formats]

    if file_extension not in expected_formats_lower:
        raise ValidationError(
            f"Invalid file format: {file_extension}. "
            f"Expected one of: {', '.join(expected_formats)}"
        )

    return file_extension


def validate_config_structure(config: Dict[str, Any], required_keys: List[str]) -> None:
    """
    Validate that a configuration dictionary has all required keys.

    Args:
        config: Configuration dictionary to validate
        required_keys: List of required keys

    Raises:
        ValidationError: If required keys are missing
    """
    if not isinstance(config, dict):
        raise ValidationError("Configuration must be a dictionary")

    missing_keys = []
    for key in required_keys:
        if key not in config:
            missing_keys.append(key)

    if missing_keys:
        raise ValidationError(f"Missing required configuration keys: {', '.join(missing_keys)}")


def validate_email(email: str) -> str:
    """
    Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        Validated email address

    Raises:
        ValidationError: If email format is invalid
    """
    if not email:
        raise ValidationError("Email address cannot be empty")

    email = email.strip()

    # Basic email regex pattern
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(email_pattern, email):
        raise ValidationError(f"Invalid email format: {email}")

    return email


def validate_date_format(date_string: str, format_pattern: str = r"^\d{4}-\d{2}-\d{2}$") -> str:
    """
    Validate date string format.

    Args:
        date_string: Date string to validate
        format_pattern: Regex pattern for expected date format

    Returns:
        Validated date string

    Raises:
        ValidationError: If date format is invalid
    """
    if not date_string:
        raise ValidationError("Date string cannot be empty")

    date_string = date_string.strip()

    if not re.match(format_pattern, date_string):
        raise ValidationError(f"Invalid date format: {date_string}")

    return date_string


def validate_non_empty_string(value: str, field_name: str) -> str:
    """
    Validate that a string is not empty or whitespace-only.

    Args:
        value: String value to validate
        field_name: Name of the field for error messages

    Returns:
        Validated and stripped string

    Raises:
        ValidationError: If string is empty or whitespace-only
    """
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string")

    value = value.strip()

    if not value:
        raise ValidationError(f"{field_name} cannot be empty")

    return value


def validate_positive_number(value: Union[int, float], field_name: str) -> Union[int, float]:
    """
    Validate that a number is positive.

    Args:
        value: Number to validate
        field_name: Name of the field for error messages

    Returns:
        Validated number

    Raises:
        ValidationError: If number is not positive
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{field_name} must be a number")

    if value <= 0:
        raise ValidationError(f"{field_name} must be positive")

    return value


def validate_percentage(value: Union[int, float], field_name: str) -> float:
    """
    Validate that a number is a valid percentage (0-100).

    Args:
        value: Number to validate as percentage
        field_name: Name of the field for error messages

    Returns:
        Validated percentage as float

    Raises:
        ValidationError: If value is not a valid percentage
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{field_name} must be a number")

    if value < 0 or value > 100:
        raise ValidationError(f"{field_name} must be between 0 and 100")

    return float(value)


def validate_probability(value: Union[int, float], field_name: str) -> float:
    """
    Validate that a number is a valid probability (0.0-1.0).

    Args:
        value: Number to validate as probability
        field_name: Name of the field for error messages

    Returns:
        Validated probability as float

    Raises:
        ValidationError: If value is not a valid probability
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{field_name} must be a number")

    if value < 0.0 or value > 1.0:
        raise ValidationError(f"{field_name} must be between 0.0 and 1.0")

    return float(value)


def validate_wbs_code(wbs_code: str) -> str:
    """
    Validate Work Breakdown Structure code format.

    Args:
        wbs_code: WBS code to validate (e.g., "1.2.3", "A.1.2")

    Returns:
        Validated WBS code

    Raises:
        ValidationError: If WBS code format is invalid
    """
    if not wbs_code:
        raise ValidationError("WBS code cannot be empty")

    wbs_code = wbs_code.strip()

    # Basic WBS code pattern: alphanumeric segments separated by dots
    wbs_pattern = r"^[A-Za-z0-9]+(\.[A-Za-z0-9]+)*$"

    if not re.match(wbs_pattern, wbs_code):
        raise ValidationError(f"Invalid WBS code format: {wbs_code}")

    return wbs_code


def validate_risk_id(risk_id: str) -> str:
    """
    Validate risk ID format.

    Args:
        risk_id: Risk ID to validate

    Returns:
        Validated risk ID

    Raises:
        ValidationError: If risk ID format is invalid
    """
    if not risk_id:
        raise ValidationError("Risk ID cannot be empty")

    risk_id = risk_id.strip()

    # Risk ID pattern: letters, numbers, hyphens, underscores
    risk_pattern = r"^[A-Za-z0-9_-]+$"

    if not re.match(risk_pattern, risk_id):
        raise ValidationError(f"Invalid risk ID format: {risk_id}")

    return risk_id


def validate_stakeholder_id(stakeholder_id: str) -> str:
    """
    Validate stakeholder ID format.

    Args:
        stakeholder_id: Stakeholder ID to validate

    Returns:
        Validated stakeholder ID

    Raises:
        ValidationError: If stakeholder ID format is invalid
    """
    if not stakeholder_id:
        raise ValidationError("Stakeholder ID cannot be empty")

    stakeholder_id = stakeholder_id.strip()

    # Stakeholder ID pattern: letters, numbers, hyphens, underscores
    stakeholder_pattern = r"^[A-Za-z0-9_-]+$"

    if not re.match(stakeholder_pattern, stakeholder_id):
        raise ValidationError(f"Invalid stakeholder ID format: {stakeholder_id}")

    return stakeholder_id


def validate_phone_number(phone: str) -> str:
    """
    Validate phone number format (flexible international format).

    Args:
        phone: Phone number to validate

    Returns:
        Validated phone number

    Raises:
        ValidationError: If phone number format is invalid
    """
    if not phone:
        return ""  # Phone is optional

    phone = phone.strip()

    # Flexible phone pattern: digits, spaces, hyphens, parentheses, plus sign
    phone_pattern = r"^[\+]?[\d\s\-\(\)\.]{7,20}$"

    if not re.match(phone_pattern, phone):
        raise ValidationError(f"Invalid phone number format: {phone}")

    return phone


def validate_enum_value(value: str, enum_class, field_name: str):
    """
    Validate that a string value is a valid enum member.

    Args:
        value: String value to validate
        enum_class: Enum class to validate against
        field_name: Name of the field for error messages

    Returns:
        Validated enum member

    Raises:
        ValidationError: If value is not a valid enum member
    """
    if not value:
        raise ValidationError(f"{field_name} cannot be empty")

    value = value.lower().strip()

    try:
        # Try to find enum member by value
        for member in enum_class:
            if member.value.lower() == value:
                return member

        # If not found, raise error with valid options
        valid_values = [member.value for member in enum_class]
        raise ValidationError(
            f"Invalid {field_name}: {value}. " f"Valid options are: {', '.join(valid_values)}"
        )
    except Exception as e:
        raise ValidationError(f"Error validating {field_name}: {str(e)}")


def validate_list_of_strings(
    value: List[str], field_name: str, allow_empty: bool = True
) -> List[str]:
    """
    Validate that a value is a list of non-empty strings.

    Args:
        value: List to validate
        field_name: Name of the field for error messages
        allow_empty: Whether to allow empty list

    Returns:
        Validated list of strings

    Raises:
        ValidationError: If value is not a valid list of strings
    """
    if not isinstance(value, list):
        raise ValidationError(f"{field_name} must be a list")

    if not allow_empty and len(value) == 0:
        raise ValidationError(f"{field_name} cannot be empty")

    validated_list = []
    for i, item in enumerate(value):
        if not isinstance(item, str):
            raise ValidationError(f"{field_name}[{i}] must be a string")

        item = item.strip()
        if not item:
            raise ValidationError(f"{field_name}[{i}] cannot be empty")

        validated_list.append(item)

    return validated_list


def validate_date_string(
    date_string: str, field_name: str, allow_empty: bool = False
) -> Optional[str]:
    """
    Validate date string in ISO format (YYYY-MM-DD).

    Args:
        date_string: Date string to validate
        field_name: Name of the field for error messages
        allow_empty: Whether to allow empty/None values

    Returns:
        Validated date string or None if empty and allowed

    Raises:
        ValidationError: If date string is invalid
    """
    if not date_string:
        if allow_empty:
            return None
        else:
            raise ValidationError(f"{field_name} cannot be empty")

    date_string = date_string.strip()

    # Validate ISO date format
    iso_date_pattern = r"^\d{4}-\d{2}-\d{2}$"
    if not re.match(iso_date_pattern, date_string):
        raise ValidationError(f"{field_name} must be in YYYY-MM-DD format")

    # Validate that it's a real date
    try:
        from datetime import datetime

        datetime.strptime(date_string, "%Y-%m-%d")
    except ValueError:
        raise ValidationError(f"{field_name} is not a valid date: {date_string}")

    return date_string


def validate_currency_amount(
    value: Union[str, int, float], field_name: str, allow_negative: bool = False
) -> Optional[float]:
    """
    Validate currency amount.

    Args:
        value: Currency amount to validate
        field_name: Name of the field for error messages
        allow_negative: Whether to allow negative amounts

    Returns:
        Validated currency amount as float

    Raises:
        ValidationError: If currency amount is invalid
    """
    if value is None or value == "":
        return None

    try:
        if isinstance(value, str):
            # Remove common currency symbols and whitespace
            cleaned_value = re.sub(r"[$,\s]", "", value.strip())
            amount = float(cleaned_value)
        else:
            amount = float(value)

        if not allow_negative and amount < 0:
            raise ValidationError(f"{field_name} cannot be negative")

        return amount

    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} must be a valid currency amount")
