"""
Template rendering system using Jinja2
"""

import datetime
import re
from pathlib import Path
from typing import Any

from jinja2 import ChoiceLoader, Environment, FileSystemLoader, PackageLoader, TemplateNotFound


class TemplateRenderer:
    """
    Renders Jinja2 templates with project configuration
    """

    def __init__(self, template_dir: Path | None = None):
        """
        Initialize template renderer

        Args:
            template_dir: Path to templates directory.
                         If None, uses default templates/ in package
        """
        # Resolve template loader(s).
        # Priority:
        # 1. explicit template_dir if provided and exists -> FileSystemLoader
        # 2. package-internal `vyte/templates` -> FileSystemLoader
        # 3. top-level `templates/` (repo-style) -> FileSystemLoader
        # 4. PackageLoader('vyte', 'templates') as fallback for installed packages

        package_dir = Path(__file__).parent.parent
        fs_template_pkg = package_dir / "templates"  # vyte/templates
        fs_template_top = package_dir.parent / "templates"  # ../templates

        loaders = []
        chosen_fs: Path | None = None

        if template_dir is not None:
            p = Path(template_dir)
            if p.exists():
                loaders.append(FileSystemLoader(str(p)))
                chosen_fs = p
            else:
                raise FileNotFoundError(f"Templates directory not found: {p}")
        else:
            if fs_template_pkg.exists():
                loaders.append(FileSystemLoader(str(fs_template_pkg)))
                chosen_fs = fs_template_pkg

            if fs_template_top.exists():
                loaders.append(FileSystemLoader(str(fs_template_top)))
                if chosen_fs is None:
                    chosen_fs = fs_template_top

            # PackageLoader fallback (works when templates are packaged inside the vyte package)
            try:
                loaders.append(PackageLoader("vyte", "templates"))
            except (ImportError, ValueError, ModuleNotFoundError):
                # Ignore if PackageLoader cannot be created (e.g., in development)
                pass

        if not loaders:
            raise FileNotFoundError(
                "Templates directory not found: tried vyte/templates and ../templates"
            )

        self.template_dir = chosen_fs

        loader = ChoiceLoader(loaders) if len(loaders) > 1 else loaders[0]

        # Configure Jinja2 environment with chosen loader(s)
        self.env = Environment(
            loader=loader,
            trim_blocks=False,
            lstrip_blocks=False,
            keep_trailing_newline=True,
        )

        # Add custom filters
        self.env.filters["pascal_case"] = self._pascal_case
        self.env.filters["snake_case"] = self._snake_case
        self.env.filters["kebab_case"] = self._kebab_case
        self.env.filters["title_case"] = self._title_case

        # Add custom globals
        self.env.globals["now"] = datetime.datetime.now
        self.env.globals["year"] = datetime.datetime.now().year

    @staticmethod
    def _pascal_case(text: str) -> str:
        """Convert text to PascalCase"""
        return "".join(word.capitalize() for word in text.replace("-", "_").split("_"))

    @staticmethod
    def _snake_case(text: str) -> str:
        """Convert text to snake_case"""
        # Handle PascalCase/camelCase
        text = re.sub("([A-Z]+)", r"_\1", text).lower()
        # Handle kebab-case
        text = text.replace("-", "_")
        # Remove duplicate underscores
        text = re.sub("_+", "_", text)
        return text.strip("_")

    @staticmethod
    def _kebab_case(text: str) -> str:
        """Convert text to kebab-case"""
        return TemplateRenderer._snake_case(text).replace("_", "-")

    @staticmethod
    def _title_case(text: str) -> str:
        """Convert text to Title Case"""
        return text.replace("_", " ").replace("-", " ").title()

    def render(self, template_path: str, context: dict[str, Any]) -> str:
        """
        Render a template with given context

        Args:
            template_path: Relative path to template (e.g., 'flask_restx/init.py.j2')
            context: Dictionary of variables to pass to template

        Returns:
            Rendered template as string

        Raises:
            TemplateNotFound: If template doesn't exist
        """
        try:
            template = self.env.get_template(template_path)
            return template.render(**context)
        except TemplateNotFound as exc:
            raise TemplateNotFound(
                f"Template not found: {template_path}\n" f"Looking in: {self.template_dir}"
            ) from exc

    def render_to_file(
        self,
        template_path: str,
        output_path: Path,
        context: dict[str, Any],
        create_dirs: bool = True,
    ):
        """
        Render template and write to file

        Args:
            template_path: Relative path to template
            output_path: Path where to write rendered content
            context: Dictionary of variables to pass to template
            create_dirs: If True, create parent directories if they don't exist
        """
        content = self.render(template_path, context)

        if create_dirs:
            output_path.parent.mkdir(parents=True, exist_ok=True)

        output_path.write_text(content, encoding="utf-8")

    def template_exists(self, template_path: str) -> bool:
        """Check if a template exists"""
        try:
            self.env.get_template(template_path)
            return True
        except TemplateNotFound:
            return False

    def list_templates(self, pattern: str | None = None) -> list[str]:
        """
        List all available templates

        Args:
            pattern: Optional glob pattern to filter templates (e.g., 'flask_*/*.j2')

        Returns:
            List of template paths
        """
        templates = []

        if pattern:
            templates = [
                str(p.relative_to(self.template_dir))
                for p in self.template_dir.glob(pattern)
                if p.is_file()
            ]
        else:
            templates = [
                str(p.relative_to(self.template_dir))
                for p in self.template_dir.rglob("*.j2")
                if p.is_file()
            ]

        return sorted(templates)

    def get_template_info(self, template_path: str) -> dict[str, Any]:
        """
        Get information about a template

        Returns:
            Dictionary with template metadata
        """
        full_path = self.template_dir / template_path

        if not full_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        stat = full_path.stat()

        return {
            "path": template_path,
            "full_path": str(full_path),
            "size": stat.st_size,
            "modified": datetime.datetime.fromtimestamp(stat.st_mtime),
            "exists": True,
        }

    def validate_context(self, template_path: str, context: dict[str, Any]) -> list[str]:
        """
        Validate if context has all required variables for template

        Returns:
            List of missing variables (empty if all present)
        """

        try:
            template = self.env.get_template(template_path)
            source = template.source

            # Find all variables used in template
            var_pattern = r"\{\{\s*(\w+)"
            used_vars = set(re.findall(var_pattern, source))

            # Check which are missing from context
            missing = used_vars - set(context.keys())

            return sorted(missing)
        except TemplateNotFound:
            return []


