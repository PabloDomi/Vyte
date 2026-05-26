"""
CLI commands for vyte
"""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from ..__version__ import __version__
from ..core.config import (
    COMPATIBILITY_MATRIX,
    ProjectConfig,
    get_compatible_orms,
    get_framework_info,
)
from ..core.dependencies import DependencyManager
from ..core.generator import ProjectGenerator
from ..exceptions import (
    ConfigurationError,
    FileSystemError,
    GenerationError,
    ValidationError,
    VyteError,
)
from .display import (
    show_error,
    show_generation_progress,
    show_next_steps,
    show_success,
    show_summary,
    show_warning,
    show_welcome,
)
from .interactive import interactive_setup

console = Console()


@click.group(name="vyte")
@click.version_option(version=__version__, prog_name="Vyte")
def cli():
    """
    🚀 Vyte - Rapid Development Tool

    Professional API project generator for Python.
    Supports Flask-Restx, FastAPI, and Django-Rest with multiple ORMs.
    """


@cli.command()
@click.option("--name", "-n", help="Project name")
@click.option(
    "--framework",
    "-f",
    type=click.Choice(["Flask-Restx", "FastAPI", "Django-Rest"], case_sensitive=False),
    help="Web framework",
)
@click.option(
    "--orm",
    "-o",
    type=click.Choice(["SQLAlchemy", "TortoiseORM", "Peewee", "DjangoORM"], case_sensitive=False),
    help="ORM/ODM",
)
@click.option(
    "--database",
    "-d",
    type=click.Choice(["PostgreSQL", "MySQL", "SQLite"], case_sensitive=False),
    help="Database type",
)
@click.option("--auth/--no-auth", default=True, help="Include JWT authentication")
@click.option("--docker/--no-docker", default=True, help="Include Docker support")
@click.option("--tests/--no-tests", default=True, help="Include testing suite")
@click.option("--git/--no-git", default=True, help="Initialize Git repository")
@click.option(
    "--interactive/--no-interactive", "-i", default=True, help="Interactive mode (recommended)"
)
def create(name, framework, orm, database, auth, docker, tests, git, interactive):
    """
    Create a new API project

    Examples:

        # Interactive mode (recommended)
        vyte create

        # Quick creation
        vyte create --name my-api --framework FastAPI --orm SQLAlchemy --database PostgreSQL

        # No authentication
        vyte create -n my-api -f Flask-Restx -o SQLAlchemy -d SQLite --no-auth
    """
    show_welcome()

    try:
        # Interactive mode or use provided options
        if interactive or not all([name, framework, orm, database]):
            config = interactive_setup()
        else:
            # Validate configuration
            config = ProjectConfig(
                name=name,
                framework=framework,
                orm=orm,
                database=database,
                auth_enabled=auth,
                docker_support=docker,
                testing_suite=tests,
                git_init=git,
            )

        # Show summary
        show_summary(config)

        # Confirm in interactive mode
        if interactive:
            if not click.confirm("\n✨ Ready to generate project?", default=True):
                show_warning("Operation cancelled")
                return

        # Initialize generator
        generator = ProjectGenerator()

        # Validate before generation
        is_valid, errors = generator.validate_before_generate(config)
        if not is_valid:
            show_error("Validation failed", errors)
            sys.exit(1)

        # Generate project with progress
        project_path = show_generation_progress(generator, config)

        # Initialize git if requested
        if config.git_init:
            _init_git(project_path)

        # Show success and next steps
        show_success(f"Project created successfully at: {project_path}")
        show_next_steps(project_path, config)

    except (ConfigurationError, ValidationError) as e:
        show_error("Configuration Error", [str(e)])
        sys.exit(1)
    except FileExistsError as e:
        show_error(
            "Directory Exists",
            [str(e), "Please choose a different project name or remove the existing directory."],
        )
        sys.exit(1)
    except (FileSystemError, OSError) as e:
        show_error("File System Error", [str(e), "Check permissions and disk space."])
        sys.exit(1)
    except GenerationError as e:
        show_error("Generation Failed", [str(e)])
        sys.exit(1)
    except KeyboardInterrupt:
        show_warning("Operation cancelled by user")
        sys.exit(130)  # Standard exit code for SIGINT
    except VyteError as e:
        show_error("Vyte Error", [str(e)])
        sys.exit(1)
    except Exception as e:  # noqa: BLE001 - Catch-all for unexpected errors with proper reporting
        show_error(
            "Unexpected Error",
            [str(e), "This is a bug. Please report it at https://github.com/PabloDomi/Vyte/issues"],
        )
        console.print_exception()
        sys.exit(1)


@cli.command()
@click.argument(
    "framework", type=click.Choice(["Flask-Restx", "FastAPI", "Django-Rest"], case_sensitive=False)
)
def info(framework):
    """
    Show detailed information about a framework

    Examples:
        vyte info FastAPI
        vyte info Flask-Restx
    """

    framework_info = get_framework_info(framework)

    # Create info table
    table = Table(title=f"ℹ️  {framework} Information", show_header=False)
    table.add_column("Property", style="cyan", width=20)
    table.add_column("Value", style="green")

    table.add_row("Compatible ORMs", ", ".join(framework_info["compatible_orms"]))
    table.add_row("Databases", ", ".join(framework_info["databases"]))
    table.add_row("Async Support", "✅ Yes" if framework_info["async_support"] else "❌ No")

    if framework_info["incompatible_orms"]:
        table.add_row(
            "Incompatible ORMs", ", ".join(framework_info["incompatible_orms"]), style="red"
        )
        table.add_row("Reason", framework_info["reason"], style="yellow")

    console.print("\n")
    console.print(table)
    console.print("\n")


