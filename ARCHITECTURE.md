# PM Assistant - 4-Layer Architecture

This document describes the reorganized 4-layer architecture of the PM Assistant application.

## Architecture Overview

The PM Assistant has been restructured following a clean 4-layer architecture pattern:

```
PM Assistant/
├── ui/                 # Layer 1: User Interface (Presentation)
├── logic/              # Layer 2: Business Logic
├── service/            # Layer 3: Application Services
└── data/               # Layer 4: Data Access
```

## Layer Descriptions

### Layer 1: UI (User Interface/Presentation)
**Location**: `/ui/`

Contains all user interface components and entry points:

- **`ui/cli/`** - Command Line Interface
  - `main.py` - CLI application entry point
  
- **`ui/web/`** - Web Interface
  - `streamlit_app.py` - Streamlit web application
  
- **`ui/common/`** - Shared UI utilities
  - `exceptions.py` - Application exceptions
  - `logger.py` - Logging utilities
  - `validators.py` - Input validation
  - `error_handling.py` - Error handling utilities

**Responsibilities**:
- User interaction handling
- Input validation and sanitization
- Output formatting and presentation
- Error message display

### Layer 2: Logic (Business Logic)
**Location**: `/logic/`

Contains core business logic, domain models, and orchestration:

- **`logic/domain/`** - Business Domain Models
  - `domain.py` - Core business entities (Risk, Deliverable, Milestone, Stakeholder)
  
- **`logic/models/`** - Application Models
  - `models.py` - Data transfer objects and core application models
  
- **`logic/orchestration/`** - Workflow Orchestration
  - `engine.py` - Main application engine and orchestrator
  - `config_manager.py` - Configuration management
  - `mode_detector.py` - Operation mode detection logic
  - `file_scanner.py` - File discovery and scanning

**Responsibilities**:
- Business rule enforcement
- Workflow orchestration
- Domain model definitions
- Core application logic

### Layer 3: Service (Application Services)
**Location**: `/service/`

Contains application services and business operations:

- **`service/processors/`** - Core Processing Services
  - `base_processor.py` - Abstract processor base class
  - `document_check.py` - Document validation processor
  - `status_analysis.py` - Project status analysis processor
  - `learning_module.py` - Learning content processor
  
- **`service/analysis/`** - Analysis Services
  - (Future extension point for specialized analysis services)
  
- **`service/learning/`** - Learning and Training Services
  - `content_loader.py` - Learning content management
  - `presenter.py` - Learning content presentation
  - `modules/` - Learning modules (markdown files)
  
- **`service/reporting/`** - Report Generation Services
  - `base_reporter.py` - Abstract reporter base class
  - `markdown_reporter.py` - Markdown report generation
  - `excel_reporter.py` - Excel report generation

**Responsibilities**:
- Business operation implementation
- Data processing and transformation
- Report generation
- Learning content management

### Layer 4: Data (Data Access)
**Location**: `/data/`

Contains data access, file handling, and persistence logic:

- **`data/handlers/`** - File Format Handlers
  - `base_handler.py` - Abstract file handler base class
  - `markdown_handler.py` - Markdown file processing
  - `excel_handler.py` - Excel file processing
  - `mpp_handler.py` - Microsoft Project file processing
  
- **`data/extractors/`** - Data Extraction
  - `deliverable_extractor.py` - Deliverable data extraction
  - `milestone_extractor.py` - Milestone data extraction
  - `risk_extractor.py` - Risk data extraction
  - `stakeholder_extractor.py` - Stakeholder data extraction
  
- **`data/repositories/`** - Data Repositories
  - (Future extension point for data persistence)
  
- **`data/models/`** - Data Models
  - (Future extension point for data-specific models)

**Responsibilities**:
- File format handling
- Data extraction from various sources
- Data persistence (future)
- External system integration (future)

## Dependency Rules

The architecture follows strict dependency rules:

1. **UI Layer** may depend on:
   - Logic Layer
   - Common utilities

2. **Logic Layer** may depend on:
   - Service Layer
   - Common utilities

3. **Service Layer** may depend on:
   - Data Layer
   - Common utilities

4. **Data Layer** may depend on:
   - Common utilities only

## Benefits of This Architecture

1. **Separation of Concerns**: Each layer has clear responsibilities
2. **Maintainability**: Changes in one layer minimally affect others
3. **Testability**: Each layer can be tested independently
4. **Scalability**: Easy to extend functionality within each layer
5. **Flexibility**: UI can be changed without affecting business logic
6. **Reusability**: Service and Data layers can be reused across different UIs

## Migration Notes

- All import statements have been updated to reflect the new structure
- Original files remain in place for backward compatibility during transition
- Tests will need to be updated to use new import paths
- Configuration may need updates for new module paths

## Usage Examples

### CLI Usage
```bash
# From the ui/cli directory
python main.py --mode status-analysis --project-path ./my-project
```

### Web UI Usage
```bash
# From the ui/web directory
streamlit run streamlit_app.py
```

### Programmatic Usage
```python
from logic.orchestration.engine import PMAnalysisEngine
from logic.models.models import OperationMode

engine = PMAnalysisEngine()
result = engine.run(
    mode=OperationMode.STATUS_ANALYSIS,
    project_path="./my-project"
)
```