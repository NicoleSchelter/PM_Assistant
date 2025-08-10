# Contributing to PM Analysis Tool

Thank you for your interest in contributing to the PM Analysis Tool! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Types of Contributions

We welcome several types of contributions:

- **Bug Reports**: Help us identify and fix issues
- **Feature Requests**: Suggest new functionality or improvements
- **Code Contributions**: Submit bug fixes, new features, or improvements
- **Documentation**: Improve documentation, examples, or tutorials
- **Testing**: Add test cases or improve test coverage
- **Learning Modules**: Contribute new educational content

### Getting Started

1. **Fork the Repository**
   ```bash
   git clone https://github.com/your-username/pm-analysis-tool.git
   cd pm-analysis-tool
   ```

2. **Set Up Development Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # If available
   ```

3. **Run Tests**
   ```bash
   pytest
   pytest --cov=. --cov-report=html  # With coverage
   ```

4. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b bugfix/issue-description
   ```

## 📋 Development Guidelines

### Code Style

We follow PEP 8 style guidelines with some specific conventions:

#### Python Code Standards
- **Line Length**: Maximum 88 characters (Black formatter default)
- **Imports**: Use absolute imports, group by standard library, third-party, local
- **Naming Conventions**:
  - Classes: `PascalCase` (e.g., `RiskExtractor`)
  - Functions/Variables: `snake_case` (e.g., `extract_risks`)
  - Constants: `UPPER_CASE` (e.g., `DEFAULT_CONFIG_PATH`)
  - Private methods: `_leading_underscore`

#### Documentation Standards
- **Docstrings**: Use Google-style docstrings for all public functions and classes
- **Type Hints**: Include type hints for all function parameters and return values
- **Comments**: Use inline comments sparingly, prefer self-documenting code

#### Example Code Style
```python
from typing import List, Dict, Optional
from core.domain import Risk

class RiskExtractor:
    """
    Extracts risk information from various document formats.
    
    This class processes risk management documents and extracts structured
    risk data including probability, impact, and mitigation strategies.
    
    Attributes:
        confidence_threshold: Minimum confidence score for risk extraction
        supported_formats: List of supported file formats
    """
    
    def __init__(self, confidence_threshold: float = 0.7):
        """
        Initialize the risk extractor.
        
        Args:
            confidence_threshold: Minimum confidence score for extraction
            
        Raises:
            ValueError: If confidence_threshold is not between 0 and 1
        """
        if not 0 <= confidence_threshold <= 1:
            raise ValueError("Confidence threshold must be between 0 and 1")
        
        self.confidence_threshold = confidence_threshold
        self.supported_formats = ['.md', '.xlsx', '.docx']
    
    def extract_risks(self, file_path: str) -> List[Risk]:
        """
        Extract risks from the specified file.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            List of extracted Risk objects
            
        Raises:
            FileNotFoundError: If the specified file doesn't exist
            UnsupportedFormatError: If the file format is not supported
        """
        # Implementation here
        pass
```

### Architecture Guidelines

#### Layered Architecture
The project follows a layered architecture pattern:

1. **Presentation Layer** (`main.py`, CLI interface)
2. **Application Layer** (`core/engine.py`, orchestration)
3. **Domain Layer** (`core/domain.py`, business logic)
4. **Infrastructure Layer** (`file_handlers/`, `reporters/`, external integrations)

#### Design Patterns
- **Strategy Pattern**: Different processors for different operation modes
- **Factory Pattern**: File handler and processor creation
- **Abstract Base Classes**: Consistent interfaces for extensibility
- **Dependency Injection**: Configuration and logger injection

#### Adding New Components

##### New File Handler
```python
from file_handlers.base_handler import BaseFileHandler
from core.models import ValidationResult

class NewFormatHandler(BaseFileHandler):
    """Handler for new file format."""
    
    def can_handle(self, file_path: str) -> bool:
        """Check if this handler can process the file."""
        return file_path.lower().endswith('.newformat')
    
    def extract_data(self, file_path: str) -> Dict[str, Any]:
        """Extract structured data from the file."""
        # Implementation
        pass
    
    def validate_structure(self, file_path: str) -> ValidationResult:
        """Validate file structure and content."""
        # Implementation
        pass
```

