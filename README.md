# PM Analysis Tool

A comprehensive Python-based project management analysis tool that processes and analyzes project management documents to provide insights on project health, risks, deliverables, milestones, and stakeholder engagement.

## 🚀 Features

- **Multi-format Support**: Process Markdown, Excel, Microsoft Project (.mpp), and Word documents
- **Three Operation Modes**:
  - **Document Check**: Verify presence and structure of required PM documents
  - **Status Analysis**: Extract and analyze project data from multiple documents
  - **Learning Module**: Access PM best practices and educational content
- **Intelligent Mode Detection**: Automatically recommends optimal operation mode based on available files
- **Rich Reporting**: Generate reports in Markdown and Excel formats
- **Extensible Architecture**: Plugin-based design for easy extension with new file types and processors
- **Command-Line Interface**: User-friendly CLI with progress tracking and rich console output

## 📋 Requirements

### System Requirements
- Python 3.8 or higher
- Java Runtime Environment (JRE) 8+ (required for Microsoft Project file support)

### Supported File Formats
- **Markdown** (.md): Project documents, requirements, plans
- **Excel** (.xlsx, .xls): Stakeholder registers, risk registers, data tables
- **Microsoft Project** (.mpp): Project schedules, timelines, resource allocation
- **Word Documents** (.docx): Project documentation (limited support)

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd "PM Assistant"
```

### 2. Create Virtual Environment (Recommended)
```bash
python -m venv .venv

# On Windows
.venv\Scripts\activate

# On macOS/Linux
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Install Java Runtime (for .mpp support)
The tool requires Java Runtime Environment for Microsoft Project file processing:

