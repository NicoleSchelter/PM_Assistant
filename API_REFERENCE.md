# PM Analysis Tool - API Reference

This document provides detailed API documentation for the PM Analysis Tool, covering all public classes, methods, and configuration options.

## Table of Contents

1. [Core Classes](#core-classes)
   - [PMAnalysisEngine](#pmanalysisengine)
   - [ConfigManager](#configmanager)
   - [AvatarService](#avatarservice)
2. [Models](#models)
   - [ProcessingResult](#processingresult)
   - [OperationMode](#operationmode)
3. [Processors](#processors)
   - [BaseProcessor](#baseprocessor)
   - [DocumentCheckProcessor](#documentcheckprocessor)
   - [StatusAnalysisProcessor](#statusanalysisprocessor)
   - [LearningModuleProcessor](#learningmoduleprocessor)
4. [Reporters](#reporters)
   - [BaseReporter](#basereporter)
   - [MarkdownReporter](#markdownreporter)
   - [ExcelReporter](#excelreporter)
5. [File Handlers](#file-handlers)
   - [BaseHandler](#basehandler)
   - [MarkdownHandler](#markdownhandler)
   - [ExcelHandler](#excelhandler)
   - [MppHandler](#mpphandler)
6. [Configuration](#configuration)
   - [Configuration Options](#configuration-options)

## Core Classes

### PMAnalysisEngine

The main engine class that orchestrates the analysis process.

```python
from logic.orchestration.engine import PMAnalysisEngine

# Initialize engine with default config
engine = PMAnalysisEngine()

# Initialize engine with custom config
engine = PMAnalysisEngine(config_path="config.yaml")
```

#### Constructor

```python
PMAnalysisEngine(config_path: Optional[str] = None)
```

**Parameters:**
- `config_path` (str, optional): Path to configuration file. Defaults to "config.yaml"

#### Methods

##### run()

Execute the analysis process.

```python
result = engine.run(
    mode="status-analysis",
    project_path="./my-project",
    output_formats=["markdown", "excel"]
)
```

**Parameters:**
- `mode` (str, optional): Operation mode. Options: "document-check", "status-analysis", "learning-module", or "auto"
- `project_path` (str, optional): Path to project directory. Defaults to configured path
- `output_formats` (list[str], optional): Output formats. Options: "markdown", "excel"

**Returns:**
- `ProcessingResult`: Analysis results

##### get_engine_status()

Get engine status information.

```python
status = engine.get_engine_status()
```

**Returns:**
- `dict`: Engine status information

##### get_processor_info()

Get information about available processors.

```python
info = engine.get_processor_info()
```

**Returns:**
- `dict`: Processor information

### ConfigManager

Manages configuration loading and validation.

```python
from logic.orchestration.config_manager import ConfigManager

# Initialize with default config
config_manager = ConfigManager()

# Initialize with custom config
config_manager = ConfigManager("my-config.yaml")
```

#### Constructor

```python
ConfigManager(config_path: Optional[str] = None)
```

**Parameters:**
- `config_path` (str, optional): Path to configuration file. Defaults to "config.yaml"

#### Methods

##### load_config()

Load configuration from file.

```python
config = config_manager.load_config()
```

**Returns:**
- `dict`: Configuration data

##### get_project_config()

Get project configuration.

```python
project_config = config_manager.get_project_config()
```

**Returns:**
- `dict`: Project configuration

##### get_avatar_config()

Get avatar configuration.

```python
avatar_config = config_manager.get_avatar_config()
```

**Returns:**
- `dict`: Avatar configuration

##### get_required_documents()

Get required documents configuration.

```python
docs = config_manager.get_required_documents()
```

**Returns:**
- `list[dict]`: Required documents configuration

##### get_modes_config()

Get operation modes configuration.

```python
modes = config_manager.get_modes_config()
```

**Returns:**
- `dict`: Modes configuration

##### get_output_config()

Get output configuration.

```python
output = config_manager.get_output_config()
```

**Returns:**
- `dict`: Output configuration

##### get_logging_config()

Get logging configuration.

```python
logging = config_manager.get_logging_config()
```

**Returns:**
- `dict`: Logging configuration

##### get_project_path()

Get default project path.

```python
path = config_manager.get_project_path()
```

**Returns:**
- `str`: Default project path

##### is_mode_enabled()

Check if operation mode is enabled.

```python
enabled = config_manager.is_mode_enabled("status-analysis")
```

**Parameters:**
- `mode` (str): Mode name to check

**Returns:**
- `bool`: True if mode is enabled

### AvatarService

Manages avatar functionality with D-ID or HeyGen services.

```python
from service.avatar import AvatarService

# Initialize with configuration
avatar_service = AvatarService(config)
```

#### Constructor

```python
AvatarService(config: dict)
```

**Parameters:**
- `config` (dict): Configuration dictionary containing avatar settings

#### Methods

##### is_enabled()

Check if avatar service is enabled and properly configured.

```python
enabled = avatar_service.is_enabled()
```

**Returns:**
- `bool`: True if avatar service is enabled and configured

##### get_avatar_html()

Generate HTML for displaying the avatar.

```python
html = avatar_service.get_avatar_html(width=400, height=400)
```

**Parameters:**
- `width` (int): Width of the avatar container
- `height` (int): Height of the avatar container

**Returns:**
- `str`: HTML string for embedding the avatar

##### speak()

Make the avatar speak the given text.

```python
video_url = avatar_service.speak("Hello, welcome to the PM Assistant!")
```

**Parameters:**
- `text` (str): Text for the avatar to speak

**Returns:**
- `str`: URL to the generated video/speech or None if failed

## Models

### ProcessingResult

Represents the result of a processing operation.

```python
from logic.models.models import ProcessingResult

result = ProcessingResult(
    success=True,
    operation="status-analysis",
    messages=["Analysis completed successfully"],
    data={"risks": [], "milestones": []}
)
```

#### Attributes

- `success` (bool): Whether the operation was successful
- `operation` (str): Operation mode that was executed
- `messages` (list[str]): Messages from the operation
- `data` (dict): Processed data
- `errors` (list[str], optional): Error messages if any
- `warnings` (list[str], optional): Warning messages if any
- `processing_time_seconds` (float, optional): Processing time in seconds

### OperationMode

Enumeration of available operation modes.

```python
from logic.models.models import OperationMode

mode = OperationMode.DOCUMENT_CHECK
mode = OperationMode.STATUS_ANALYSIS
mode = OperationMode.LEARNING_MODULE
```

Values:
- `DOCUMENT_CHECK`
- `STATUS_ANALYSIS`
- `LEARNING_MODULE`

## Processors

### BaseProcessor

Abstract base class for all processors.

#### Methods

##### process()

Process project files.

```python
result = processor.process(project_path, config)
```

### DocumentCheckProcessor

Processor for document validation.

### StatusAnalysisProcessor

Processor for project status analysis.

### LearningModuleProcessor

Processor for learning content delivery.

## Reporters

### BaseReporter

Abstract base class for all reporters.

#### Methods

##### generate()

Generate report.

```python
reporter.generate(data, output_path)
```

### MarkdownReporter

Reporter for Markdown format.

### ExcelReporter

Reporter for Excel format.

## File Handlers

### BaseHandler

Abstract base class for all file handlers.

#### Methods

##### can_handle()

Check if handler can process file.

```python
can_process = handler.can_handle(file_path)
```

##### extract_data()

Extract data from file.

```python
data = handler.extract_data(file_path)
```

### MarkdownHandler

Handler for Markdown files.

### ExcelHandler

Handler for Excel files.

### MppHandler

Handler for Microsoft Project files.

## Configuration

### Configuration Options

The tool is configured using a YAML file with the following sections:

#### project

Project metadata and settings.

```yaml
project:
  name: "Example Project"
  default_path: "./sample_project"
  description: "Project description"
  owner: "Project Manager"
```

#### avatar

Avatar assistant settings.

```yaml
avatar:
  enabled: true
  provider: "did"
  did:
    api_key: "your-did-api-key"
    avatar_id: "default"
    voice_id: "en-US-JennyNeural"
  heygen:
    api_key: "your-heygen-api-key"
    avatar_id: "default"
    voice_id: "en-US-JennyNeural"
  greeting: "Hello! How can I help you?"
```

#### required_documents

Document requirements configuration.

```yaml
required_documents:
  - name: "Project Charter"
    patterns: ["*charter*"]
    formats: ["md", "docx"]
    required: true
```

#### modes

Operation mode settings.

```yaml
modes:
  document_check:
    enabled: true
    output_formats: ["markdown"]
  status_analysis:
    enabled: true
    output_formats: ["markdown", "excel"]
  learning_module:
    enabled: true
```

#### output

Output settings.

```yaml
output:
  directory: "./reports"
  timestamp_files: true
```

#### logging

Logging configuration.

```yaml
logging:
  level: "INFO"
  file: "pm_analysis.log"
  console: true
```