class TemplateRegistry:
    """
    Registry of all template paths for different configurations
    Maps framework/orm combinations to their template files
    """

    # Template mappings
    TEMPLATES = {
        "Flask-Restx": {
            "SQLAlchemy": {
                "init": "flask_restx/sqlalchemy/__init__.py.j2",
                "extensions": "flask_restx/sqlalchemy/extensions.py.j2",
                "models": "flask_restx/sqlalchemy/models.py.j2",
                "routes": "flask_restx/sqlalchemy/routes.py.j2",
                "config": "flask_restx/sqlalchemy/config.py.j2",
                "app": "flask_restx/sqlalchemy/app.py.j2",
            },
            "Peewee": {
                "init": "flask_restx/peewee/__init__.py.j2",
                "extensions": "flask_restx/peewee/extensions.py.j2",
                "models": "flask_restx/peewee/models.py.j2",
                "routes": "flask_restx/peewee/routes.py.j2",
                "config": "flask_restx/peewee/config.py.j2",
                "app": "flask_restx/peewee/app.py.j2",
            },
        },
        "FastAPI": {
            "SQLAlchemy": {
                "main": "fastapi/sqlalchemy/main.py.j2",
                "database": "fastapi/sqlalchemy/database.py.j2",
                "models": "fastapi/sqlalchemy/models.py.j2",
                "routes": "fastapi/sqlalchemy/routes.py.j2",
                "config": "fastapi/sqlalchemy/config.py.j2",
                "schemas": "fastapi/sqlalchemy/schemas.py.j2",
            },
            "TortoiseORM": {
                "main": "fastapi/tortoise/main.py.j2",
                "database": "fastapi/tortoise/database.py.j2",
                "models": "fastapi/tortoise/models.py.j2",
                "routes": "fastapi/tortoise/routes.py.j2",
                "config": "fastapi/tortoise/config.py.j2",
                "schemas": "fastapi/tortoise/schemas.py.j2",
            },
        },
        "Django-Rest": {
            "DjangoORM": {
                "settings": "django-rest/djangoORM/settings.py.j2",
                "urls": "django-rest/djangoORM/urls.py.j2",
                "models": "django-rest/djangoORM/models.py.j2",
                "serializers": "django-rest/djangoORM/serializers.py.j2",
                "views": "django-rest/djangoORM/views.py.j2",
                "permissions": "django-rest/djangoORM/permissions.py.j2",
            },
        },
    }

    # Common templates used by all projects
    COMMON_TEMPLATES = {
        "gitignore": "common/.gitignore.j2",
        "env_example": "common/env.example.j2",
        "readme": "common/README.md.j2",
        "license": "common/LICENSE.j2",
        "dockerfile": "common/Dockerfile.j2",
        "docker_compose": "common/docker-compose.yml.j2",
        "dockerignore": "common/.dockerignore.j2",
        # 'app' intentionally omitted: framework-specific 'app' templates live under each framework
        "security": "common/security.py.j2",
        "pytest_ini": "common/pytest.ini.j2",
        "pyproject_toml": "common/pyproject.toml.j2",
        "License": "common/LICENSE.j2",
    }

    # Test templates
    TEST_TEMPLATES = {
        "Flask-Restx": {
            "SQLAlchemy": {
                "pytest_ini": "flask_restx/sqlalchemy/pytest.ini.j2",
                "conftest": "flask_restx/sqlalchemy/conftest.py.j2",
                "test_api": "flask_restx/sqlalchemy/test_api.py.j2",
                "test_models": "flask_restx/sqlalchemy/test_models.py.j2",
                "test_security": "common/test_security.py.j2",
                ".env_test": "flask_restx/sqlalchemy/.env.test.example.j2",
            },
            "Peewee": {
                "pytest_ini": "flask_restx/peewee/pytest.ini.j2",
                "conftest": "flask_restx/peewee/conftest.py.j2",
                "test_api": "flask_restx/peewee/test_api.py.j2",
                "test_models": "flask_restx/peewee/test_models.py.j2",
                "test_security": "common/test_security.py.j2",
                ".env_test": "flask_restx/peewee/.env.test.example.j2",
            },
        },
        "FastAPI": {
            "SQLAlchemy": {
                "pytest_ini": "fastapi/sqlalchemy/pytest.ini.j2",
                "conftest": "fastapi/sqlalchemy/conftest.py.j2",
                "test_api": "fastapi/sqlalchemy/test_api.py.j2",
                "test_models": "fastapi/sqlalchemy/test_models.py.j2",
                "test_security": "common/test_security.py.j2",
                ".env_test": "fastapi/sqlalchemy/.env.test.example.j2",
            },
            "TortoiseORM": {
                "pytest_ini": "fastapi/tortoise/pytest.ini.j2",
                "conftest": "fastapi/tortoise/conftest.py.j2",
                "test_api": "fastapi/tortoise/test_api.py.j2",
                "test_models": "fastapi/tortoise/test_models.py.j2",
                "test_security": "common/test_security.py.j2",
                ".env_test": "fastapi/tortoise/.env.test.example.j2",
            },
        },
        "Django-Rest": {
            "DjangoORM": {
                "pytest_ini": "django-rest/djangoORM/pytest.ini.j2",
                "conftest": "django-rest/djangoORM/conftest.py.j2",
                "test_api": "django-rest/djangoORM/test_api.py.j2",
                "test_models": "django-rest/djangoORM/test_models.py.j2",
                "test_security": "common/test_security.py.j2",
                ".env_test": "django-rest/djangoORM/.env.test.example.j2",
            },
        },
    }

    @classmethod
    def get_templates_for_config(
        cls, framework: str, orm: str, auth_enabled: bool, testing_suite: bool
    ) -> dict[str, str]:
        """
        Get all template paths needed for a configuration

        Args:
            framework: Framework name
            orm: ORM name
            auth_enabled: Whether authentication is enabled
            testing_suite: Whether to include tests

        Returns:
            Dictionary mapping template names to their paths
        """
        templates = {}

        # Start with common templates, then overlay framework-specific templates
        templates.update(cls.COMMON_TEMPLATES)

        framework_templates = cls.TEMPLATES.get(framework, {}).get(orm, {})
        templates.update(framework_templates)

        # Test templates
        if testing_suite:
            test_templates = cls.TEST_TEMPLATES.get(framework, {}).get(orm, {})
            templates.update(test_templates)

        return templates

    @classmethod
    def get_required_templates(cls, framework: str, orm: str) -> list[str]:
        """
        Get list of required template files that must exist

        Returns:
            List of template paths
        """
        templates = cls.get_templates_for_config(framework, orm, True, True)
        return list(templates.values())

    @classmethod
    def validate_templates_exist(
        cls, renderer: TemplateRenderer, framework: str, orm: str
    ) -> tuple[bool, list[str]]:
        """
        Validate that all required templates exist

        Returns:
            (all_exist, list_of_missing_templates)
        """
        required = cls.get_required_templates(framework, orm)
        missing = []

        for template_path in required:
            if not renderer.template_exists(template_path):
                missing.append(template_path)

        return len(missing) == 0, missing


# Convenience function for quick rendering
def quick_render(template_path: str, context: dict[str, Any]) -> str:
    """
    Quick render function for one-off template rendering

    Args:
        template_path: Path to template
        context: Template context

    Returns:
        Rendered content
    """
    renderer = TemplateRenderer()
    return renderer.render(template_path, context)
