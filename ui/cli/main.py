#!/usr/bin/env python3
"""
PM Analysis Tool - Command Line Interface

This module provides the main entry point and CLI interface for the PM Analysis Tool.
It uses Click for command-line argument parsing and Rich for enhanced console output
and progress reporting.
"""

import sys
import time
from pathlib import Path
from typing import List, Optional

# Add parent directories to path for imports
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

import click
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.prompt import Confirm
from rich.table import Table
from rich.text import Text

from logic.orchestration.engine import PMAnalysisEngine
from logic.models.models import OperationMode, ProcessingResult
from ui.common.exceptions import ConfigurationError, PMAnalysisError, ValidationError
from ui.common.logger import get_logger

# Initialize console and logger
# Use file parameter to ensure output is captured in tests
console = Console(file=sys.stdout, force_terminal=False)
logger = get_logger(__name__)

# Version information
__version__ = "1.0.0"


@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show version information")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to configuration file (default: config.yaml)",
)
@click.option(
    "--project-path",
    "-p",
    type=click.Path(exists=True, file_okay=False),
    help="Path to project directory",
)
@click.option(
    "--mode",
    "-m",
    type=click.Choice(["document-check", "status-analysis", "learning-module"]),
    help="Operation mode (auto-detected if not specified)",
)
@click.option(
    "--output-format",
    "-o",
    multiple=True,
    type=click.Choice(["markdown", "excel", "console"]),
    help="Output format(s) for reports",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-essential output")
@click.pass_context
def cli(ctx, version, config, project_path, mode, output_format, verbose, quiet):
    """
    PM Analysis Tool - Analyze project management documents and generate insights.

    The tool operates in three modes:

    \b
    • document-check: Verify presence and structure of required PM documents
    • status-analysis: Extract and analyze project data from multiple documents
    • learning-module: Present PM best practices and educational content

    If no mode is specified, the tool will automatically detect the optimal mode
    based on available files in the project directory.

    Examples:

    \b
    # Auto-detect mode and analyze current directory
    pm-analysis

    \b
    # Explicitly run document check on specific directory
    pm-analysis --mode document-check --project-path ./my-project

    \b
    # Generate both markdown and excel reports
    pm-analysis --mode status-analysis -o markdown -o excel

    \b
    # Run with custom configuration
    pm-analysis --config ./custom-config.yaml --verbose
    """
    # Handle version flag
    if version:
        click.echo(f"PM Analysis Tool v{__version__}")
        return

    # Set up context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["config"] = config
    ctx.obj["project_path"] = project_path
    ctx.obj["mode"] = mode
    ctx.obj["output_format"] = list(output_format) if output_format else None
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet

    # If no subcommand is provided, run interactive mode by default
    if ctx.invoked_subcommand is None:
        # Check if any analysis options were provided
        has_analysis_options = any([
            project_path,
            mode,
            output_format,
            verbose and not quiet
        ])
        
        if has_analysis_options:
            # Run traditional CLI analysis
            ctx.invoke(
                analyze,
                config=config,
                project_path=project_path,
                mode=mode,
                output_format=output_format,
                verbose=verbose,
                quiet=quiet,
            )
        else:
            # Run interactive mode
            ctx.invoke(interactive, config=config)


@cli.command()
@click.option("--config", "-c", type=click.Path(exists=True), help="Path to configuration file")
@click.option(
    "--project-path",
    "-p",
    type=click.Path(exists=True, file_okay=False),
    help="Path to project directory",
)
@click.option(
    "--mode",
    "-m",
    type=click.Choice(["document-check", "status-analysis", "learning-module"]),
    help="Operation mode",
)
@click.option(
    "--output-format",
    "-o",
    multiple=True,
    type=click.Choice(["markdown", "excel", "console"]),
    help="Output format(s) for reports",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-essential output")
def analyze(config, project_path, mode, output_format, verbose, quiet):
    """Run PM analysis on project documents."""

    # Configure console output level
    if quiet:
        console.quiet = True

    try:
        # Display welcome message
        if not quiet:
            _display_welcome_banner()

        # Initialize engine
        with console.status("[bold blue]Initializing PM Analysis Engine...") as status:
            try:
                engine = PMAnalysisEngine(config_path=config)
                if verbose:
                    console.print("✓ Engine initialized successfully", style="green")
            except ConfigurationError as e:
                click.echo(f"Configuration Error: {e}", err=True)
                raise click.Abort()
            except Exception as e:
                click.echo(f"Initialization Error: {e}", err=True)
                raise click.Abort()

        # Convert mode string to enum if provided
        operation_mode = None
        if mode:
            mode_mapping = {
                "document-check": OperationMode.DOCUMENT_CHECK,
                "status-analysis": OperationMode.STATUS_ANALYSIS,
                "learning-module": OperationMode.LEARNING_MODULE,
            }
            operation_mode = mode_mapping[mode]

        # Convert output format list
        output_formats = list(output_format) if output_format else None

        # Run analysis with progress tracking
        result = _run_analysis_with_progress(
            engine=engine,
            mode=operation_mode,
            project_path=project_path,
            output_formats=output_formats,
            verbose=verbose,
            quiet=quiet,
        )

        # Display results
        if not quiet:
            _display_results(result, verbose)

        # Exit with appropriate code
        sys.exit(0 if result.success else 1)

    except click.Abort:
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\nAnalysis interrupted by user", err=True)
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error in CLI: {e}", exc_info=True)
        click.echo(f"Unexpected error: {e}", err=True)
        if verbose:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.option("--config", "-c", type=click.Path(exists=True), help="Path to configuration file")
@click.option(
    "--project-path",
    "-p",
    type=click.Path(exists=True, file_okay=False),
    help="Path to project directory",
)
def detect_mode(config, project_path):
    """Detect optimal operation mode based on available files."""

    try:
        console.print("[bold blue]Detecting optimal operation mode...[/bold blue]")

        # Initialize engine
        engine = PMAnalysisEngine(config_path=config)

        # Detect mode
        with console.status("Analyzing project files..."):
            recommendation = engine.detect_optimal_mode(project_path)

        # Display recommendation
        _display_mode_recommendation(recommendation)

    except Exception as e:
        click.echo(f"Mode detection failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--config", "-c", type=click.Path(exists=True), help="Path to configuration file")
@click.option(
    "--project-path",
    "-p",
    type=click.Path(exists=True, file_okay=False),
    help="Path to project directory",
)
def list_files(config, project_path):
    """List available project files without processing them."""

    try:
        console.print("[bold blue]Scanning for project files...[/bold blue]")

        # Initialize engine
        engine = PMAnalysisEngine(config_path=config)

        # Get available files
        with console.status("Scanning directory..."):
            files = engine.get_available_files(project_path)

        # Display files
        _display_file_list(files)

    except Exception as e:
        click.echo(f"File scanning failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--config", "-c", type=click.Path(exists=True), help="Path to configuration file")
def status(config):
    """Show engine status and configuration information."""

    try:
        # Initialize engine
        engine = PMAnalysisEngine(config_path=config)

        # Get status information
        engine_status = engine.get_engine_status()
        processor_info = engine.get_processor_info()

        # Display status
        _display_engine_status(engine_status, processor_info)

    except Exception as e:
        click.echo(f"Status check failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--config", "-c", type=click.Path(exists=True), help="Path to configuration file")
def interactive(config):
    """Run interactive PM analysis with guided dialogs."""
    try:
        _run_interactive_mode(config)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interactive session cancelled by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Error in interactive mode: {e}[/red]")
        # Don't try to access console options for debug
        sys.exit(1)


def _run_interactive_mode(config_path: Optional[str]):
    """Run the interactive mode with guided dialogs."""
    
    # Display welcome
    console.print(Panel(
        Text("Welcome to PM Analysis Tool Interactive Mode", style="bold blue"),
        title="Interactive Analysis",
        border_style="blue",
        padding=(1, 2)
    ))
    
    # Initialize engine
    try:
        with console.status("[bold blue]Initializing PM Analysis Engine..."):
            engine = PMAnalysisEngine(config_path=config_path)
        console.print("[green]✓ Engine initialized successfully[/green]")
    except Exception as e:
        console.print(f"[red]✗ Failed to initialize engine: {e}[/red]")
        return
    
    # Step 1: Project Repository Selection
    project_path = _interactive_project_selection()
    if not project_path:
        console.print("[yellow]No project selected. Exiting.[/yellow]")
        return
    
    # Step 2: Scan and display project files
    console.print(f"\n[bold blue]📁 Scanning project: {project_path}[/bold blue]")
    try:
        with console.status("Scanning for project files..."):
            files = engine.get_available_files(str(project_path))
        
        if files:
            _display_interactive_file_list(files)
        else:
            console.print("[yellow]⚠️  No PM documents found in the selected directory[/yellow]")
            if not Confirm.ask("\nContinue anyway?"):
                return
    except Exception as e:
        console.print(f"[red]✗ Error scanning files: {e}[/red]")
        return
    
    # Step 3: Mode detection and recommendation
    console.print("\n[bold blue]🎯 Analyzing project and recommending operation mode...[/bold blue]")
    try:
        with console.status("Detecting optimal mode..."):
            recommendation = engine.detect_optimal_mode(str(project_path))
        
        _display_interactive_mode_recommendation(recommendation)
        
        # Allow user to override mode
        selected_mode = _interactive_mode_selection(recommendation)
        
    except Exception as e:
        console.print(f"[red]✗ Error detecting mode: {e}[/red]")
        return
    
    # Step 4: Select output formats
    output_formats = _interactive_output_format_selection()
    
    # Step 5: Run analysis
    console.print("\n[bold blue]🚀 Running PM Analysis...[/bold blue]")
    try:
        result = _run_interactive_analysis(
            engine=engine,
            mode=selected_mode,
            project_path=str(project_path),
            output_formats=output_formats
        )
    except Exception as e:
        console.print(f"[red]✗ Analysis failed: {e}[/red]")
        return
    
    # Step 6: Display results and next steps
    _display_interactive_results(result)
    
    # Step 7: Recommend and handle next steps
    _handle_interactive_next_steps(result, engine, project_path)


def _interactive_project_selection() -> Optional[Path]:
    """Interactive project directory selection."""
    
    console.print("\n[bold]📂 Project Repository Selection[/bold]")
    
    # Default to current directory
    current_dir = Path.cwd()
    console.print(f"Current directory: [cyan]{current_dir}[/cyan]")
    
    if Confirm.ask("Use current directory as project root?"):
        return current_dir
    
    # Allow manual input
    while True:
        path_input = click.prompt(
            "\nEnter project directory path",
            type=str,
            default=str(current_dir)
        )
        
        project_path = Path(path_input).expanduser().resolve()
        
        if not project_path.exists():
            console.print(f"[red]✗ Directory does not exist: {project_path}[/red]")
            if not Confirm.ask("Try again?"):
                return None
            continue
        
        if not project_path.is_dir():
            console.print(f"[red]✗ Path is not a directory: {project_path}[/red]")
            if not Confirm.ask("Try again?"):
                return None
            continue
        
        console.print(f"[green]✓ Selected project directory: {project_path}[/green]")
        return project_path


def _display_interactive_file_list(files):
    """Display discovered files in an interactive format."""
    
    if not files:
        console.print("[yellow]No files discovered[/yellow]")
        return
    
    # Create a rich table for better formatting
    table = Table(title=f"Discovered Project Files ({len(files)} total)", show_header=True, header_style="bold cyan")
    table.add_column("📄 File", style="white", width=40)
    table.add_column("📋 Type", style="blue", width=15)
    table.add_column("💾 Size", style="green", width=10)
    table.add_column("✅ Status", style="yellow", width=15)
    
    for file_info in files[:20]:  # Limit to first 20 files
        # Format file size
        if hasattr(file_info, 'size_bytes') and file_info.size_bytes:
            if file_info.size_bytes > 1024 * 1024:
                size_str = f"{file_info.size_bytes / (1024 * 1024):.1f} MB"
            elif file_info.size_bytes > 1024:
                size_str = f"{file_info.size_bytes / 1024:.1f} KB"
            else:
                size_str = f"{file_info.size_bytes} B"
        else:
            size_str = "N/A"
        
        # Get file format
        if hasattr(file_info, 'format') and file_info.format:
            format_str = file_info.format.value.upper()
        else:
            format_str = file_info.path.suffix.upper().lstrip('.')
        
        # Determine status
        if hasattr(file_info, 'is_readable') and file_info.is_readable:
            status = "✅ Ready"
        else:
            status = "⚠️  Check"
        
        # Truncate long filenames
        filename = file_info.path.name
        if len(filename) > 35:
            filename = filename[:32] + "..."
        
        table.add_row(filename, format_str, size_str, status)
    
    console.print(table)
    
    if len(files) > 20:
        console.print(f"[dim]... and {len(files) - 20} more files[/dim]")


def _display_interactive_mode_recommendation(recommendation):
    """Display mode recommendation in interactive format."""
    
    # Main recommendation panel
    recommendation_text = Text()
    recommendation_text.append("🎯 Recommended Mode: ", style="bold")
    recommendation_text.append(recommendation.recommended_mode.value.replace('_', '-').title(), style="bold green")
    recommendation_text.append(f"\n📊 Confidence: {recommendation.confidence_percentage}%", style="cyan")
    recommendation_text.append(f"\n💭 Reasoning: {recommendation.reasoning}", style="white")
    
    panel = Panel(
        recommendation_text,
        title="Mode Analysis Results",
        border_style="green",
        padding=(1, 2)
    )
    console.print(panel)
    
    # Available vs Missing documents
    if hasattr(recommendation, 'available_documents') and recommendation.available_documents:
        console.print("\n[bold green]✅ Available Documents:[/bold green]")
        for doc in recommendation.available_documents[:5]:  # Limit display
            console.print(f"  • {doc.value}")
    
    if hasattr(recommendation, 'missing_documents') and recommendation.missing_documents:
        console.print("\n[bold yellow]📋 Missing Documents:[/bold yellow]")
        for doc in recommendation.missing_documents[:5]:  # Limit display
            console.print(f"  • {doc.value}")


def _interactive_mode_selection(recommendation):
    """Allow user to select or override the recommended mode."""
    
    mode_options = {
        "1": ("document-check", OperationMode.DOCUMENT_CHECK, "📋 Document Check - Verify required documents are present"),
        "2": ("status-analysis", OperationMode.STATUS_ANALYSIS, "📊 Status Analysis - Extract and analyze project data"),
        "3": ("learning-module", OperationMode.LEARNING_MODULE, "📚 Learning Module - Access PM best practices")
    }
    
    recommended_key = None
    for key, (mode_name, mode_enum, _) in mode_options.items():
        if mode_enum == recommendation.recommended_mode:
            recommended_key = key
            break
    
    console.print("\n[bold]🎯 Operation Mode Selection[/bold]")
    
    # Show options
    for key, (mode_name, mode_enum, description) in mode_options.items():
        style = "bold green" if key == recommended_key else "white"
        recommended_marker = " (Recommended)" if key == recommended_key else ""
        console.print(f"  {key}. {description}{recommended_marker}", style=style)
    
    # Get user choice
    if Confirm.ask(f"\nUse recommended mode ({recommendation.recommended_mode.value.replace('_', '-')})?"):
        return recommendation.recommended_mode
    
    while True:
        choice = click.prompt("\nSelect mode (1-3)", type=str, default=recommended_key or "2")
        
        if choice in mode_options:
            selected_mode = mode_options[choice][1]
            console.print(f"[green]✓ Selected mode: {selected_mode.value.replace('_', '-')}[/green]")
            return selected_mode
        else:
            console.print("[red]Invalid choice. Please select 1, 2, or 3.[/red]")


def _interactive_output_format_selection() -> List[str]:
    """Interactive output format selection."""
    
    console.print("\n[bold]📄 Output Format Selection[/bold]")
    
    formats = {
        "markdown": "📝 Markdown - Human-readable text reports",
        "excel": "📊 Excel - Structured data in spreadsheet format",
        "console": "💻 Console - Display results in terminal only"
    }
    
    selected_formats = []
    
    for format_key, description in formats.items():
        if Confirm.ask(f"Generate {description}?", default=(format_key == "markdown")):
            selected_formats.append(format_key)
    
    if not selected_formats:
        console.print("[yellow]No output format selected. Using console output.[/yellow]")
        selected_formats = ["console"]
    
    console.print(f"[green]✓ Selected formats: {', '.join(selected_formats)}[/green]")
    return selected_formats


def _run_interactive_analysis(engine, mode, project_path, output_formats):
    """Run analysis with interactive progress display."""
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        
        # Create progress tasks
        scan_task = progress.add_task("📂 Scanning project files...", total=1)
        mode_task = progress.add_task("🎯 Detecting operation mode...", total=1)
        process_task = progress.add_task("⚙️  Processing documents...", total=1)
        report_task = progress.add_task("📊 Generating reports...", total=1)
        
        try:
            # Simulate progress steps
            progress.update(scan_task, completed=1)
            time.sleep(0.5)
            
            progress.update(mode_task, completed=1)
            time.sleep(0.5)
            
            # Run actual analysis
            result = engine.run(
                mode=mode,
                project_path=project_path,
                output_formats=output_formats
            )
            
            progress.update(process_task, completed=1)
            time.sleep(0.5)
            
            progress.update(report_task, completed=1)
            
            return result
            
        except Exception as e:
            console.print(f"\n[red]✗ Analysis failed: {e}[/red]")
            raise


def _display_interactive_results(result):
    """Display analysis results in interactive format."""
    
    if result.success:
        console.print("\n[bold green]🎉 Analysis Completed Successfully![/bold green]")
        
        # Create results summary
        results_text = Text()
        results_text.append("✅ Status: ", style="bold")
        results_text.append("Success", style="bold green")
        
        if hasattr(result, 'processing_time_seconds'):
            results_text.append(f"\n⏱️  Duration: {result.processing_time_seconds:.2f} seconds", style="cyan")
        
        if hasattr(result, 'operation'):
            results_text.append(f"\n🎯 Operation: {result.operation}", style="white")
        
        panel = Panel(
            results_text,
            title="Analysis Results",
            border_style="green",
            padding=(1, 2)
        )
        console.print(panel)
        
    else:
        console.print("\n[bold red]❌ Analysis Completed with Errors[/bold red]")
        
        if hasattr(result, 'errors') and result.errors:
            console.print("\n[red]Errors encountered:[/red]")
            for error in result.errors[:3]:  # Show first 3 errors
                console.print(f"  • {error}")
    
    # Display any generated reports
    if hasattr(result, 'data') and 'report_summary' in result.data:
        _display_interactive_report_summary(result.data['report_summary'])


def _display_interactive_report_summary(report_summary):
    """Display generated reports summary."""
    
    console.print("\n[bold]📊 Generated Reports[/bold]")
    
    for format_name, report_info in report_summary.items():
        if report_info.get('success', False):
            output_path = report_info.get('output_path', 'N/A')
            console.print(f"  ✅ {format_name.title()}: [cyan]{output_path}[/cyan]")
        else:
            console.print(f"  ❌ {format_name.title()}: Failed to generate")


def _handle_interactive_next_steps(result, engine, project_path):
    """Handle next steps recommendations and user decisions."""
    
    console.print("\n[bold blue]🎯 Recommended Next Steps[/bold blue]")
    
    # Generate next steps based on analysis results
    next_steps = _generate_next_steps_recommendations(result)
    
    if not next_steps:
        console.print("[green]✅ Analysis is complete. No additional actions needed.[/green]")
        return
    
    # Display recommendations
    for i, step in enumerate(next_steps, 1):
        console.print(f"  {i}. {step['description']}")
    
    # Ask user what to do next
    console.print("\n[bold]What would you like to do next?[/bold]")
    console.print("  1. 🔄 Run different analysis mode")
    console.print("  2. 📁 Analyze different project")
    console.print("  3. 📊 View detailed results")
    console.print("  4. 🚪 Exit")
    
    while True:
        choice = click.prompt("\nSelect action (1-4)", type=str, default="4")
        
        if choice == "1":
            # Run different mode
            console.print("\n[blue]🔄 Running different analysis mode...[/blue]")
            _run_interactive_mode(None)  # Restart interactive mode
            break
        elif choice == "2":
            # Analyze different project
            console.print("\n[blue]📁 Selecting different project...[/blue]")
            _run_interactive_mode(None)  # Restart interactive mode
            break
        elif choice == "3":
            # View detailed results
            _display_detailed_results(result)
            # Ask again
            continue
        elif choice == "4":
            console.print("\n[green]👋 Thank you for using PM Analysis Tool![/green]")
            break
        else:
            console.print("[red]Invalid choice. Please select 1, 2, 3, or 4.[/red]")


def _generate_next_steps_recommendations(result):
    """Generate next steps based on analysis results."""
    
    recommendations = []
    
    if not result.success:
        recommendations.append({
            "description": "🔧 Review and fix analysis errors",
            "priority": "high"
        })
    
    # Add recommendations based on operation mode
    if hasattr(result, 'operation'):
        if "document-check" in result.operation:
            recommendations.append({
                "description": "📋 Create missing project documents",
                "priority": "medium"
            })
            recommendations.append({
                "description": "📊 Run status analysis after documents are complete",
                "priority": "medium"
            })
        elif "status-analysis" in result.operation:
            recommendations.append({
                "description": "⚠️  Address identified risks and issues",
                "priority": "high"
            })
            recommendations.append({
                "description": "📈 Update project stakeholders with analysis results",
                "priority": "medium"
            })
    
    return recommendations


def _display_detailed_results(result):
    """Display detailed analysis results."""
    
    console.print("\n[bold blue]🔍 Detailed Analysis Results[/bold blue]")
    
    # Show all available data
    if hasattr(result, 'data') and result.data:
        for key, value in result.data.items():
            console.print(f"\n[bold]{key.replace('_', ' ').title()}:[/bold]")
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    console.print(f"  • {sub_key}: {sub_value}")
            else:
                console.print(f"  {value}")
    
    # Show errors and warnings
    if hasattr(result, 'errors') and result.errors:
        console.print("\n[red]❌ Errors:[/red]")
        for error in result.errors:
            console.print(f"  • {error}")
    
    if hasattr(result, 'warnings') and result.warnings:
        console.print("\n[yellow]⚠️  Warnings:[/yellow]")
        for warning in result.warnings:
            console.print(f"  • {warning}")
    
    click.prompt("\nPress Enter to continue", default="", show_default=False)


def _display_welcome_banner():
    """Display welcome banner with tool information."""
    banner_text = Text()
    banner_text.append("PM Analysis Tool", style="bold blue")
    banner_text.append(f" v{__version__}", style="dim")

    panel = Panel(banner_text, title="Welcome", border_style="blue", padding=(1, 2))
    console.print(panel)


def _run_analysis_with_progress(
    engine: PMAnalysisEngine,
    mode: Optional[OperationMode],
    project_path: Optional[str],
    output_formats: Optional[List[str]],
    verbose: bool,
    quiet: bool,
) -> ProcessingResult:
    """Run analysis with progress tracking and user feedback."""

    if quiet:
        # Run without progress display for quiet mode
        return engine.run(mode=mode, project_path=project_path, output_formats=output_formats)

    # Display progress messages for test compatibility
    click.echo("Scanning project files...")
    time.sleep(0.1)  # Brief pause for visual feedback

    click.echo("Detecting operation mode...")
    time.sleep(0.1)

    click.echo("Processing documents...")

    # Run the actual analysis
    result = engine.run(mode=mode, project_path=project_path, output_formats=output_formats)

    click.echo("Generating reports...")
    time.sleep(0.1)

    click.echo("Analysis complete!")

    return result


def _display_results(result: ProcessingResult, verbose: bool):
    """Display analysis results in a formatted manner."""

    if result.success:
        console.print("\n[bold green]✓ Analysis completed successfully![/bold green]")
    else:
        console.print("\n[bold red]✗ Analysis completed with errors[/bold red]")

    # Display execution summary
    if "execution_summary" in result.data:
        summary = result.data["execution_summary"]

        summary_table = Table(title="Execution Summary", show_header=True, header_style="bold blue")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="white")

        summary_table.add_row("Execution ID", summary.get("execution_id", "N/A"))
        summary_table.add_row("Operation Mode", summary.get("selected_mode", "N/A"))
        summary_table.add_row("Files Discovered", str(summary.get("files_discovered", 0)))
        summary_table.add_row("Files Processed", str(summary.get("files_processed", 0)))
        summary_table.add_row("Reports Generated", str(summary.get("reports_generated", 0)))
        summary_table.add_row("Execution Time", f"{summary.get('total_execution_time', 0):.2f}s")

        console.print(summary_table)

    # Display mode recommendation if available
    if "mode_analysis" in result.data:
        mode_analysis = result.data["mode_analysis"]

        mode_panel = Panel(
            f"Recommended: [bold]{mode_analysis.get('recommended_mode', 'N/A')}[/bold]\n"
            f"Confidence: {mode_analysis.get('confidence_percentage', 0)}%\n"
            f"Reasoning: {mode_analysis.get('reasoning', 'N/A')}",
            title="Mode Analysis",
            border_style="yellow",
        )
        console.print(mode_panel)

    # Display report summary
    if "report_summary" in result.data:
        report_summary = result.data["report_summary"]

        report_table = Table(title="Generated Reports", show_header=True, header_style="bold green")
        report_table.add_column("Format", style="cyan")
        report_table.add_column("Status", style="white")
        report_table.add_column("Output Path", style="dim")

        for format_name, report_info in report_summary.items():
            status = "✓ Success" if report_info["success"] else "✗ Failed"
            status_style = "green" if report_info["success"] else "red"
            output_path = report_info.get("output_path", "N/A")

            report_table.add_row(format_name, Text(status, style=status_style), output_path)

        console.print(report_table)

    # Display errors and warnings
    if result.errors and verbose:
        click.echo("\nErrors:")
        for error in result.errors:
            click.echo(f"  • {error}")

    if result.warnings and verbose:
        click.echo("\nWarnings:")
        for warning in result.warnings:
            click.echo(f"  • {warning}")


def _display_mode_recommendation(recommendation):
    """Display mode recommendation in a formatted manner."""

    # Convert enum value to CLI command format
    mode_display = recommendation.recommended_mode.value.replace("_", "-")

    # Use click.echo for test compatibility
    click.echo(f"Recommended Mode: {mode_display}")
    click.echo(f"Confidence: {recommendation.confidence_percentage}%")
    click.echo(f"Reasoning: {recommendation.reasoning}")

    # Available documents
    if recommendation.available_documents:
        click.echo("\nAvailable Documents:")
        for doc in recommendation.available_documents:
            click.echo(f"  ✓ {doc.value}")

    # Missing documents
    if recommendation.missing_documents:
        click.echo("\nMissing Documents:")
        for doc in recommendation.missing_documents:
            click.echo(f"  ✗ {doc.value}")

    # Alternative modes
    if recommendation.alternative_modes:
        click.echo("\nAlternative Modes:")
        for mode in recommendation.alternative_modes:
            click.echo(f"  • {mode.value}")


def _display_file_list(files):
    """Display list of discovered files in a formatted table."""

    if not files:
        click.echo("No project files found")
        return

    click.echo(f"Discovered Files ({len(files)} total):")
    click.echo("File Name\t\tFormat\tSize\t\tStatus")
    click.echo("-" * 60)

    for file_info in files:
        # Format file size
        size_str = f"{file_info.size_bytes / 1024:.1f} KB" if file_info.size_bytes else "N/A"

        # Determine status
        if file_info.is_readable:
            status = "✓ Readable"
        elif file_info.has_error():
            status = "✗ Error"
        else:
            status = "? Unknown"

        # Get format from file_format or format attribute
        format_str = getattr(file_info, "file_format", "unknown")
        if hasattr(file_info, "format") and file_info.format:
            format_str = file_info.format.value

        click.echo(f"{file_info.name}\t\t{format_str.upper()}\t{size_str}\t\t{status}")


def _display_engine_status(engine_status, processor_info):
    """Display engine status and configuration information."""

    # Engine status
    click.echo("Engine Status:")
    click.echo("-" * 40)
    click.echo(
        f"Engine: {'✓ Initialized' if engine_status['initialized'] else '✗ Not Initialized'}"
    )
    click.echo(f"Configuration: {'✓ Loaded' if engine_status['config_loaded'] else '✗ Not Loaded'}")
    click.echo(f"Last Scan Files: {engine_status['last_scan_file_count']}")
    click.echo(f"Executions: {engine_status['execution_count']}")

    if engine_status["last_recommended_mode"]:
        click.echo(f"Last Recommended Mode: {engine_status['last_recommended_mode']}")

    # Available processors
    if processor_info:
        click.echo("\nAvailable Processors:")
        click.echo("-" * 40)
        for mode, info in processor_info.items():
            click.echo(f"{mode}: {info.get('name', 'Unknown')} v{info.get('version', 'N/A')}")


if __name__ == "__main__":
    cli()
