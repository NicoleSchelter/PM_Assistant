# API Reference

This document provides comprehensive API documentation for the PM Analysis Tool's core components and interfaces.

## Core Engine

### PMAnalysisEngine

The main orchestrator class that coordinates all system components.

```python
from core.engine import PMAnalysisEngine

engine = PMAnalysisEngine(config_path="config.yaml")
result = engine.run(mode=OperationMode.STATUS_ANALYSIS)
```

#### Constructor

```python
def __init__(self, config_path: Optional[str] = None)
```

**Parameters:**
- `config_path` (str, optional): Path to configuration file. Defaults to "config.yaml"

**Raises:**
- `ConfigurationError`: If configuration file is invalid or missing required settings

#### Methods

##### run()

```python
def run(
    self,
    mode: Optional[OperationMode] = None,
    project_path: Optional[str] = None,
    output_formats: Optional[List[str]] = None
) -> ProcessingResult
```

Execute the analysis workflow.

**Parameters:**
- `mode` (OperationMode, optional): Operation mode to use. Auto-detected if not specified
- `project_path` (str, optional): Path to project directory. Uses config default if not specified
- `output_formats` (List[str], optional): Output formats for reports. Uses config default if not specified

**Returns:**
- `ProcessingResult`: Result object containing success status, data, errors, and warnings

**Example:**
```python
result = engine.run(
    mode=OperationMode.STATUS_ANALYSIS,
    project_path="./my-project",
    output_formats=["markdown", "excel"]
)

if result.success:
    print("Analysis completed successfully")
    print(f"Reports generated: {result.data.get('reports', [])}")
else:
    print("Analysis failed:")
    for error in result.errors:
        print(f"  - {error}")
```

##### detect_optimal_mode()

```python
def detect_optimal_mode(self, project_path: Optional[str] = None) -> ModeRecommendation
```

Analyze available files and recommend optimal operation mode.

**Parameters:**
- `project_path` (str, optional): Path to project directory

**Returns:**
- `ModeRecommendation`: Recommendation object with mode, confidence, and reasoning

**Example:**
```python
recommendation = engine.detect_optimal_mode("./project")
print(f"Recommended mode: {recommendation.recommended_mode}")
print(f"Confidence: {recommendation.confidence_percentage}%")
print(f"Reasoning: {recommendation.reasoning}")
```

## Data Models

### Core Models

#### ProcessingResult

```python
@dataclass
class ProcessingResult:
    success: bool
    data: Dict[str, Any]
    errors: List[str]
    warnings: List[str]
    execution_time: float
    timestamp: datetime
```

#### ModeRecommendation

```python
@dataclass
class ModeRecommendation:
    recommended_mode: OperationMode
    confidence_percentage: float
    reasoning: str
    available_documents: List[DocumentType]
    missing_documents: List[DocumentType]
    alternative_modes: List[OperationMode]
```

#### FileInfo

```python
@dataclass
class FileInfo:
    name: str
    path: str
    size_bytes: int
    format: FileFormat
    last_modified: datetime
    is_readable: bool
    document_type: Optional[DocumentType] = None
    confidence_score: float = 0.0
```

### Domain Models

#### Risk

```python
@dataclass
class Risk:
    id: str
    description: str
    probability: str
    impact: str
    status: RiskStatus
    mitigation: str
    owner: str
    category: Optional[str] = None
    due_date: Optional[datetime] = None
    created_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None
```

**Example:**
```python
risk = Risk(
    id="R001",
    description="Budget overrun due to scope changes",
    probability="High",
    impact="High",
    status=RiskStatus.ACTIVE,
    mitigation="Implement strict change control process",
    owner="Project Manager"
)
```

#### Deliverable

```python
@dataclass
class Deliverable:
    id: str
    name: str
    description: str
    status: DeliverableStatus
    due_date: Optional[datetime] = None
    completion_percentage: float = 0.0
    assigned_to: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
```

#### Milestone