@cli.command()
@click.argument(
    "framework", type=click.Choice(["Flask-Restx", "FastAPI", "Django-Rest"], case_sensitive=False)
)
@click.option("--orm", help="Specific ORM to show dependencies for")
@click.option("--database", "-d", help="Specific database")
@click.option("--auth/--no-auth", default=True, help="Include auth dependencies")
def deps(framework, orm, database, auth):
    """
    Show dependencies for a configuration

    Examples:
        vyte deps FastAPI
        vyte deps Flask-Restx --orm SQLAlchemy --database PostgreSQL
    """
    # Use defaults if not specified
    if not orm:
        orm = get_compatible_orms(framework)[0]
    if not database:
        database = "PostgreSQL"

    # Create config
    config = ProjectConfig(
        name="temp",
        framework=framework,
        orm=orm,
        database=database,
        auth_enabled=auth,
        docker_support=False,
        testing_suite=True,
        git_init=False,
    )

    # Get dependencies
    dependencies = DependencyManager.get_all_dependencies(config)
    deps_info = DependencyManager.get_dependency_info(config)

    # Display
    console.print(
        f"\n[bold cyan]📦 Dependencies for {framework} + {orm} + {database}[/bold cyan]\n"
    )

    # Stats table
    stats_table = Table(show_header=False)
    stats_table.add_column("Category", style="cyan")
    stats_table.add_column("Count", style="green", justify="right")

    stats_table.add_row("Total Dependencies", str(deps_info["total"]))
    stats_table.add_row("Base", str(deps_info["base"]))
    stats_table.add_row("Framework", str(deps_info["framework"]))
    stats_table.add_row("ORM", str(deps_info["orm"]))
    stats_table.add_row("Testing", str(deps_info["testing"]))
    if auth:
        stats_table.add_row("Authentication", str(deps_info["auth"]))

    console.print(stats_table)
    console.print("\n[bold]Package List:[/bold]\n")

    for dep in dependencies:
        console.print(f"  • {dep}")

    console.print("\n")


@cli.command("list")
def list_frameworks():
    """
    List all available frameworks and ORMs
    """
    console.print("\n[bold cyan]📚 Available Frameworks and ORMs[/bold cyan]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Framework", style="cyan", width=15)
    table.add_column("Compatible ORMs", style="green")
    table.add_column("Async", justify="center", width=8)

    for framework, framework_info in COMPATIBILITY_MATRIX.items():
        async_mark = "✅" if framework_info["async_support"] else "❌"
        orms = ", ".join(framework_info["compatible_orms"])
        table.add_row(framework, orms, async_mark)

    console.print(table)
    console.print("\n")


@cli.command()
@click.argument("project_path", type=click.Path(exists=True))
def validate(project_path):
    """
    Validate an existing project structure

    Examples:
        vyte validate ./my-api
    """
    project_path = Path(project_path)

    console.print(f"\n[cyan]🔍 Validating project: {project_path.name}[/cyan]\n")

    checks = []

    # Check for required files
    required_files = [
        "requirements.txt",
        "README.md",
        ".gitignore",
        ".env.example",
    ]

    for file in required_files:
        exists = (project_path / file).exists()
        status = "✅" if exists else "❌"
        checks.append((file, exists, status))

    # Check for src directory
    src_exists = (project_path / "src").exists()
    checks.append(("src/", src_exists, "✅" if src_exists else "❌"))

    # Display results
    table = Table(show_header=True)
    table.add_column("Item", style="cyan")
    table.add_column("Status", justify="center")

    for item, exists, status in checks:
        table.add_row(item, status)

    console.print(table)

    all_valid = all(exists for _, exists, _ in checks)

    if all_valid:
        console.print("\n[green]✅ Project structure is valid![/green]\n")
    else:
        console.print("\n[yellow]⚠️  Some files are missing[/yellow]\n")


@cli.command()
def docs():
    """Open documentation in browser"""
    import webbrowser

    url = "https://github.com/PabloDomi/Vyte"
    console.print(f"\n[cyan]Opening documentation: {url}[/cyan]\n")
    webbrowser.open(url)


def _init_git(project_path: Path):
    """Initialize git repository"""
    import subprocess

    try:
        # Initialize git
        subprocess.run(["git", "init"], cwd=project_path, check=True, capture_output=True)

        # Initial commit
        subprocess.run(["git", "add", "."], cwd=project_path, check=True, capture_output=True)

        subprocess.run(
            ["git", "commit", "-m", "Initial commit from vyte"],
            cwd=project_path,
            check=True,
            capture_output=True,
        )

        console.print("[green]✅ Git repository initialized[/green]")

    except subprocess.CalledProcessError:
        console.print("[yellow]⚠️  Git initialization failed (git may not be installed)[/yellow]")
    except FileNotFoundError:
        console.print("[yellow]⚠️  Git not found. Please install git to use this feature[/yellow]")


if __name__ == "__main__":
    cli()
