#!/usr/bin/env python3
"""
Installation script for PM Analysis Tool.

This script provides an interactive installation process for the PM Analysis Tool,
including dependency checking, environment setup, and configuration.
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple


# Color codes for terminal output
class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_colored(message: str, color: str = Colors.ENDC):
    """Print colored message to terminal."""
    print(f"{color}{message}{Colors.ENDC}")


def print_header(message: str):
    """Print header message."""
    print_colored(f"\n{'='*60}", Colors.HEADER)
    print_colored(f" {message}", Colors.HEADER + Colors.BOLD)
    print_colored(f"{'='*60}", Colors.HEADER)


def print_success(message: str):
    """Print success message."""
    print_colored(f"✓ {message}", Colors.OKGREEN)


def print_warning(message: str):
    """Print warning message."""
    print_colored(f"⚠ {message}", Colors.WARNING)


def print_error(message: str):
    """Print error message."""
    print_colored(f"✗ {message}", Colors.FAIL)


def print_info(message: str):
    """Print info message."""
    print_colored(f"ℹ {message}", Colors.OKBLUE)


def check_python_version() -> bool:
    """Check if Python version meets requirements."""
    print_info("Checking Python version...")

    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print_success(f"Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print_error(
            f"Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+"
        )
        return False


def check_java_installation() -> bool:
    """Check if Java Runtime Environment is installed."""
    print_info("Checking Java Runtime Environment...")

    try:
        result = subprocess.run(["java", "-version"], capture_output=True, text=True, check=True)
        java_version = result.stderr.split("\n")[0]
        print_success(f"Java found: {java_version}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_warning("Java Runtime Environment not found")
        print_info("Java is required for Microsoft Project (.mpp) file support")
        return False


def install_java_instructions():
    """Provide Java installation instructions."""
    print_header("Java Installation Instructions")

    system = platform.system().lower()

    if system == "windows":
        print_info("Windows Java Installation:")
        print("1. Download JRE from: https://www.oracle.com/java/technologies/downloads/")
        print("2. Or install OpenJDK from: https://openjdk.org/")
        print("3. Run the installer and follow the setup wizard")
        print("4. Restart your command prompt after installation")

    elif system == "darwin":  # macOS
        print_info("macOS Java Installation:")
        print("Option 1 - Using Homebrew (recommended):")
        print("  brew install openjdk@11")
        print("\nOption 2 - Manual installation:")
        print("  Download from: https://www.oracle.com/java/technologies/downloads/")

    elif system == "linux":
        print_info("Linux Java Installation:")
        print("Ubuntu/Debian:")
        print("  sudo apt update")
        print("  sudo apt install default-jre")
        print("\nCentOS/RHEL/Fedora:")
        print("  sudo yum install java-11-openjdk")
        print("  # or")
        print("  sudo dnf install java-11-openjdk")

    print("\nAfter installation, verify with: java -version")


def check_pip_installation() -> bool:
    """Check if pip is available."""
    print_info("Checking pip installation...")

    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True, check=True)
        print_success("pip is available")
        return True
    except subprocess.CalledProcessError:
        print_error("pip is not available")
        return False


def create_virtual_environment(venv_path: Path) -> bool:
    """Create a virtual environment."""
    print_info(f"Creating virtual environment at {venv_path}...")

    try:
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
        print_success("Virtual environment created successfully")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to create virtual environment: {e}")
        return False


def get_venv_python(venv_path: Path) -> Path:
    """Get the Python executable path in the virtual environment."""
    if platform.system().lower() == "windows":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"


def install_dependencies(venv_python: Path) -> bool:
    """Install project dependencies."""
    print_info("Installing project dependencies...")

    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print_error("requirements.txt not found")
        return False

    try:
        subprocess.run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], check=True)
        subprocess.run(
            [str(venv_python), "-m", "pip", "install", "-r", "requirements.txt"], check=True
        )
        print_success("Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install dependencies: {e}")
        return False


def setup_configuration() -> bool:
    """Set up initial configuration."""
    print_info("Setting up configuration...")

    config_file = Path("config.yaml")
    example_config = Path("config.example.yaml")

    if config_file.exists():
        print_warning("config.yaml already exists")
        response = input("Do you want to overwrite it? (y/N): ").lower()
        if response != "y":
            print_info("Keeping existing configuration")
            return True

    if example_config.exists():
        try:
            shutil.copy2(example_config, config_file)
            print_success("Configuration file created from example")
            return True
        except Exception as e:
            print_error(f"Failed to copy configuration: {e}")
            return False
    else:
        print_warning("Example configuration not found")
        return False


def create_sample_project() -> bool:
    """Create sample project directory if it doesn't exist."""
    print_info("Setting up sample project...")

    sample_dir = Path("sample_project")
    if sample_dir.exists():
        print_info("Sample project directory already exists")
        return True

    try:
        sample_dir.mkdir(exist_ok=True)
        print_success("Sample project directory created")
        return True
    except Exception as e:
        print_error(f"Failed to create sample project directory: {e}")
        return False


