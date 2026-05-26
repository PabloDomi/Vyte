# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.6] - 2026-05-26

### Security

- **Fix critical vulnerability**: the `JWT_SECRET_KEY` was hardcoded as the literal
  string `"SECRET_KEY"` inside the FastAPI security template. Any generated API
  using authentication was signing/verifying tokens with a publicly known key.
  Now reads `JWT_SECRET_KEY` and `JWT_ALGORITHM` from the environment, matching
  the pattern already used by `routes.py`.

### Fixed

- `security.py` was being rendered twice for Flask and FastAPI projects (once by
  the generator, once by each strategy).
- Flask projects generated `src/security.py` even with `--no-auth`.
- Django projects with `--auth` never received `security.py` nor `test_security.py`.
- `tests/test_security.py` was generated even with `--no-auth`, importing from a
  non-existent module and breaking the test suite of generated projects.
- `tests/test_security.py` import path is now framework-aware (`src/` for Flask
  and FastAPI, `{app_name}/` for Django).
- `TEST_TEMPLATES` entries falsely pointed several combos at
  `flask_restx/sqlalchemy/pytest.ini.j2` and `flask_restx/sqlalchemy/.env.test.example.j2`.
  Most notably, **FastAPI + TortoiseORM never received `asyncio_mode = auto`**,
  silently breaking its async tests.
- Django projects never wrote `tests/.env.test.example` even though the entry
  was declared in `TEST_TEMPLATES`.
- `validate_orm` accepted combinations declared incompatible in
  `COMPATIBILITY_MATRIX` (`Flask + DjangoORM`, `FastAPI + DjangoORM`, etc.).
  The validator now delegates to the matrix (single source of truth).
- Generated FastAPI `main.py` wrapped CORS middleware and Swagger / ReDoc /
  OpenAPI URLs inside `{% if auth_enabled %}`, making them disappear in projects
  without authentication. They are now always present.
- `get_python_version()` always returned `"3.11"` regardless of the active
  runtime. Now returns the actual `sys.version_info` (e.g. `"3.12"`), so
  generated `Dockerfile`, `pyproject.toml`, and Black/Ruff `target-version`
  reflect reality.
- Alembic's generated `env.py` contained a literal `{project_name}` placeholder
  that was never interpolated.
- `_init_git` never raised `GitError`, making the `except GitError` branch in
  `cli/commands.py:create` unreachable. The dead branch and import were removed.
- `vyte/strategies/__init.py` (typo — missing underscore) renamed to
  `__init__.py`. The previously dead `__all__` is now applied.

### Changed

- **Project structure: Strategy pattern replaced with a declarative registry.**
  `BaseStrategy`, `FlaskRestxStrategy`, `FastAPIStrategy`, `DjangoRestStrategy`
  were eliminated in favor of `FrameworkSpec` / `FileSpec` dataclasses in
  `vyte/strategies/registry.py`. Net result: ~941 LOC → ~481 LOC for the
  generator subsystem, and adding a new (framework, ORM) combination now means
  appending one entry to `FRAMEWORK_REGISTRY` instead of subclassing.
- `ProjectConfig`'s `validate_name` no longer checks `Path.exists()`. Filesystem
  checks belong to the generator; validators are now pure, serializable, and
  deterministic.
- `model_dump_safe()` now also exposes `vyte_version` (so generated headers
  reflect the actual installed version) and `app_name` (snake_case form of
  the project name, used as the Django app module).
- Alembic setup is fully template-driven. The `subprocess.run(["alembic", "init", ...])`
  path was removed: vyte no longer depends on Alembic being installed on the
  generating machine, and the previous `os.chdir()` (process-global, not
  thread-safe) is gone.
- Branding cleanup across 17 files: misspellings (`presto`, `vytesto`,
  `vytestosto`, `vytestostostostosto`) were unified to `vyte`. Hardcoded
  `vyte v2.0` headers in 46 templates are now `vyte {{ vyte_version }}`.
- Trailing garbage at the end of `Makefile` (5 duplicated echo lines and a
  stray `"""` from a stale copy-paste) removed.

### Added

- `vyte/strategies/registry.py`: `FileSpec` and `FrameworkSpec` dataclasses
  and a `FRAMEWORK_REGISTRY` mapping each `(framework, ORM)` to its spec
  (directories, files, optional post-generate hook).
- Four new Django templates extracted from inline strings:
  `apps.py.j2`, `wsgi.py.j2`, `asgi.py.j2`, `manage.py.j2`.
- Django projects with `--auth` now correctly render `{app_name}/security.py`
  and `tests/test_security.py`.
- `tests/.env.test.example` now generated for Django projects.

### Removed

- `vyte/strategies/base.py`, `flask_restx.py`, `fastapi.py`, `django_rest.py`
  (folded into the declarative registry; were not part of the public API).
- `AlembicConfigurator` class and its `subprocess.run(["alembic", "init"])`
  path — replaced by module-level `setup_alembic(project_path, module_name)`.
- Unreachable `except GitError` branch in CLI.

## [2.0.5] - 2025-11-17

### Added

