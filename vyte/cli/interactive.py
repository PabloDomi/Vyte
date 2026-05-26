# vyte/cli/interactive.py
"""
Interactive setup for project configuration
"""

from InquirerPy import inquirer
from InquirerPy.validator import EmptyInputValidator

from ..core.config import COMPATIBILITY_MATRIX, ProjectConfig


def interactive_setup() -> ProjectConfig:
    """
    Interactive project setup

    Returns:
        Validated ProjectConfig
    """
    # Project name
    name = inquirer.text(
        message="📝 Project name:",
        validate=EmptyInputValidator("Project name cannot be empty"),
        filter=lambda x: x.lower().strip(),
    ).execute()

    # Framework selection
    framework = inquirer.select(
        message="🎯 Select a framework:",
        choices=[
            {"name": "⚡ FastAPI - Modern, fast (async), automatic docs", "value": "FastAPI"},
            {"name": "🌶️  Flask-Restx - Mature, flexible, Swagger UI", "value": "Flask-Restx"},
            {
                "name": "🎸 Django-Rest - Full-featured, admin panel included",
                "value": "Django-Rest",
            },
        ],
        default="FastAPI",
    ).execute()

    # Show framework info
    info = COMPATIBILITY_MATRIX[framework]
    compatible_orms = info["compatible_orms"]

    # ORM selection (based on framework compatibility)
    if framework == "Django-Rest":
        orm = "DjangoORM"
    else:
        orm_choices = []

        if "SQLAlchemy" in compatible_orms:
            orm_choices.append(
                {
                    "name": "🗄️  SQLAlchemy - Most popular, mature, well-documented",
                    "value": "SQLAlchemy",
                }
            )

        if "TortoiseORM" in compatible_orms:
            orm_choices.append(
                {"name": "🐢 TortoiseORM - Async ORM, Django-like API", "value": "TortoiseORM"}
            )

        if "Peewee" in compatible_orms:
            orm_choices.append(
                {"name": "🪶 Peewee - Lightweight, simple, easy to learn", "value": "Peewee"}
            )

        orm = inquirer.select(
            message="💾 Select an ORM:", choices=orm_choices, default="SQLAlchemy"
        ).execute()

    # Database selection
    database = inquirer.select(
        message="🗃️  Select database:",
        choices=[
            {
                "name": "🐘 PostgreSQL - Production-ready, powerful, recommended",
                "value": "PostgreSQL",
            },
            {"name": "🐬 MySQL - Popular, reliable, widely supported", "value": "MySQL"},
            {"name": "💾 SQLite - Lightweight, zero-config, perfect for dev", "value": "SQLite"},
        ],
        default="PostgreSQL",
    ).execute()

    # Authentication
    auth_enabled = inquirer.confirm(
        message="🔐 Include JWT authentication?", default=True
    ).execute()

    # Docker support
    docker_support = inquirer.confirm(
        message="🐳 Include Docker configuration?", default=True
    ).execute()

    # Testing suite
    testing_suite = inquirer.confirm(
        message="🧪 Include testing suite (pytest)?", default=True
    ).execute()

    # Git initialization
    git_init = inquirer.confirm(message="📦 Initialize Git repository?", default=True).execute()

    # Create and return config
    return ProjectConfig(
        name=name,
        framework=framework,
        orm=orm,
        database=database,
        auth_enabled=auth_enabled,
        docker_support=docker_support,
        testing_suite=testing_suite,
        git_init=git_init,
    )
