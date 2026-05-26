# tests/test_strategies.py
"""
Test the declarative framework registry.
"""

from vyte.core.config import ProjectConfig
from vyte.strategies.registry import FRAMEWORK_REGISTRY, all_template_paths, get_spec


def test_registry_covers_every_supported_combo():
    """Every (framework, ORM) advertised by the CLI must have a spec."""
    expected = {
        ("Flask-Restx", "SQLAlchemy"),
        ("Flask-Restx", "Peewee"),
        ("FastAPI", "SQLAlchemy"),
        ("FastAPI", "TortoiseORM"),
        ("Django-Rest", "DjangoORM"),
    }
    assert set(FRAMEWORK_REGISTRY) == expected


def test_get_spec_returns_matching_combo():
    cfg = ProjectConfig(
        name="test-fastapi", framework="FastAPI", orm="SQLAlchemy",
        database="PostgreSQL",
    )
    spec = get_spec(cfg)
    assert spec.framework == "FastAPI"
    assert spec.orm == "SQLAlchemy"
    # FastAPI+SQLAlchemy has an Alembic post-generate hook
    assert spec.post_generate is not None


def test_all_template_paths_filters_by_config():
    """Optional features (auth, testing) drop their templates when disabled."""
    cfg_min = ProjectConfig(
        name="t", framework="FastAPI", orm="SQLAlchemy",
        database="PostgreSQL",
        auth_enabled=False, docker_support=False, testing_suite=False,
    )
    cfg_full = ProjectConfig(
        name="t", framework="FastAPI", orm="SQLAlchemy",
        database="PostgreSQL",
        auth_enabled=True, docker_support=True, testing_suite=True,
    )
    paths_min = set(all_template_paths(cfg_min))
    paths_full = set(all_template_paths(cfg_full))
    assert paths_min < paths_full
    assert "common/security.py.j2" in paths_full
    assert "common/security.py.j2" not in paths_min
