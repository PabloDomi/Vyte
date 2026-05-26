"""
Dependency management system - Declarative and maintainable
"""

from pathlib import Path

from ..__version__ import __version__
from .config import ProjectConfig


class DependencyManager:
    """
    Manages project dependencies in a declarative way
    All dependencies are defined in class constants for easy maintenance
    """

    # Base dependencies for all projects
    BASE_DEPS = [
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
    ]

    # Testing dependencies
    TESTING_DEPS = [
        "pytest>=7.4.0",
        "pytest-cov>=4.1.0",
        "pytest-asyncio>=0.21.0",  # For async tests
        "pytest-django>=4.5.2",
    ]

    # Framework-specific dependencies
    FRAMEWORK_DEPS: dict[str, dict[str, list[str]]] = {
        "Flask-Restx": {
            "base": [
                "Flask>=3.0.0",
                "flask-restx>=1.3.0",
                "flask-cors>=4.0.0",
            ],
            "auth": [
                "flask-jwt-extended>=4.5.0",
                "passlib[bcrypt]==1.7.4",
                "bcrypt==4.0.1",
            ],
            "production": [
                "gunicorn>=21.2.0",
                "gevent>=23.9.1",
            ],
        },
        "FastAPI": {
            "base": [
                "fastapi>=0.109.0",
                "uvicorn[standard]>=0.27.0",
                "python-multipart>=0.0.6",  # For form data
                "email-validator>=2.1.0",
            ],
            "auth": [
                "python-jose[cryptography]>=3.3.0",
                "passlib[bcrypt]==1.7.4",
                "bcrypt==4.0.1",
                "python-multipart>=0.0.6",
            ],
            "production": [
                "gunicorn>=21.2.0",
            ],
        },
        "Django-Rest": {
            "base": [
                "Django>=5.0.0",
                "djangorestframework>=3.14.0",
                "django-cors-headers>=4.3.0",
                "django-filter>=23.5",
                "drf-spectacular>=0.27.0",
            ],
            "auth": [
                "djangorestframework-simplejwt>=5.3.0",
            ],
            "production": [
                "gunicorn>=21.2.0",
                "whitenoise>=6.6.0",  # Static files
            ],
        },
    }

    # ORM-specific dependencies
    ORM_DEPS: dict[str, dict[str, list[str]]] = {
        "SQLAlchemy": {
            "base": [
                "sqlalchemy>=2.0.0",
            ],
            "Flask-Restx": [
                "flask-sqlalchemy>=3.1.0",
                "Flask-Migrate>=4.0.0",
            ],
            "FastAPI": [
                "sqlalchemy[asyncio]>=2.0.0",
                "alembic>=1.13.0",
            ],
            "drivers": {
                "PostgreSQL": ["asyncpg>=0.29.0"],
                "MySQL": ["aiomysql>=0.2.0"],
                "SQLite": ["aiosqlite>=0.19.0"],
            },
        },
        "TortoiseORM": {
            "base": [
                "tortoise-orm>=0.20.0",
                "aerich>=0.7.2",  # Migrations tool
                "tomlkit>=0.11.6",
            ],
            "drivers": {
                "PostgreSQL": ["asyncpg>=0.29.0"],
                "MySQL": ["aiomysql>=0.2.0"],
                "SQLite": ["aiosqlite>=0.19.0"],
            },
        },
        "Peewee": {
            "base": [
                "peewee>=3.17.0",
            ],
            "Flask-Restx": [
                "peewee-migrate>=1.12.0",
            ],
        },
        "DjangoORM": {
            "base": [],  # Included in Django
        },
    }

    # Database driver dependencies
    DB_DRIVERS: dict[str, dict[str, list[str]]] = {
        "PostgreSQL": {
            "sync": ["psycopg2-binary>=2.9.9"],
            "async": ["asyncpg>=0.29.0"],
        },
        "MySQL": {
            "sync": ["mysqlclient>=2.2.0"],
            "async": ["aiomysql>=0.2.0"],
        },
        "SQLite": {
            "sync": [],  # Built-in
            "async": ["aiosqlite>=0.19.0"],
        },
    }

    # Optional but recommended dependencies
    RECOMMENDED_DEPS = [
        "rich>=13.7.0",  # Better console output
        "httpx>=0.26.0",  # Better HTTP client
    ]

    @classmethod
    def get_all_dependencies(cls, config: ProjectConfig) -> list[str]:
        """
        Get complete list of dependencies for a project configuration

        Args:
            config: ProjectConfig instance

        Returns:
            Sorted list of dependency strings
        """
        deps: set[str] = set()

        # Base dependencies
        deps.update(cls.BASE_DEPS)

        # Testing dependencies
        if config.testing_suite:
            deps.update(cls.TESTING_DEPS)

        # Framework dependencies
        framework_deps = cls.FRAMEWORK_DEPS.get(config.framework, {})
        deps.update(framework_deps.get("base", []))

        if config.auth_enabled:
            deps.update(framework_deps.get("auth", []))

        # Always include production server
        deps.update(framework_deps.get("production", []))

        # ORM dependencies
        orm_deps = cls.ORM_DEPS.get(config.orm, {})
        deps.update(orm_deps.get("base", []))
        deps.update(orm_deps.get(config.framework, []))

        # Database drivers
        db_mode = "async" if config.is_async_framework() else "sync"
        db_drivers = cls.DB_DRIVERS.get(config.database, {})
        deps.update(db_drivers.get(db_mode, []))

        # Recommended dependencies
        deps.update(cls.RECOMMENDED_DEPS)

        # Convert to sorted list
        return sorted(deps)

    @classmethod
    def get_dev_dependencies(cls) -> list[str]:
        """Get development dependencies"""
        return sorted(
            [
                "black>=23.12.0",
                "ruff>=0.1.0",
                "mypy>=1.7.0",
                "pre-commit>=3.6.0",
            ]
        )

    @classmethod
    def write_requirements_txt(cls, config: ProjectConfig, output_dir: Path):
        """
        Write requirements.txt file

        Args:
            config: ProjectConfig instance
            output_dir: Directory to write requirements.txt
        """
        requirements_path = output_dir / "requirements.txt"

        deps = cls.get_all_dependencies(config)

        content = [
            f"# Requirements generated by vyte {__version__}",
            f"# Project: {config.name}",
            f"# Framework: {config.framework}",
            f"# ORM: {config.orm}",
            f"# Database: {config.database}",
            "",
            "# Base dependencies",
        ]

        # Group dependencies by category
        base_deps = [
            d for d in deps if any(d.startswith(base.split(">=")[0]) for base in cls.BASE_DEPS)
        ]

        framework_name = config.framework.lower().replace("-", "")
        framework_deps = [d for d in deps if framework_name in d.lower()]

        orm_name = config.orm.lower()
        orm_deps = [
            d
            for d in deps
            if orm_name in d.lower() or "alembic" in d.lower() or "migrate" in d.lower()
        ]

        testing_deps = [d for d in deps if "pytest" in d.lower() or "cov" in d.lower()]

        other_deps = [
            d for d in deps if d not in base_deps + framework_deps + orm_deps + testing_deps
        ]

        # Write grouped dependencies
        content.extend(base_deps)

        if framework_deps:
            content.extend(["", f"# {config.framework} framework"])
            content.extend(framework_deps)

        if orm_deps:
            content.extend(["", f"# {config.orm} ORM"])
            content.extend(orm_deps)

        if testing_deps and config.testing_suite:
            content.extend(["", "# Testing"])
            content.extend(testing_deps)

        if other_deps:
            content.extend(["", "# Other dependencies"])
            content.extend(other_deps)

        content.append("")  # Empty line at end

        requirements_path.write_text("\n".join(content), encoding="utf-8")

    @classmethod
    def write_requirements_dev_txt(cls, output_dir: Path):
        """Write requirements-dev.txt for development dependencies"""
        requirements_dev_path = output_dir / "requirements-dev.txt"

        dev_deps = cls.get_dev_dependencies()

        content = [
            "# Development requirements",
            "# Install with: pip install -r requirements-dev.txt",
            "",
            "-r requirements.txt  # Include production requirements",
            "",
        ]
        content.extend(dev_deps)
        content.append("")

        requirements_dev_path.write_text("\n".join(content), encoding="utf-8")

    @classmethod
    def get_dependency_info(cls, config: ProjectConfig) -> dict[str, int]:
        """
        Get statistics about dependencies

        Returns:
            Dictionary with counts of different dependency types
        """
        all_deps = cls.get_all_dependencies(config)

        return {
            "total": len(all_deps),
            "base": len(cls.BASE_DEPS),
            "framework": len(cls.FRAMEWORK_DEPS.get(config.framework, {}).get("base", [])),
            "orm": len(cls.ORM_DEPS.get(config.orm, {}).get("base", [])),
            "testing": len(cls.TESTING_DEPS) if config.testing_suite else 0,
            "auth": (
                len(cls.FRAMEWORK_DEPS.get(config.framework, {}).get("auth", []))
                if config.auth_enabled
                else 0
            ),
        }

    @classmethod
    def check_dependency_conflicts(cls, deps: list[str]) -> list[str]:
        """
        Check for potential dependency conflicts

        Args:
            deps: List of dependency strings

        Returns:
            List of potential conflicts/warnings
        """
        warnings = []

        # Extract package names (without versions)
        packages = [dep.split(">=")[0].split("==")[0].lower() for dep in deps]

        # Check for potential conflicts
        if "sqlalchemy" in packages and "tortoise-orm" in packages:
            warnings.append(
                "Warning: Using both SQLAlchemy and TortoiseORM. " "Consider using only one ORM."
            )

        if "django" in packages and any(p in packages for p in ["flask", "fastapi"]):
            warnings.append(
                "Warning: Mixing Django with other frameworks. "
                "This is unusual and may cause conflicts."
            )

        return warnings