```python
@dataclass
class Milestone:
    id: str
    name: str
    date: datetime
    status: MilestoneStatus
    description: str
    dependencies: List[str] = field(default_factory=list)
    critical_path: bool = False
    baseline_date: Optional[datetime] = None
    variance_days: int = 0
```

#### Stakeholder

```python
@dataclass
class Stakeholder:
    name: str
    role: str
    contact: str
    influence: str
    interest: str
    communication_preference: str
    department: Optional[str] = None
    engagement_strategy: Optional[str] = None
```

## File Handlers

### BaseFileHandler

Abstract base class for all file handlers.

```python
from file_handlers.base_handler import BaseFileHandler

class CustomHandler(BaseFileHandler):
    def can_handle(self, file_path: str) -> bool:
        return file_path.lower().endswith('.custom')
    
    def extract_data(self, file_path: str) -> Dict[str, Any]:
        # Implementation
        pass
    
    def validate_structure(self, file_path: str) -> ValidationResult:
        # Implementation
        pass
```

#### Methods

##### can_handle()

```python
@abstractmethod
def can_handle(self, file_path: str) -> bool
```

Check if this handler can process the specified file.

**Parameters:**
- `file_path` (str): Path to the file to check

**Returns:**
- `bool`: True if handler can process the file, False otherwise

##### extract_data()

```python
@abstractmethod
def extract_data(self, file_path: str) -> Dict[str, Any]
```

Extract structured data from the file.

**Parameters:**
- `file_path` (str): Path to the file to process

**Returns:**
- `Dict[str, Any]`: Extracted data in structured format

**Raises:**
- `FileProcessingError`: If file cannot be processed
- `DataExtractionError`: If data extraction fails

##### validate_structure()

```python
@abstractmethod
def validate_structure(self, file_path: str) -> ValidationResult
```

Validate file structure and content.

**Parameters:**
- `file_path` (str): Path to the file to validate

**Returns:**
- `ValidationResult`: Validation result with success status and messages

### MarkdownHandler

Handler for Markdown files.

```python
from file_handlers.markdown_handler import MarkdownHandler

handler = MarkdownHandler()
data = handler.extract_data("Risk Management Plan.md")
```

#### Methods

##### extract_tables()

```python
def extract_tables(self, content: str) -> List[Dict[str, Any]]
```

Extract tables from Markdown content.

**Parameters:**
- `content` (str): Markdown content

**Returns:**
- `List[Dict[str, Any]]`: List of extracted tables with headers and rows

##### extract_sections()

```python
def extract_sections(self, content: str) -> Dict[str, str]
```

Extract sections from Markdown content based on headers.

**Parameters:**
- `content` (str): Markdown content

**Returns:**
- `Dict[str, str]`: Dictionary mapping section titles to content

### ExcelHandler

Handler for Excel files.

```python
from file_handlers.excel_handler import ExcelHandler

handler = ExcelHandler()
data = handler.extract_data("Stakeholder_Register.xlsx")
```

#### Methods

##### extract_sheet_data()

```python
def extract_sheet_data(self, file_path: str, sheet_name: Optional[str] = None) -> pd.DataFrame
```

Extract data from specific Excel sheet.

**Parameters:**
- `file_path` (str): Path to Excel file
- `sheet_name` (str, optional): Name of sheet to extract. Uses first sheet if not specified

**Returns:**
- `pd.DataFrame`: Extracted data as pandas DataFrame

##### get_sheet_names()

```python
def get_sheet_names(self, file_path: str) -> List[str]
```

Get list of sheet names in Excel file.

**Parameters:**
- `file_path` (str): Path to Excel file

**Returns:**
- `List[str]`: List of sheet names

## Processors

### BaseProcessor

Abstract base class for all processors.

```python
from processors.base_processor import BaseProcessor

class CustomProcessor(BaseProcessor):
    def process(self, files: List[str], config: Dict) -> ProcessingResult:
        # Implementation
        pass
    
    def validate_inputs(self, files: List[str]) -> bool:
        # Implementation
        pass
```

#### Methods

##### process()

```python
@abstractmethod
def process(self, files: List[str], config: Dict) -> ProcessingResult
```

