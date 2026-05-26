# tests/conftest.py
"""
Pytest configuration and fixtures
"""

import os
import shutil
import stat
import tempfile
import time
from pathlib import Path

import pytest
from click.testing import CliRunner

from vyte.core.config import ProjectConfig
from vyte.core.generator import ProjectGenerator
from vyte.core.renderer import TemplateRenderer


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests"""
    temp = Path(tempfile.mkdtemp())
    yield temp
    if temp.exists():
        # Use a robust rmtree to handle transient Windows file locks
        for _ in range(5):
            try:
                shutil.rmtree(temp)
                break
            except Exception:
                time.sleep(0.1)
        else:
            # Last attempt with onerror handler to try clearing readonly flags
            def _onerror(func, path, excinfo):
                try:
                    os.chmod(path, stat.S_IWRITE)
                    func(path)
                except Exception:
                    pass

            try:
                shutil.rmtree(temp, onerror=_onerror)
            except Exception:
                pass


@pytest.fixture
def sample_config():
    """Sample project configuration"""
    return ProjectConfig(
        name="test-api",
        framework="Flask-Restx",
        orm="SQLAlchemy",
        database="PostgreSQL",
        auth_enabled=True,
        docker_support=True,
        testing_suite=True,
        git_init=False,
    )


@pytest.fixture
def generator():
    """Project generator instance"""
    return ProjectGenerator()


@pytest.fixture
def renderer():
    """Template renderer instance"""
    return TemplateRenderer()


@pytest.fixture
def runner():
    """Reusable Click CLI test runner"""
    return CliRunner()
