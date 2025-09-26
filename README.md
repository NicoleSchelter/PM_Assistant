# PM Analysis Tool

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-black)](https://github.com/psf/black)

## Overview

The PM Analysis Tool is a comprehensive project management assistant that analyzes project documentation and provides insights, risk assessments, and recommendations. It supports various document formats including Microsoft Project (.mpp), Excel, Word, and Markdown files.

## Features

- **Document Analysis**: Automatically scans and analyzes project documentation
- **Risk Assessment**: Identifies potential project risks and provides mitigation strategies
- **Progress Tracking**: Monitors project milestones and deliverables
- **Compliance Checking**: Ensures project documents meet required standards
- **Learning Module**: Provides project management education and best practices
- **Avatar Assistant**: Interactive avatar interface using D-ID or HeyGen (Web UI only)

## Supported File Formats

- Microsoft Project (.mpp)
- Microsoft Excel (.xlsx)
- Microsoft Word (.docx)
- Markdown (.md)
- Plain Text (.txt)
- CSV (.csv)

## Installation

### Prerequisites

- Python 3.8 or higher
- Java Runtime Environment (for MPP file processing)
- Virtual environment (recommended)

### Quick Installation

```bash
# Clone the repository
git clone <repository-url>
cd pm-analysis-tool

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run installation script
python install.py
```

### Configuration

The tool uses a YAML configuration file (`config.yaml`) to define:

- Required project documents
- Operation modes
- Output settings
- File processing options
- Avatar assistant settings

To get started:

```bash
# Copy the example configuration
cp config.example.yaml config.yaml

# Edit config.yaml to match your project needs
```

Key configuration sections include:

- `project`: Project metadata and default paths
- `required_documents`: Document types to look for
- `modes`: Operation mode settings
- `avatar`: Avatar assistant configuration (D-ID or HeyGen)
- `output`: Report generation settings

## Usage

### Command Line Interface

```bash
# Basic usage with default configuration
python main.py

# Specify custom configuration
python main.py --config my-config.yaml

# Analyze specific project directory
python main.py --project-path ./my-project

# Run in specific mode
python main.py --mode status-analysis
```

### Web Interface (Streamlit)

```bash
# Run the Streamlit web interface
streamlit run streamlit_app.py
```

The web interface provides a user-friendly way to upload files, configure options, and view results with an interactive avatar assistant.

### Avatar Assistant

The PM Assistant includes an avatar assistant feature that can be enabled in the web interface:

1. Configure API keys for D-ID or HeyGen in `config.yaml`
2. Select your preferred provider in the avatar settings
3. Use the avatar to interact with the tool through natural language

Supported avatar providers:
- **D-ID**: Create realistic avatars with the D-ID platform
- **HeyGen**: Generate avatars with the HeyGen platform

## Operation Modes

### Document Check Mode

Verifies the presence and structure of required project documents.

### Status Analysis Mode

Extracts and analyzes project data to provide insights on:
- Project risks and mitigation strategies
- Milestone tracking and timeline analysis
- Resource allocation
- Stakeholder engagement

### Learning Module Mode

Provides project management education and best practices based on your project data.

## Architecture

The tool follows a clean 4-layer architecture:

1. **UI Layer**: User interfaces (CLI and Web)
2. **Logic Layer**: Business logic and orchestration
3. **Service Layer**: Processing services and operations
4. **Data Layer**: Data access and file handling

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed information.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