##### New Processor
```python
from processors.base_processor import BaseProcessor
from core.models import ProcessingResult

class NewModeProcessor(BaseProcessor):
    """Processor for new operation mode."""
    
    def process(self, files: List[str], config: Dict) -> ProcessingResult:
        """Process files according to new mode logic."""
        # Implementation
        pass
    
    def validate_inputs(self, files: List[str]) -> bool:
        """Validate required inputs for processing."""
        # Implementation
        pass
```

### Testing Guidelines

#### Test Structure
- **Unit Tests**: Test individual functions and classes in isolation
- **Integration Tests**: Test component interactions and workflows
- **End-to-End Tests**: Test complete user scenarios

#### Test Naming Convention
```python
def test_should_extract_risks_when_valid_markdown_file():
    """Test that risks are extracted from valid markdown files."""
    pass

def test_should_raise_error_when_file_not_found():
    """Test that FileNotFoundError is raised for missing files."""
    pass
```

#### Test Organization
```
tests/
├── unit/
│   ├── test_risk_extractor.py
│   ├── test_markdown_handler.py
│   └── ...
├── integration/
│   ├── test_document_check_workflow.py
│   ├── test_status_analysis_workflow.py
│   └── ...
├── fixtures/
│   ├── sample_documents/
│   └── test_data/
└── conftest.py
```

#### Writing Good Tests
```python
import pytest
from unittest.mock import Mock, patch
from core.domain import Risk
from extractors.risk_extractor import RiskExtractor

class TestRiskExtractor:
    """Test suite for RiskExtractor class."""
    
    @pytest.fixture
    def risk_extractor(self):
        """Create a RiskExtractor instance for testing."""
        return RiskExtractor(confidence_threshold=0.7)
    
    @pytest.fixture
    def sample_risk_data(self):
        """Sample risk data for testing."""
        return {
            'id': 'R001',
            'description': 'Sample risk',
            'probability': 'High',
            'impact': 'Medium'
        }
    
    def test_should_extract_risks_from_valid_data(self, risk_extractor, sample_risk_data):
        """Test successful risk extraction from valid data."""
        # Arrange
        expected_risk = Risk(
            id='R001',
            description='Sample risk',
            probability='High',
            impact='Medium'
        )
        
        # Act
        with patch.object(risk_extractor, '_parse_file') as mock_parse:
            mock_parse.return_value = [sample_risk_data]
            result = risk_extractor.extract_risks('test_file.md')
        
        # Assert
        assert len(result) == 1
        assert result[0].id == expected_risk.id
        assert result[0].description == expected_risk.description
    
    def test_should_handle_empty_file_gracefully(self, risk_extractor):
        """Test handling of empty files."""
        # Act & Assert
        with patch.object(risk_extractor, '_parse_file') as mock_parse:
            mock_parse.return_value = []
            result = risk_extractor.extract_risks('empty_file.md')
            assert result == []
```

## 🐛 Bug Reports

### Before Submitting a Bug Report

1. **Check existing issues** to avoid duplicates
2. **Update to the latest version** to see if the issue persists
3. **Gather system information** (OS, Python version, dependencies)

### Bug Report Template

```markdown
**Bug Description**
A clear and concise description of the bug.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected Behavior**
A clear description of what you expected to happen.

**Screenshots/Logs**
If applicable, add screenshots or log output to help explain the problem.

**Environment:**
- OS: [e.g., Windows 10, macOS 12.0, Ubuntu 20.04]
- Python Version: [e.g., 3.9.7]
- PM Analysis Tool Version: [e.g., 1.0.0]
- Java Version (if applicable): [e.g., OpenJDK 11.0.2]

**Additional Context**
Add any other context about the problem here.
```

## 💡 Feature Requests

### Feature Request Template

