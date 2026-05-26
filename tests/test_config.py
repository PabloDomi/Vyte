# tests/test_config.py
"""
Test configuration module
"""

import pytest
from pydantic import ValidationError

from vyte.core.config import (
    ProjectConfig,
    get_compatible_orms,
    quick_validate,
    validate_combination,
)


def test_valid_config():
    """Test valid configuration"""
    config = ProjectConfig(
        name="my-api",
        framework="Flask-Restx",
        orm="SQLAlchemy",
        database="PostgreSQL",
        auth_enabled=True,
    )

    assert config.name == "my-api"
    assert config.framework == "Flask-Restx"
    assert config.orm == "SQLAlchemy"


def test_invalid_name():
    """Test invalid project name"""
    with pytest.raises(ValidationError):
        ProjectConfig(
            name="My API!",  # Invalid characters
            framework="Flask-Restx",
            orm="SQLAlchemy",
            database="PostgreSQL",
        )


def test_incompatible_combination():
    """Test incompatible framework/ORM combination"""
    with pytest.raises(ValidationError, match="TortoiseORM is not compatible"):
        ProjectConfig(
            name="test-api",
            framework="Flask-Restx",
            orm="TortoiseORM",  # Not compatible with Flask
            database="PostgreSQL",
        )


def test_validate_combination():
    """Test combination validation"""
    # Valid combination
    is_valid, msg = validate_combination("Flask-Restx", "SQLAlchemy")
    assert is_valid
    assert msg == ""

    # Invalid combination
    is_valid, msg = validate_combination("Flask-Restx", "TortoiseORM")
    assert not is_valid
    assert ("async" in msg.lower() and "sync" in msg.lower()) or "synchronous" in msg.lower()


def test_get_compatible_orms():
    """Test getting compatible ORMs"""
    orms = get_compatible_orms("Flask-Restx")
    assert "SQLAlchemy" in orms
    assert "Peewee" in orms
    assert "TortoiseORM" not in orms


def test_quick_validate():
    """Test quick validation"""
    # Valid
    is_valid, errors = quick_validate("Flask-Restx", "SQLAlchemy", "PostgreSQL", "test-api")
    assert is_valid
    assert len(errors) == 0

    # Invalid - no name
    is_valid, errors = quick_validate("Flask-Restx", "SQLAlchemy", "PostgreSQL", "")
    assert not is_valid
    assert len(errors) > 0


def test_config_methods():
    """Test configuration methods"""
    config = ProjectConfig(
        name="test-api",
        framework="FastAPI",
        orm="SQLAlchemy",
        database="PostgreSQL",
    )

    assert config.is_async_framework() is True
    assert config.get_port() == 8000
    # python_version reflects the current runtime (e.g. "3.11", "3.12", "3.13")
    pv = config.get_python_version()
    assert pv.startswith("3.") and pv.count(".") == 1

    # Flask config
    config_flask = ProjectConfig(
        name="test-api",
        framework="Flask-Restx",
        orm="SQLAlchemy",
        database="PostgreSQL",
    )

    assert config_flask.is_async_framework() is False
    assert config_flask.get_port() == 5300
