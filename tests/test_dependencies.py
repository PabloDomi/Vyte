# tests/test_dependencies.py
"""
Test dependency management
"""

from vyte.core.config import ProjectConfig
from vyte.core.dependencies import DependencyManager


def test_get_all_dependencies():
    """Test getting all dependencies"""
    config = ProjectConfig(
        name="test-api",
        framework="Flask-Restx",
        orm="SQLAlchemy",
        database="PostgreSQL",
        auth_enabled=True,
    )

    deps = DependencyManager.get_all_dependencies(config)

    assert len(deps) > 0
    assert any("flask" in d.lower() for d in deps)
    assert any("sqlalchemy" in d.lower() for d in deps)
    assert any("psycopg2" in d.lower() for d in deps)
    assert any("jwt" in d.lower() for d in deps)


def test_dependency_info():
    """Test dependency statistics"""
    config = ProjectConfig(
        name="test-api",
        framework="FastAPI",
        orm="SQLAlchemy",
        database="PostgreSQL",
        auth_enabled=True,
        testing_suite=True,
    )

    info = DependencyManager.get_dependency_info(config)

    assert info["total"] > 0
    assert info["base"] > 0
    assert info["framework"] > 0
    assert info["orm"] > 0
    assert info["testing"] > 0
    assert info["auth"] > 0


def test_async_driver_selection():
    """Test async driver selection for FastAPI"""
    config = ProjectConfig(
        name="test-api",
        framework="FastAPI",
        orm="SQLAlchemy",
        database="PostgreSQL",
    )

    deps = DependencyManager.get_all_dependencies(config)

    # Should include async driver
    assert any("asyncpg" in d.lower() for d in deps)
    assert not any("psycopg2" in d.lower() for d in deps)


def test_sync_driver_selection():
    """Test sync driver selection for Flask"""
    config = ProjectConfig(
        name="test-api",
        framework="Flask-Restx",
        orm="SQLAlchemy",
        database="PostgreSQL",
    )

    deps = DependencyManager.get_all_dependencies(config)

    # Should include sync driver
    assert any("psycopg2" in d.lower() for d in deps)
    assert not any("asyncpg" in d.lower() for d in deps)