def run_tests(venv_python: Path) -> bool:
    """Run basic tests to verify installation."""
    print_info("Running installation tests...")

    try:
        # Test basic import
        result = subprocess.run(
            [
                str(venv_python),
                "-c",
                'import core.engine; print("Core modules imported successfully")',
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        print_success("Basic import test passed")

        # Test CLI help
        result = subprocess.run(
            [str(venv_python), "main.py", "--help"], capture_output=True, text=True, check=True
        )

        print_success("CLI interface test passed")
        return True

    except subprocess.CalledProcessError as e:
        print_error(f"Installation test failed: {e}")
        return False


def print_activation_instructions(venv_path: Path):
    """Print virtual environment activation instructions."""
    print_header("Virtual Environment Activation")

    system = platform.system().lower()

    if system == "windows":
        activate_script = venv_path / "Scripts" / "activate.bat"
        print_info("To activate the virtual environment on Windows:")
        print(f"  {activate_script}")
        print("\nOr in PowerShell:")
        print(f"  {venv_path / 'Scripts' / 'Activate.ps1'}")

    else:  # macOS/Linux
        activate_script = venv_path / "bin" / "activate"
        print_info("To activate the virtual environment:")
        print(f"  source {activate_script}")

    print("\nAfter activation, you can run:")
    print("  python main.py --help")
    print("  python main.py --version")


def print_usage_examples():
    """Print usage examples."""
    print_header("Usage Examples")

    examples = [
        ("Basic analysis", "python main.py"),
        ("Analyze specific directory", "python main.py --project-path ./my-project"),
        ("Document check mode", "python main.py --mode document-check"),
        ("Status analysis with Excel output", "python main.py --mode status-analysis -o excel"),
        ("Verbose output", "python main.py --verbose"),
        ("Custom configuration", "python main.py --config my-config.yaml"),
    ]

    for description, command in examples:
        print(f"  {description}:")
        print_colored(f"    {command}", Colors.OKCYAN)
        print()


def main():
    """Main installation process."""
    print_header("PM Analysis Tool Installation")
    print_info("This script will help you install and configure the PM Analysis Tool")

    # Check if we're in the right directory
    if not Path("main.py").exists():
        print_error("main.py not found. Please run this script from the PM Assistant directory.")
        sys.exit(1)

    # System checks
    print_header("System Requirements Check")

    checks_passed = True

    # Python version check
    if not check_python_version():
        checks_passed = False

    # pip check
    if not check_pip_installation():
        checks_passed = False

    # Java check (optional)
    java_available = check_java_installation()
    if not java_available:
        install_java = input(
            "\nWould you like to see Java installation instructions? (y/N): "
        ).lower()
        if install_java == "y":
            install_java_instructions()
            input("\nPress Enter to continue after installing Java (or continue without Java)...")

    if not checks_passed:
        print_error("Some system requirements are not met. Please fix them before continuing.")
        sys.exit(1)

    # Installation options
    print_header("Installation Options")

    use_venv = input("Create a virtual environment? (Y/n): ").lower()
    use_venv = use_venv != "n"

    venv_path = None
    venv_python = Path(sys.executable)

    if use_venv:
        venv_name = input("Virtual environment name (default: .venv): ").strip()
        if not venv_name:
            venv_name = ".venv"

        venv_path = Path(venv_name)

        if venv_path.exists():
            print_warning(f"Virtual environment {venv_path} already exists")
            overwrite = input("Overwrite existing virtual environment? (y/N): ").lower()
            if overwrite == "y":
                shutil.rmtree(venv_path)
            else:
                print_info("Using existing virtual environment")

        if not venv_path.exists():
            if not create_virtual_environment(venv_path):
                sys.exit(1)

        venv_python = get_venv_python(venv_path)

    # Install dependencies
    print_header("Installing Dependencies")
    if not install_dependencies(venv_python):
        sys.exit(1)

    # Setup configuration
    print_header("Configuration Setup")
    setup_configuration()

    # Create sample project
    create_sample_project()

    # Run tests
    print_header("Installation Verification")
    if not run_tests(venv_python):
        print_warning("Some tests failed, but installation may still work")

    # Success message
    print_header("Installation Complete!")
    print_success("PM Analysis Tool has been installed successfully!")

    if venv_path:
        print_activation_instructions(venv_path)

    print_usage_examples()

    print_header("Next Steps")
    print_info("1. Activate your virtual environment (if created)")
    print_info("2. Review and customize config.yaml for your needs")
    print_info("3. Place your project files in the sample_project directory")
    print_info("4. Run: python main.py --help to see all available options")
    print_info("5. Start with: python main.py to analyze your project")

    print_colored("\nHappy project analyzing! 🎯", Colors.OKGREEN + Colors.BOLD)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_colored("\n\nInstallation cancelled by user.", Colors.WARNING)
        sys.exit(1)
    except Exception as e:
        print_error(f"Installation failed with error: {e}")
        sys.exit(1)