```markdown
**Feature Description**
A clear and concise description of the feature you'd like to see.

**Problem Statement**
What problem does this feature solve? What use case does it address?

**Proposed Solution**
Describe your preferred solution or approach.

**Alternative Solutions**
Describe any alternative solutions or features you've considered.

**Additional Context**
Add any other context, mockups, or examples about the feature request.
```

## 🔄 Pull Request Process

### Before Submitting

1. **Create an Issue**: For significant changes, create an issue first to discuss the approach
2. **Follow Coding Standards**: Ensure your code follows the project's style guidelines
3. **Add Tests**: Include appropriate tests for your changes
4. **Update Documentation**: Update relevant documentation and docstrings
5. **Test Thoroughly**: Run the full test suite and ensure all tests pass

### Pull Request Template

```markdown
**Description**
Brief description of the changes and their purpose.

**Related Issue**
Fixes #(issue number)

**Type of Change**
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

**Testing**
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] I have tested the changes manually

**Checklist**
- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] Any dependent changes have been merged and published
```

### Review Process

1. **Automated Checks**: CI/CD pipeline runs tests and code quality checks
2. **Code Review**: Maintainers review the code for quality and consistency
3. **Testing**: Changes are tested in different environments
4. **Documentation Review**: Documentation changes are reviewed for clarity
5. **Approval**: At least one maintainer approval required for merge

## 📚 Adding Learning Modules

Learning modules are educational content files that help users understand project management concepts.

### Creating a Learning Module

1. **Create Markdown File**: Add a new `.md` file in `learning/modules/`
2. **Follow Structure**: Use the established content structure
3. **Include Examples**: Provide practical examples and use cases
4. **Add Exercises**: Include practice exercises or questions

### Learning Module Template

```markdown
# Module Title

## Overview
Brief description of what this module covers.

## Learning Objectives
By the end of this module, you will be able to:
- Objective 1
- Objective 2
- Objective 3

## Content

### Section 1: Concept Introduction
Explanation of key concepts...

### Section 2: Practical Application
How to apply these concepts...

### Section 3: Best Practices
Industry best practices and recommendations...

## Examples

### Example 1: Scenario Description
Detailed example with step-by-step explanation...

## Practice Exercises

### Exercise 1
Description of the exercise and what to do...

## Summary
Key takeaways from this module...

## Additional Resources
- Link to external resources
- Recommended reading
- Related tools
```

## 🧪 Development Tools

### Recommended Development Setup

#### IDE/Editor Configuration
- **VS Code**: Recommended extensions:
  - Python
  - Pylance
  - Black Formatter
  - autoDocstring
  - GitLens

#### Pre-commit Hooks
```bash
pip install pre-commit
pre-commit install
```

#### Code Quality Tools
```bash
# Formatting
black .

# Linting
flake8 .

# Type checking
mypy .

# Import sorting
isort .

# Security scanning
bandit -r .
```

### Development Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/new-feature
   ```

2. **Make Changes**
   - Write code following style guidelines
   - Add appropriate tests
   - Update documentation

3. **Run Quality Checks**
   ```bash
   black .
   flake8 .
   mypy .
   pytest
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/new-feature
   ```

### Commit Message Convention

We follow the Conventional Commits specification:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

Examples:
```
feat: add support for CSV stakeholder registers
fix: resolve issue with Excel file parsing
docs: update installation instructions
test: add unit tests for risk extractor
```

## 📞 Getting Help

### Communication Channels

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Documentation**: Check the README and inline documentation first

### Questions and Support

Before asking for help:

1. **Search existing issues** and discussions
2. **Check the documentation** and examples
3. **Review the troubleshooting section** in README
4. **Try the latest version** to see if the issue is resolved

When asking for help, please provide:
- Clear description of the problem
- Steps to reproduce the issue
- Your environment details (OS, Python version, etc.)
- Relevant code snippets or error messages
- What you've already tried

## 🏆 Recognition

Contributors will be recognized in:
- **CONTRIBUTORS.md** file
- **Release notes** for significant contributions
- **GitHub contributors** section

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

Thank you for contributing to the PM Analysis Tool! Your efforts help make project management analysis more accessible and effective for everyone. 🎯