Process files according to processor-specific logic.

**Parameters:**
- `files` (List[str]): List of file paths to process
- `config` (Dict): Configuration dictionary

**Returns:**
- `ProcessingResult`: Processing result with success status and data

##### validate_inputs()

```python
@abstractmethod
def validate_inputs(self, files: List[str]) -> bool
```

Validate that required inputs are available for processing.

**Parameters:**
- `files` (List[str]): List of file paths to validate

**Returns:**
- `bool`: True if inputs are valid, False otherwise

### DocumentCheckProcessor

Processor for document verification mode.

```python
from processors.document_check import DocumentCheckProcessor

processor = DocumentCheckProcessor()
result = processor.process(files, config)
```

### StatusAnalysisProcessor

Processor for status analysis mode.

```python
from processors.status_analysis import StatusAnalysisProcessor

processor = StatusAnalysisProcessor()
result = processor.process(files, config)
```

## Extractors

### RiskExtractor

Extract risk information from documents.

```python
from extractors.risk_extractor import RiskExtractor

extractor = RiskExtractor(confidence_threshold=0.7)
risks = extractor.extract_from_file("Risk Management Plan.md")
```

#### Methods

##### extract_from_file()

```python
def extract_from_file(self, file_path: str) -> List[Risk]
```

Extract risks from a single file.

**Parameters:**
- `file_path` (str): Path to file to process

**Returns:**
- `List[Risk]`: List of extracted Risk objects

##### extract_from_markdown()

```python
def extract_from_markdown(self, content: str) -> List[Risk]
```

Extract risks from Markdown content.

**Parameters:**
- `content` (str): Markdown content to process

**Returns:**
- `List[Risk]`: List of extracted Risk objects

##### extract_from_excel()

```python
def extract_from_excel(self, file_path: str, sheet_name: Optional[str] = None) -> List[Risk]
```

Extract risks from Excel file.

**Parameters:**
- `file_path` (str): Path to Excel file
- `sheet_name` (str, optional): Sheet name to process

**Returns:**
- `List[Risk]`: List of extracted Risk objects

### DeliverableExtractor

Extract deliverable information from WBS documents.

```python
from extractors.deliverable_extractor import DeliverableExtractor

extractor = DeliverableExtractor()
deliverables = extractor.extract_from_file("Work Breakdown Structure.md")
```

### MilestoneExtractor

Extract milestone information from roadmap and schedule documents.

```python
from extractors.milestone_extractor import MilestoneExtractor

extractor = MilestoneExtractor()
milestones = extractor.extract_from_file("Project Roadmap.md")
```

### StakeholderExtractor

Extract stakeholder information from stakeholder registers.

```python
from extractors.stakeholder_extractor import StakeholderExtractor

extractor = StakeholderExtractor()
stakeholders = extractor.extract_from_file("Stakeholder_Register.xlsx")
```

## Reporters

### BaseReporter

Abstract base class for all reporters.

```python
from reporters.base_reporter import BaseReporter

class CustomReporter(BaseReporter):
    def generate_report(self, data: Dict[str, Any], output_path: str) -> bool:
        # Implementation
        pass
    
    def get_file_extension(self) -> str:
        return ".custom"
```

### MarkdownReporter

Generate Markdown reports.

```python
from reporters.markdown_reporter import MarkdownReporter

reporter = MarkdownReporter()
success = reporter.generate_report(data, "report.md")
```

### ExcelReporter

Generate Excel reports.

```python
from reporters.excel_reporter import ExcelReporter

reporter = ExcelReporter()
success = reporter.generate_report(data, "report.xlsx")
```

## Configuration

### ConfigManager

Manage configuration loading and validation.

```python
from core.config_manager import ConfigManager

config_manager = ConfigManager("config.yaml")
config = config_manager.get_config()
```

#### Methods

##### get_config()

```python
def get_config(self) -> Dict[str, Any]
```

Get the loaded configuration.

**Returns:**
- `Dict[str, Any]`: Configuration dictionary

##### validate_config()

```python
def validate_config(self, config: Dict[str, Any]) -> bool
```