**Windows:**
- Download and install JRE from [Oracle](https://www.oracle.com/java/technologies/downloads/) or [OpenJDK](https://openjdk.org/)

**macOS:**
```bash
brew install openjdk@11
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install default-jre
```

### 5. Verify Installation
```bash
python main.py --version
```

## 🚀 Quick Start

### Interactive Mode (Recommended for New Users)
The tool features a guided interactive mode that walks you through the entire analysis process:

```bash
# Start interactive mode (default when no parameters provided)
python main_entry.py

# Or explicitly request interactive mode
python main_entry.py interactive
```

The interactive mode provides:
- 🎯 **Guided Project Selection** - Choose and validate project directory
- 📊 **Automatic Mode Detection** - Smart recommendations based on available files
- 🎨 **Visual File Discovery** - See all discovered documents in formatted tables
- 🔧 **Flexible Configuration** - Choose operation mode and output formats
- 📈 **Real-time Progress** - Visual progress tracking during analysis
- 🎯 **Next Steps Guidance** - Recommendations and action options after analysis

For a complete interactive mode walkthrough, see [INTERACTIVE_MODE_DEMO.md](INTERACTIVE_MODE_DEMO.md).

### Traditional CLI Mode
```bash
# Auto-detect mode and analyze current directory
python main.py

# Analyze specific project directory
python main.py --project-path ./my-project

# Use specific operation mode
python main.py --mode status-analysis

# Generate multiple report formats
python main.py --mode status-analysis -o markdown -o excel
```

### Configuration
The tool uses a YAML configuration file (`config.yaml`) to define:
- Required document patterns and formats
- Operation mode settings
- Output preferences
- Logging configuration

Copy and customize the default configuration:
```bash
cp config.yaml my-config.yaml
python main.py --config my-config.yaml
```

## 🏗️ Architecture

The PM Assistant follows a clean 4-layer architecture:

- **UI Layer** (`ui/`) - User interfaces (CLI, Web)
- **Logic Layer** (`logic/`) - Business logic and orchestration
- **Service Layer** (`service/`) - Application services and processors
- **Data Layer** (`data/`) - Data access and file handling

For detailed architecture documentation, see [ARCHITECTURE.md](ARCHITECTURE.md).

## 📖 Usage Guide

### Operation Modes

#### 1. Document Check Mode
Verifies that all required project management documents are present and properly formatted.

```bash
python main.py --mode document-check --project-path ./project
```

**What it checks:**
- Project Charter
- Scope Statement  
- Risk Management Plan
- Work Breakdown Structure
- Project Roadmap/Timeline
- Stakeholder Register

#### 2. Status Analysis Mode
Extracts and consolidates project data from multiple documents to provide comprehensive project insights.

```bash
python main.py --mode status-analysis --project-path ./project -o excel
```

**What it analyzes:**
- Risk status and mitigation progress
- Deliverable completion status
- Milestone tracking and timeline adherence
- Stakeholder engagement levels
- Overall project health metrics

#### 3. Learning Module Mode
Provides access to project management best practices and educational content.

```bash
python main.py --mode learning-module
```

**Available modules:**
- Risk Management Fundamentals
- Stakeholder Analysis Techniques
- Project Scheduling Best Practices

### Command-Line Options

```bash
python main.py [OPTIONS] [COMMAND]

Options:
  --version                     Show version information
  -c, --config PATH            Path to configuration file
  -p, --project-path PATH      Path to project directory
  -m, --mode [document-check|status-analysis|learning-module]
                               Operation mode (auto-detected if not specified)
  -o, --output-format [markdown|excel|console]
                               Output format(s) for reports (can be used multiple times)
  -v, --verbose                Enable verbose output
  -q, --quiet                  Suppress non-essential output
  --help                       Show help message

Commands:
  analyze      Run PM analysis on project documents (default)
  detect-mode  Detect optimal operation mode based on available files
  list-files   List available project files without processing
  status       Show engine status and configuration information
```
##
# Examples

#### Analyze a Complete Project
```bash
# For a project with all required documents
python main.py --project-path ./complete-project --mode status-analysis -o markdown -o excel
```

#### Check Missing Documents
```bash
# For a project missing some documents
python main.py --project-path ./incomplete-project --mode document-check
```

#### Custom Configuration
```bash
# Use custom document requirements
python main.py --config ./custom-config.yaml --project-path ./project
```

#### Verbose Analysis
```bash
# Get detailed output for troubleshooting
python main.py --project-path ./project --verbose
```

## 📁 Project Structure

```
PM Assistant/
├── main.py                     # Entry point and CLI interface
├── config.yaml                 # Default configuration file
├── requirements.txt             # Python dependencies
├── README.md                   # This documentation
├── core/                       # Core business logic
│   ├── engine.py               # Main orchestration engine
│   ├── config_manager.py       # Configuration handling
│   ├── mode_detector.py        # Intelligent mode detection
│   ├── file_scanner.py         # File discovery and validation
│   ├── domain.py               # Domain models (Risk, Deliverable, etc.)
│   └── models.py               # Data structures and enums
├── processors/                 # Operation mode processors
│   ├── document_check.py       # Document verification logic
│   ├── status_analysis.py      # Data extraction and analysis
│   └── learning_module.py      # Learning content presentation
├── file_handlers/              # Format-specific file processing
│   ├── markdown_handler.py     # Markdown file processing
│   ├── excel_handler.py        # Excel file processing
│   └── mpp_handler.py          # Microsoft Project file processing
├── extractors/                 # Data extraction logic
│   ├── risk_extractor.py       # Risk data extraction
│   ├── deliverable_extractor.py # WBS deliverable extraction
│   ├── milestone_extractor.py  # Timeline and milestone extraction
│   └── stakeholder_extractor.py # Stakeholder data extraction
├── reporters/                  # Report generation
│   ├── markdown_reporter.py    # Markdown report generation
│   └── excel_reporter.py       # Excel report generation
├── learning/                   # Learning module system
│   ├── content_loader.py       # Dynamic content loading
│   ├── presenter.py            # Learning module presentation
│   └── modules/                # Learning content directory
├── utils/                      # Shared utilities
│   ├── logger.py               # Centralized logging
│   ├── exceptions.py           # Custom exception classes
│   └── validators.py           # Input validation utilities
└── tests/                      # Comprehensive test suite
    ├── conftest.py             # Pytest fixtures and configuration
    ├── test_data/              # Sample files for testing
    └── test_*.py               # Test files
```

## ⚙️ Configuration

The tool uses a YAML configuration file to customize behavior. Here's the structure:

```yaml
# Project settings
project:
  name: "PM Analysis Project"
  default_path: "./project_files"

# Required documents configuration
required_documents:
  - name: "Project Charter"
    patterns: ["*charter*", "*project*charter*"]
    formats: ["md", "docx"]
    required: true

# Operation modes
modes:
  document_check:
    enabled: true
    output_formats: ["markdown", "console"]
  status_analysis:
    enabled: true
    output_formats: ["markdown", "excel"]
  learning_module:
    enabled: true
    content_path: "./learning/modules"

# Output settings
output:
  directory: "./reports"
  timestamp_files: true
  overwrite_existing: false

# Logging configuration
logging:
  level: "INFO"
  file: "pm_analysis.log"
  console: true
```

### Customizing Document Requirements

You can customize which documents are required and their naming patterns:

```yaml
required_documents:
  - name: "Custom Risk Document"
    patterns: ["*custom*risk*", "*risk*analysis*"]
    formats: ["md", "xlsx"]
    required: true
  - name: "Team Charter"
    patterns: ["*team*charter*", "*charter*"]
    formats: ["md", "docx"]
    required: false
```

## 📊 Sample Project Structure

The tool expects project files to follow standard PM document naming conventions:

```
my-project/
├── Project Charter.md
├── Project Scope Statement.md
├── Risk Management Plan.md
├── Work Breakdown Structure.md
├── Project Roadmap.md
├── Stakeholder_Register.xlsx
├── Risk_Register.xlsx
└── Project_Schedule.mpp
```

### Document Format Examples

#### Risk Management Plan (Markdown)
```markdown
# Risk Management Plan

## Risk Register

| Risk ID | Description | Probability | Impact | Status | Mitigation | Owner |
|---------|-------------|-------------|---------|---------|------------|-------|
| R001 | Budget overrun | High | High | Active | Weekly budget reviews | PM |
| R002 | Resource unavailability | Medium | High | Mitigated | Backup resources identified | RM |
```

#### Stakeholder Register (Excel)
| Name | Role | Contact | Influence | Interest | Communication |
|------|------|---------|-----------|----------|---------------|
| John Smith | Project Sponsor | john@company.com | High | High | Weekly reports |
| Jane Doe | Technical Lead | jane@company.com | Medium | High | Daily standups |#
# 🧪 Testing

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=.

# Run specific test file
pytest tests/test_engine.py

# Run with verbose output
pytest -v
```

### Test Structure
- **Unit Tests**: Test individual components and functions
- **Integration Tests**: Test complete workflows and component interactions
- **Fixture Data**: Sample project files for testing scenarios

## 🔧 Development

### Setting Up Development Environment
```bash
# Install development dependencies
pip install -r requirements.txt

# Install pre-commit hooks (optional)
pip install pre-commit
pre-commit install

# Run code formatting
black .

# Run linting
flake8 .

# Run type checking
mypy .
```

### Adding New File Handlers

1. Create a new handler class inheriting from `BaseFileHandler`
2. Implement required methods: `can_handle()`, `extract_data()`, `validate_structure()`
3. Register the handler in the file handler factory
4. Add corresponding tests

Example:
```python
from file_handlers.base_handler import BaseFileHandler

class CSVHandler(BaseFileHandler):
    def can_handle(self, file_path: str) -> bool:
        return file_path.lower().endswith('.csv')
    
    def extract_data(self, file_path: str) -> Dict:
        # Implementation here
        pass
    
    def validate_structure(self, file_path: str) -> ValidationResult:
        # Implementation here
        pass
```

### Adding New Learning Modules

1. Create a new Markdown file in `learning/modules/`
2. Follow the established content structure
3. The module will be automatically discovered and loaded

## 🐛 Troubleshooting

### Common Issues

#### Java Runtime Not Found
```
Error: Java Runtime Environment not found
```
**Solution**: Install JRE 8+ and ensure it's in your system PATH.

#### Microsoft Project Files Not Processing
```
Error: Cannot process .mpp file
```
**Solutions**:
1. Verify Java installation: `java -version`
2. Check if py4j is installed: `pip show py4j`
3. Try converting .mpp to XML format first

#### Configuration File Not Found
```
Error: Configuration file not found
```
**Solution**: Ensure `config.yaml` exists in the project root or specify path with `--config`.

#### Permission Denied on Output Directory
```
Error: Permission denied writing to reports directory
```
**Solution**: Check write permissions on the output directory or specify a different path in configuration.

### Debug Mode
Enable verbose logging for troubleshooting:
```bash
python main.py --verbose --project-path ./project
```

Check the log file for detailed error information:
```bash
tail -f pm_analysis.log
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Contribution Guidelines
- Follow PEP 8 style guidelines
- Add tests for new functionality
- Update documentation for new features
- Ensure all tests pass before submitting

## 📞 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the troubleshooting section above
- Review the test files for usage examples

## 🔄 Version History

- **v1.0.0**: Initial release with core functionality
  - Document check, status analysis, and learning modules
  - Multi-format file support (Markdown, Excel, MPP)
  - Intelligent mode detection
  - Rich CLI interface and reporting

---

**Happy Project Managing! 🎯**