- **Comprehensive MkDocs documentation website** with Material theme
  - 7 complete documentation pages: index, quickstart, cli, frameworks, databases, configuration, api-reference
  - Professional Material theme with custom colors (cyan/deep purple)
  - Integrated Vyte logos in header and favicon
  - Search functionality
  - Git revision date plugin for last modified timestamps
  - mkdocstrings for automatic API documentation
  - Full navigation structure with 6 main sections
- **GitHub Actions workflow for automatic documentation deployment**
  - Automatic deployment to GitHub Pages on push to main
  - Triggered by changes in docs/, mkdocs.yml, or source code
  - Python dependency caching for faster builds
- **Documentation dependencies** in pyproject.toml
  - mkdocs >= 1.5.0
  - mkdocs-material >= 9.5.0
  - mkdocstrings\[python\] >= 0.24.0
  - mkdocs-git-revision-date-localized-plugin >= 1.2.0
- **Branding assets**
  - 5 logo variants in docs/images/ folder
  - BRANDING.md guide for logo usage
  - Documentation badge in README.md

### Fixed

- Logo visibility in documentation header (changed to B&W version for better contrast)
- Broken links in documentation files (README.md, docs/ paths)
- Logo path in index.md (corrected to relative images/ path)
- MkDocs build warnings and strict mode errors

### Changed

- Added documentation link badge to README.md
- Copied SECURITY.md to docs/ folder for MkDocs access
- Added site/ folder to .gitignore
- Updated mkdocs.yml to use B&W logo for better header contrast

### Documentation

- **Quick Start Guide**: Complete installation and first project tutorial
- **CLI Reference**: Full command documentation with examples and tips
- **Frameworks Guide**: Detailed comparison of FastAPI, Flask-Restx, Django-Rest
- **Databases Guide**: Comprehensive ORM and database documentation
- **Configuration Guide**: Environment variables and settings reference
- **API Reference**: Complete Python API documentation
- **Home Page**: Feature overview, philosophy, and use cases

## [2.0.4] - 2025-11-13

### Added

- Custom exception hierarchy with 8 specific exception types (VyteError, ConfigurationError, GenerationError, TemplateError, DependencyError, ValidationError, FileSystemError, GitError)
- Comprehensive test suite for exceptions with 100% coverage
- 26 new unit tests for display functions and interactive mode
- Pre-commit hooks configuration with black, ruff, isort, bandit, and mypy
- EditorConfig file for consistent coding styles
- Pylint configuration file
- GitHub Actions workflow for automated testing and linting
- CHANGELOG.md, CONTRIBUTING.md, SECURITY.md, CONTRIBUTORS.md, DEVELOPMENT.md, and ROADMAP.md documentation
- Codecov configuration for code coverage tracking
- .gitattributes for consistent line endings
- Improved Makefile with 20+ development commands

### Fixed

- Synchronized version numbers across all files (2.0.4)
- Fixed CLI help command displaying correct name 'vyte' instead of 'cli'
- Improved version management using single source of truth in `__version__.py`
- Better error handling with specific exception types instead of generic Exception
- PackageLoader exception handling in renderer module

### Changed

- Version now imported dynamically from `__version__.py` across all modules
- Converted pyproject.toml to use setuptools with dynamic version attribute
- Improved code consistency and formatting (31 files reformatted with black)
- Enhanced error messages with custom exception types
- Updated README.md with badges and comprehensive project information
- Reorganized documentation files into dedicated docs/ folder
- Moved SECURITY.md to root for GitHub security tab integration

### Improved

- Test coverage increased from 72% to 73% (65 tests total: 63 passed, 2 skipped)
- Code quality with automated linting and formatting tools
- Developer experience with pre-commit hooks and improved documentation
- Project structure and organization for better maintainability

## [2.0.3] - 2025-11-XX

### Added

- Multiple framework support (Flask-Restx, FastAPI, Django-Rest)
- Multiple ORM support (SQLAlchemy, TortoiseORM, Peewee, Django ORM)
- Interactive CLI with beautiful Rich UI
- JWT authentication support
- Docker and docker-compose generation
- Complete testing suite with pytest
- Auto-generated API documentation
- Git repository initialization

### Changed

- Migrated to Pydantic v2
- Updated to Python 3.11+ requirement
- Improved project structure and organization

## [2.0.0] - 2025-10-XX

### Added

- Initial release of Vyte 2.0
- Complete rewrite with modern Python practices
- Support for async frameworks
- Comprehensive compatibility matrix
- Template-based generation system

## \[1.x.x\] - Legacy

Previous versions (deprecated)

______________________________________________________________________

## Version Comparison

### \[Unreleased\]

- Features and fixes in development

### Categories

- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security fixes

[2.0.0]: https://github.com/PabloDomi/Vyte/releases/tag/v2.0.0
[2.0.3]: https://github.com/PabloDomi/Vyte/compare/v2.0.0...v2.0.3
[2.0.4]: https://github.com/PabloDomi/Vyte/compare/v2.0.3...v2.0.4
[2.0.5]: https://github.com/PabloDomi/Vyte/compare/v2.0.4...v2.0.5
