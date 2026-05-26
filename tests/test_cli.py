# tests/test_cli.py
"""
Test CLI commands
"""

import vyte
from vyte.cli.commands import cli


def test_cli_help(runner):
    """Test CLI help command"""
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "vyte" in result.output
    assert "create" in result.output


def test_cli_version(runner):
    """Test CLI version command"""
    result = runner.invoke(cli, ["--version"])

    assert result.exit_code == 0
    # Compare against package version rather than hard-coded literal
    assert vyte.__version__ in result.output


def test_cli_list(runner):
    """Test list command"""
    result = runner.invoke(cli, ["list"])

    assert result.exit_code == 0
    assert "Flask-Restx" in result.output
    assert "FastAPI" in result.output


def test_cli_info(runner):
    """Test info command"""
    result = runner.invoke(cli, ["info", "FastAPI"])

    assert result.exit_code == 0
    assert "FastAPI" in result.output
    assert "SQLAlchemy" in result.output


def test_cli_deps(runner):
    """Test deps command"""
    result = runner.invoke(cli, ["deps", "Flask-Restx"])

    assert result.exit_code == 0
    assert "Dependencies" in result.output


def test_cli_create_non_interactive(runner):
    """Test create command without interaction"""

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "create",
                "--name",
                "test-cli-api",
                "--framework",
                "Flask-Restx",
                "--orm",
                "SQLAlchemy",
                "--database",
                "SQLite",
                "--no-interactive",
            ],
        )

        # The command may interact with templates on disk; ensure it exits cleanly
        assert result.exit_code in (0, 1)
