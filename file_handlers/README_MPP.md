# Microsoft Project File Handler

## Overview

The MPP Handler (`mpp_handler.py`) provides comprehensive support for processing Microsoft Project (.mpp) files with multiple fallback strategies to ensure compatibility across different environments.

## Features

### Multiple Processing Methods
1. **MPXJ Library** (Primary method)
   - Uses Java-based MPXJ library via py4j bridge
   - Provides the most comprehensive MPP file support
   - Requires Java Runtime Environment

2. **PyWin32 COM Interface** (Windows fallback)
   - Uses Windows COM interface to Microsoft Project
   - Requires Microsoft Project to be installed
   - Windows-only solution

3. **XML Conversion** (Universal fallback)
   - Converts MPP files to XML format for parsing
   - Most compatible but may have limited feature support
   - Works on any platform

### Graceful Fallback System
- Automatically detects available processing methods
- Falls back to alternative methods when primary methods fail
- Logs detailed information about method selection and failures

### Data Extraction Capabilities
- **Milestones**: Extracts milestone information with dates, status, and descriptions
- **Tasks**: Retrieves task details including dependencies, progress, and assignments
- **Resources**: Captures resource information and assignments
- **Timeline Data**: Extracts project timeline, critical path, and scheduling information
- **Project Metadata**: Retrieves project-level information like start/end dates

## Usage

### Basic Usage
```python
from file_handlers.mpp_handler import MPPHandler

handler = MPPHandler()

# Check if handler can process the file
if handler.can_handle("project.mpp"):
    # Extract all data
    data = handler.extract_data("project.mpp")
    
    # Extract specific milestone objects
    milestones = handler.extract_milestones("project.mpp")
    
    # Extract timeline information
    timeline = handler.extract_timeline_data("project.mpp")
```

### Validation
```python
# Validate file structure
result = handler.validate_structure("project.mpp")
if result.is_valid:
    print("File is valid")
else:
    print(f"Validation errors: {result.errors}")
```

### Check Processing Capabilities
```python
# Get information about available processing methods
capabilities = handler.get_processing_capabilities()
print(f"MPXJ available: {capabilities['mpxj_available']}")
print(f"PyWin32 available: {capabilities['pywin32_available']}")
print(f"XML conversion available: {capabilities['xml_conversion_available']}")
```

## Installation Requirements

### For MPXJ Support
```bash
pip install py4j
# Ensure Java Runtime Environment is installed
```

### For PyWin32 Support (Windows only)
```bash
pip install pywin32
# Ensure Microsoft Project is installed
```

### For XML Conversion
No additional dependencies required (uses built-in XML parsing).

## Data Structure

### Extracted Data Format
```python
{
    'project_info': {
        'name': 'Project Name',
        'start_date': '2024-01-01',
        'finish_date': '2024-12-31',
        'file_path': '/path/to/file.mpp',
        'extraction_method': 'MPXJ'
    },
    'milestones': [
        {
            'id': 'milestone_1',
            'name': 'Project Kickoff',
            'date': '2024-01-15',
            'status': 'completed',
            'type': 'project_milestone',
            'description': 'Project start milestone'
        }
    ],
    'tasks': [
        {
            'id': 'task_1',
            'name': 'Design Phase',
            'start_date': '2024-01-16',
            'finish_date': '2024-02-15',
            'duration': 30,
            'percent_complete': 75,
            'is_milestone': False
        }
    ],
    'resources': [
        {
            'id': 'resource_1',
            'name': 'Project Manager',
            'type': 'Work',
            'cost': 5000.00
        }
    ],
    'timeline': {
        'project_start': '2024-01-01',
        'project_finish': '2024-12-31',
        'critical_path': [...],
        'task_dependencies': [...],
        'resource_assignments': [...]
    },
    'extraction_metadata': {
        'method_used': 'MPXJ',
        'extraction_timestamp': '2024-01-15T10:30:00',
        'file_path': '/path/to/file.mpp',
        'file_size': 1048576
    }
}
```

### Milestone Objects
The handler creates `Milestone` domain objects with the following properties:
- `milestone_id`: Unique identifier
- `name`: Milestone name
- `description`: Detailed description
- `target_date`: Target completion date
- `status`: Current status (upcoming, in_progress, completed, overdue, cancelled)
- `milestone_type`: Type of milestone
- `owner`: Responsible person
- `custom_fields`: Additional metadata including source file information

## Error Handling

The handler implements comprehensive error handling:
- **File Not Found**: Raises `FileProcessingError` for missing files
- **Invalid Format**: Validates file extension and basic structure
- **Processing Failures**: Gracefully falls back to alternative methods
- **Partial Extraction**: Continues processing even if some data extraction fails

## Testing

The handler includes comprehensive unit tests covering:
- All processing methods and fallback scenarios
- Error conditions and edge cases
- Data extraction and validation
- Integration testing with mock data

Run tests with:
```bash
python -m pytest tests/test_mpp_handler.py -v
```

## Limitations

1. **MPXJ Method**: Requires Java Runtime Environment
2. **PyWin32 Method**: Windows-only, requires Microsoft Project installation
3. **XML Conversion**: Limited feature support compared to native methods
4. **File Size**: Very large MPP files may require additional memory considerations

## Future Enhancements

- Support for additional MPP file versions
- Enhanced XML conversion capabilities
- Caching of extracted data for large files
- Support for password-protected MPP files
- Integration with cloud-based project management APIs