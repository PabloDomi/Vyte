"""
Declarative project specs.

Each `FrameworkSpec` describes what to generate for a (framework, ORM) combo:
which directories to create, which templates to render where, and any
post-generation step (e.g. Alembic for SQLAlchemy).

Adding a new framework/ORM means adding one entry to FRAMEWORK_REGISTRY —
no new classes, no new methods.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from ..core.config import ProjectConfig

# Predicates -----------------------------------------------------------------

_always: Callable[[ProjectConfig], bool] = lambda _c: True
_if_auth: Callable[[ProjectConfig], bool] = lambda c: c.auth_enabled
_if_tests: Callable[[ProjectConfig], bool] = lambda c: c.testing_suite


# Specs ----------------------------------------------------------------------


@dataclass(frozen=True)
class FileSpec:
    """A template to render at a target path.

    `output` may contain Python str.format placeholders that are resolved
    against the project context (commonly `{app_name}`).
    """

    template: str
    output: str
    when: Callable[[ProjectConfig], bool] = field(default=_always, repr=False, compare=False)
    executable: bool = False


@dataclass(frozen=True)
class FrameworkSpec:
    """Everything needed to generate one (framework, ORM) combination."""

    framework: str
    orm: str
    dirs: tuple[str, ...] = ()
    init_dirs: tuple[str, ...] = ()
    files: tuple[FileSpec, ...] = ()
    test_files: tuple[FileSpec, ...] = ()
    post_generate: Optional[Callable[[Path, ProjectConfig], None]] = field(
        default=None, repr=False, compare=False
    )


# Common files (rendered for every framework) --------------------------------

COMMON_FILES: tuple[FileSpec, ...] = (
    FileSpec("common/.gitignore.j2", ".gitignore"),
    FileSpec("common/env.example.j2", ".env.example"),
    FileSpec("common/README.md.j2", "README.md"),
    FileSpec("common/LICENSE.j2", "LICENSE"),
    FileSpec("common/pyproject.toml.j2", "pyproject.toml"),
    FileSpec("common/pytest.ini.j2", "pytest.ini", when=_if_tests),
)

DOCKER_FILES: tuple[FileSpec, ...] = (
    FileSpec("common/Dockerfile.j2", "Dockerfile"),
    FileSpec("common/docker-compose.yml.j2", "docker-compose.yml"),
    FileSpec("common/.dockerignore.j2", ".dockerignore"),
)


# Common test files (the shared security test, used by all frameworks) -------

_TEST_SECURITY = FileSpec("common/test_security.py.j2", "tests/test_security.py", when=_if_auth)


# Post-generate hooks --------------------------------------------------------


def _alembic_for_src(project_path: Path, _config: ProjectConfig) -> None:
    """Create the Alembic structure for projects rooted at src/."""
    from ..core.alembic_setup import setup_alembic

    setup_alembic(project_path, module_name="src")


# Per-(framework, ORM) specs -------------------------------------------------

FLASK_RESTX_SQLALCHEMY = FrameworkSpec(
    framework="Flask-Restx",
    orm="SQLAlchemy",
    dirs=("src", "src/models", "src/routes", "src/services", "src/config",
          "src/utils", "src/controllers", "migrations"),
    init_dirs=("src", "src/models", "src/routes", "src/services", "src/config",
               "src/utils", "src/controllers"),
    files=(
        FileSpec("flask_restx/sqlalchemy/__init__.py.j2", "src/__init__.py"),
        FileSpec("flask_restx/sqlalchemy/extensions.py.j2", "src/extensions.py"),
        FileSpec("flask_restx/sqlalchemy/config.py.j2", "src/config/config.py"),
        FileSpec("flask_restx/sqlalchemy/models.py.j2", "src/models/models.py"),
        FileSpec("flask_restx/sqlalchemy/routes.py.j2", "src/routes/routes_example.py"),
        FileSpec("flask_restx/sqlalchemy/app.py.j2", "app.py"),
        FileSpec("common/security.py.j2", "src/security.py", when=_if_auth),
    ),
    test_files=(
        FileSpec("flask_restx/sqlalchemy/pytest.ini.j2", "tests/pytest.ini"),
        FileSpec("flask_restx/sqlalchemy/conftest.py.j2", "tests/conftest.py"),
        FileSpec("flask_restx/sqlalchemy/test_api.py.j2", "tests/test_api.py"),
        FileSpec("flask_restx/sqlalchemy/test_models.py.j2", "tests/test_models.py"),
        FileSpec("flask_restx/sqlalchemy/.env.test.example.j2", "tests/.env.test.example"),
        _TEST_SECURITY,
    ),
)

FLASK_RESTX_PEEWEE = FrameworkSpec(
    framework="Flask-Restx",
    orm="Peewee",
    dirs=("src", "src/models", "src/routes", "src/services", "src/config",
          "src/utils", "src/controllers", "migrations"),
    init_dirs=("src", "src/models", "src/routes", "src/services", "src/config",
               "src/utils", "src/controllers"),
    files=(
        FileSpec("flask_restx/peewee/__init__.py.j2", "src/__init__.py"),
        FileSpec("flask_restx/peewee/extensions.py.j2", "src/extensions.py"),
        FileSpec("flask_restx/peewee/config.py.j2", "src/config/config.py"),
        FileSpec("flask_restx/peewee/models.py.j2", "src/models/models.py"),
        FileSpec("flask_restx/peewee/routes.py.j2", "src/routes/routes_example.py"),
        FileSpec("flask_restx/peewee/app.py.j2", "app.py"),
        FileSpec("common/security.py.j2", "src/security.py", when=_if_auth),
    ),
    test_files=(
        FileSpec("flask_restx/peewee/pytest.ini.j2", "tests/pytest.ini"),
        FileSpec("flask_restx/peewee/conftest.py.j2", "tests/conftest.py"),
        FileSpec("flask_restx/peewee/test_api.py.j2", "tests/test_api.py"),
        FileSpec("flask_restx/peewee/test_models.py.j2", "tests/test_models.py"),
        FileSpec("flask_restx/peewee/.env.test.example.j2", "tests/.env.test.example"),
        _TEST_SECURITY,
    ),
)

FASTAPI_SQLALCHEMY = FrameworkSpec(
    framework="FastAPI",
    orm="SQLAlchemy",
    dirs=("src", "src/models", "src/routes", "src/services", "src/config",
          "src/utils", "src/api", "src/schemas", "src/crud"),
    init_dirs=("src", "src/models", "src/routes", "src/services", "src/config",
               "src/utils", "src/api", "src/schemas", "src/crud"),
    files=(
        FileSpec("fastapi/sqlalchemy/main.py.j2", "src/main.py"),
        FileSpec("fastapi/sqlalchemy/database.py.j2", "src/database.py"),
        FileSpec("fastapi/sqlalchemy/config.py.j2", "src/config/config.py"),
        FileSpec("fastapi/sqlalchemy/models.py.j2", "src/models/models.py"),
        FileSpec("fastapi/sqlalchemy/routes.py.j2", "src/api/routes.py"),
        FileSpec("fastapi/sqlalchemy/schemas.py.j2", "src/schemas/schemas.py"),
        FileSpec("common/security.py.j2", "src/security.py", when=_if_auth),
    ),
    test_files=(
        FileSpec("fastapi/sqlalchemy/pytest.ini.j2", "tests/pytest.ini"),
        FileSpec("fastapi/sqlalchemy/conftest.py.j2", "tests/conftest.py"),
        FileSpec("fastapi/sqlalchemy/test_api.py.j2", "tests/test_api.py"),
        FileSpec("fastapi/sqlalchemy/test_models.py.j2", "tests/test_models.py"),
        FileSpec("fastapi/sqlalchemy/.env.test.example.j2", "tests/.env.test.example"),
        _TEST_SECURITY,
    ),
    post_generate=_alembic_for_src,
)

FASTAPI_TORTOISE = FrameworkSpec(
    framework="FastAPI",
    orm="TortoiseORM",
    dirs=("src", "src/models", "src/routes", "src/services", "src/config",
          "src/utils", "src/api", "src/schemas", "src/crud"),
    init_dirs=("src", "src/models", "src/routes", "src/services", "src/config",
               "src/utils", "src/api", "src/schemas", "src/crud"),
    files=(
        FileSpec("fastapi/tortoise/main.py.j2", "src/main.py"),
        FileSpec("fastapi/tortoise/database.py.j2", "src/database.py"),
        FileSpec("fastapi/tortoise/config.py.j2", "src/config/config.py"),
        FileSpec("fastapi/tortoise/models.py.j2", "src/models/models.py"),
        FileSpec("fastapi/tortoise/routes.py.j2", "src/api/routes.py"),
        FileSpec("fastapi/tortoise/schemas.py.j2", "src/schemas/schemas.py"),
        FileSpec("common/security.py.j2", "src/security.py", when=_if_auth),
    ),
    test_files=(
        FileSpec("fastapi/tortoise/pytest.ini.j2", "tests/pytest.ini"),
        FileSpec("fastapi/tortoise/conftest.py.j2", "tests/conftest.py"),
        FileSpec("fastapi/tortoise/test_api.py.j2", "tests/test_api.py"),
        FileSpec("fastapi/tortoise/test_models.py.j2", "tests/test_models.py"),
        FileSpec("fastapi/tortoise/.env.test.example.j2", "tests/.env.test.example"),
        _TEST_SECURITY,
    ),
)

DJANGO_REST_DJANGOORM = FrameworkSpec(
    framework="Django-Rest",
    orm="DjangoORM",
    dirs=("{app_name}", "{app_name}/migrations",
          "{app_name}/management", "{app_name}/management/commands"),
    init_dirs=("{app_name}", "{app_name}/migrations",
               "{app_name}/management", "{app_name}/management/commands"),
    files=(
        FileSpec("django-rest/djangoORM/settings.py.j2", "{app_name}/settings.py"),
        FileSpec("django-rest/djangoORM/urls.py.j2", "{app_name}/urls.py"),
        FileSpec("django-rest/djangoORM/models.py.j2", "{app_name}/models.py"),
        FileSpec("django-rest/djangoORM/serializers.py.j2", "{app_name}/serializers.py"),
        FileSpec("django-rest/djangoORM/views.py.j2", "{app_name}/views.py"),
        FileSpec("django-rest/djangoORM/apps.py.j2", "{app_name}/apps.py"),
        FileSpec("django-rest/djangoORM/wsgi.py.j2", "{app_name}/wsgi.py"),
        FileSpec("django-rest/djangoORM/asgi.py.j2", "{app_name}/asgi.py"),
        FileSpec("django-rest/djangoORM/manage.py.j2", "manage.py", executable=True),
        FileSpec("django-rest/djangoORM/permissions.py.j2", "{app_name}/permissions.py",
                 when=_if_auth),
        FileSpec("common/security.py.j2", "{app_name}/security.py", when=_if_auth),
    ),
    test_files=(
        FileSpec("django-rest/djangoORM/pytest.ini.j2", "pytest.ini"),
        FileSpec("django-rest/djangoORM/conftest.py.j2", "tests/conftest.py"),
        FileSpec("django-rest/djangoORM/test_api.py.j2", "tests/test_api.py"),
        FileSpec("django-rest/djangoORM/test_models.py.j2", "tests/test_models.py"),
        FileSpec("django-rest/djangoORM/.env.test.example.j2", "tests/.env.test.example"),
        _TEST_SECURITY,
    ),
)


# Registry -------------------------------------------------------------------

FRAMEWORK_REGISTRY: dict[tuple[str, str], FrameworkSpec] = {
    ("Flask-Restx", "SQLAlchemy"): FLASK_RESTX_SQLALCHEMY,
    ("Flask-Restx", "Peewee"): FLASK_RESTX_PEEWEE,
    ("FastAPI", "SQLAlchemy"): FASTAPI_SQLALCHEMY,
    ("FastAPI", "TortoiseORM"): FASTAPI_TORTOISE,
    ("Django-Rest", "DjangoORM"): DJANGO_REST_DJANGOORM,
}


def get_spec(config: ProjectConfig) -> FrameworkSpec:
    """Look up the spec for a project config."""
    key = (config.framework, config.orm)
    spec = FRAMEWORK_REGISTRY.get(key)
    if spec is None:
        raise KeyError(
            f"No spec for combination {key}. "
            f"Available: {sorted(FRAMEWORK_REGISTRY.keys())}"
        )
    return spec


def all_template_paths(config: ProjectConfig) -> list[str]:
    """Return every template path that *might* be rendered for this config.

    Used by validation to check templates exist before generation starts.
    """
    spec = get_spec(config)
    paths = [f.template for f in COMMON_FILES if f.when(config)]
    if config.docker_support:
        paths.extend(f.template for f in DOCKER_FILES)
    paths.extend(f.template for f in spec.files if f.when(config))
    if config.testing_suite:
        paths.extend(f.template for f in spec.test_files if f.when(config))
    return paths