Validate configuration structure and values.

**Parameters:**
- `config` (Dict[str, Any]): Configuration to validate

**Returns:**
- `bool`: True if configuration is valid

**Raises:**
- `ConfigurationError`: If configuration is invalid

##### get_required_documents()

```python
def get_required_documents(self) -> List[Dict[str, Any]]
```

Get list of required documents from configuration.

**Returns:**
- `List[Dict[str, Any]]`: List of required document configurations

## Utilities

### Logger

Centralized logging utilities.

```python
from utils.logger import get_logger

logger = get_logger(__name__)
logger.info("Processing started")
logger.error("An error occurred", exc_info=True)
```

### Validators

Input validation utilities.

```python
from utils.validators import validate_file_path, validate_date_string

# Validate file path
is_valid = validate_file_path("/path/to/file.md")

# Validate date string
date_obj = validate_date_string("2024-01-15")
```

#### Functions

##### validate_file_path()

```python
def validate_file_path(file_path: str) -> bool
```

Validate that file path exists and is readable.

##### validate_date_string()

```python
def validate_date_string(date_str: str) -> Optional[datetime]
```

Parse and validate date string.

##### validate_probability()

```python
def validate_probability(probability: str) -> bool
```

Validate probability value (High, Medium, Low, or numeric).

## Error Handling

### Exception Hierarchy

```python
from utils.exceptions import (
    PMAnalysisError,
    ConfigurationError,
    FileProcessingError,
    DataExtractionError,
    ValidationError
)

try:
    result = engine.run()
except ConfigurationError as e:
    print(f"Configuration error: {e}")
except FileProcessingError as e:
    print(f"File processing error: {e}")
except PMAnalysisError as e:
    print(f"General analysis error: {e}")
```

### Custom Exceptions

#### PMAnalysisError

Base exception for all PM Analysis Tool errors.

#### ConfigurationError

Raised when configuration is invalid or missing.

#### FileProcessingError

Raised when file processing fails.

#### DataExtractionError

Raised when data extraction fails.

#### ValidationError

Raised when input validation fails.

## Examples

### Basic Usage

```python
from core.engine import PMAnalysisEngine
from core.models import OperationMode

# Initialize engine
engine = PMAnalysisEngine("config.yaml")

# Run analysis
result = engine.run(
    mode=OperationMode.STATUS_ANALYSIS,
    project_path="./my-project",
    output_formats=["markdown", "excel"]
)

# Check results
if result.success:
    print("Analysis completed successfully")
    print(f"Execution time: {result.execution_time:.2f} seconds")
else:
    print("Analysis failed:")
    for error in result.errors:
        print(f"  - {error}")
```

### Custom File Handler

```python
from file_handlers.base_handler import BaseFileHandler
from core.models import ValidationResult

class JSONHandler(BaseFileHandler):
    """Handler for JSON files."""
    
    def can_handle(self, file_path: str) -> bool:
        return file_path.lower().endswith('.json')
    
    def extract_data(self, file_path: str) -> Dict[str, Any]:
        import json
        with open(file_path, 'r') as f:
            return json.load(f)
    
    def validate_structure(self, file_path: str) -> ValidationResult:
        try:
            self.extract_data(file_path)
            return ValidationResult(success=True, messages=[])
        except Exception as e:
            return ValidationResult(success=False, messages=[str(e)])
```

### Custom Extractor

```python
from extractors.base_extractor import BaseExtractor
from core.domain import CustomEntity

class CustomExtractor(BaseExtractor):
    """Extract custom entities from documents."""
    
    def extract_from_file(self, file_path: str) -> List[CustomEntity]:
        # Implementation
        entities = []
        # ... extraction logic ...
        return entities
    
    def extract_from_content(self, content: str) -> List[CustomEntity]:
        # Implementation
        entities = []
        # ... extraction logic ...
        return entities
```

---

This API reference provides comprehensive documentation for extending and using the PM Analysis Tool programmatically. For more examples and detailed usage scenarios, refer to the test files and example implementations in the codebase.