# tests/integration/test_generated_projects.py
"""
Integration tests for generated projects
"""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from tests.integration._utils import safe_rmtree
from vyte.core.config import ProjectConfig
from vyte.core.generator import ProjectGenerator


@pytest.mark.integration
@pytest.mark.parametrize(
    "framework,orm,database",
    [
        ("Flask-Restx", "SQLAlchemy", "PostgreSQL"),
        ("Flask-Restx", "SQLAlchemy", "SQLite"),
        ("Flask-Restx", "Peewee", "SQLite"),
        ("FastAPI", "SQLAlchemy", "PostgreSQL"),
        ("FastAPI", "TortoiseORM", "PostgreSQL"),
    ],
)
def test_generated_project_structure(framework, orm, database):
    """Test that generated projects have correct structure"""
    temp_dir = Path(tempfile.mkdtemp())

    try:
        config = ProjectConfig(
            name="integration-test",
            framework=framework,
            orm=orm,
            database=database,
            auth_enabled=True,
            docker_support=True,
            testing_suite=True,
            git_init=False,
        )

        generator = ProjectGenerator()

        # Change to temp dir
        original_dir = os.getcwd()
        os.chdir(temp_dir)

        try:
            project_path = generator.generate(config)

            # Verify structure
            assert project_path.exists()
            assert (project_path / "src").is_dir()
            assert (project_path / "src" / "__init__.py").exists()
            assert (project_path / "src" / "models").is_dir()
            assert (project_path / "src" / "routes").is_dir()
            assert (project_path / "src" / "config").is_dir()
            assert (project_path / "requirements.txt").exists()
            assert (project_path / "README.md").exists()
            assert (project_path / ".gitignore").exists()
            assert (project_path / ".env.example").exists()

            # Verify Docker files
            assert (project_path / "Dockerfile").exists()
            assert (project_path / "docker-compose.yml").exists()

            # Verify test files
            assert (project_path / "tests").is_dir()
            assert (project_path / "pytest.ini").exists()

            # Verify Python syntax
            for py_file in project_path.rglob("*.py"):
                result = subprocess.run(
                    ["python", "-m", "py_compile", str(py_file)], capture_output=True, check=False
                )
                if result.returncode != 0:
                    print(f"DEBUG: Compilation error in {py_file}:\n{result.stderr.decode()})")
                assert (
                    result.returncode == 0
                ), f"Syntax error in {py_file}:\n{result.stderr.decode()}"

        finally:
            os.chdir(original_dir)

    finally:
        if temp_dir.exists():
            safe_rmtree(temp_dir)


@pytest.mark.integration
def test_generated_project_installs():
    """Test that dependencies can be installed"""
    temp_dir = Path(tempfile.mkdtemp())

    try:
        config = ProjectConfig(
            name="install-test",
            framework="Flask-Restx",
            orm="SQLAlchemy",
            database="SQLite",
            auth_enabled=False,
            docker_support=False,
            testing_suite=True,
            git_init=False,
        )

        generator = ProjectGenerator()

        original_dir = os.getcwd()
        os.chdir(temp_dir)

        try:
            project_path = generator.generate(config)

            # Create virtual environment
            venv_path = project_path / "venv"
            subprocess.run(["python", "-m", "venv", str(venv_path)], check=True)

            # Install dependencies
            pip_path = venv_path / "bin" / "pip"
            if not pip_path.exists():
                pip_path = venv_path / "Scripts" / "pip.exe"

            result = subprocess.run(
                [str(pip_path), "install", "-r", "requirements.txt"],
                cwd=project_path,
                capture_output=True,
                timeout=300,
                check=False,
            )

            assert (
                result.returncode == 0
            ), f"Failed to install dependencies:\n{result.stderr.decode()}"

        finally:
            os.chdir(original_dir)

    finally:
        if temp_dir.exists():
            safe_rmtree(temp_dir)
