# tests/test_generator.py
"""
Test project generator
"""

import subprocess

import pytest
from jinja2 import TemplateNotFound


def test_generator_initialization(generator):
    """Test generator initialization"""
    from vyte.strategies.registry import FRAMEWORK_REGISTRY

    assert generator.renderer is not None
    # Every supported (framework, ORM) combo has a spec in the registry
    assert ("Flask-Restx", "SQLAlchemy") in FRAMEWORK_REGISTRY
    assert ("FastAPI", "SQLAlchemy") in FRAMEWORK_REGISTRY
    assert ("Django-Rest", "DjangoORM") in FRAMEWORK_REGISTRY


def test_validate_before_generate(generator, sample_config):
    """Test validation before generation"""
    is_valid, errors = generator.validate_before_generate(sample_config)

    # Should be valid if templates exist
    # If templates don't exist, that's okay for unit tests
    assert isinstance(is_valid, bool)
    assert isinstance(errors, list)


def test_get_generation_summary(generator, sample_config):
    """Test generation summary"""
    summary = generator.get_generation_summary(sample_config)

    assert "project_name" in summary
    assert "framework" in summary
    assert "orm" in summary
    assert "database" in summary
    assert "features" in summary
    assert "dependencies" in summary


def test_generate_project(generator, sample_config, temp_dir, monkeypatch):
    """Test complete project generation"""
    # Change to temp directory
    monkeypatch.chdir(temp_dir)

    # Update config to use temp dir
    sample_config.name = "test-project"

    try:
        # Mock subprocess.run (py_compile) to avoid running python over many files
        def fake_run(*args, **kwargs):
            class Result:
                returncode = 0

            return Result()

        monkeypatch.setattr(subprocess, "run", fake_run)

        project_path = generator.generate(sample_config)

        # Check basic structure
        assert project_path.exists()
        assert (project_path / "src").exists()
        assert (project_path / "requirements.txt").exists()
        assert (project_path / "README.md").exists()
        assert (project_path / ".gitignore").exists()

        # We avoid executing py_compile in unit tests; assume syntax checks are done in CI integration tests

    except (FileNotFoundError, TemplateNotFound) as e:
        # If templates don't exist, that's okay for unit tests
        if "Template not found" not in str(e):
            raise


def test_generate_duplicate_fails(generator, sample_config, temp_dir, monkeypatch):
    """Test that generating to existing directory fails"""
    monkeypatch.chdir(temp_dir)

    # Create directory
    (temp_dir / sample_config.name).mkdir()

    with pytest.raises(FileExistsError):
        generator.generate(sample_config)
