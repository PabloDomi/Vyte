"""
Alembic setup for FastAPI + SQLAlchemy projects.

We always materialize the structure ourselves instead of shelling out to
`alembic init`, because:
  - it removes the runtime dependency on alembic being installed when vyte runs;
  - we control the content of env.py (async-URL conversion, model imports);
  - it eliminates a platform-specific failure mode (subprocess + cp1252 stdout).
"""

from pathlib import Path


_ALEMBIC_INI = """# A generic, single database configuration.

[alembic]
script_location = alembic
prepend_sys_path = .
path_separator = os

sqlalchemy.url =

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARNING
handlers = console
qualname =

[logger_sqlalchemy]
level = WARNING
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""


_SCRIPT_MAKO = '''"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
'''


def _env_py(module_name: str) -> str:
    """Return the contents of alembic/env.py for the given source module."""
    return f'''import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from {module_name}.database import Base
from {module_name}.models import *  # noqa: F401, F403 - register all models

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Alembic uses sync drivers; rewrite the URL if the app uses async ones.
database_url = os.getenv("DATABASE_URL", "sqlite:///./app.db")
if database_url.startswith("sqlite+aiosqlite"):
    database_url = database_url.replace("sqlite+aiosqlite", "sqlite")
elif database_url.startswith("postgresql+asyncpg"):
    database_url = database_url.replace("postgresql+asyncpg", "postgresql+psycopg2")
elif database_url.startswith("mysql+aiomysql"):
    database_url = database_url.replace("mysql+aiomysql", "mysql+pymysql")

config.set_main_option("sqlalchemy.url", database_url)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={{"paramstyle": "named"}},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {{}}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''


def setup_alembic(project_path: Path, module_name: str = "src") -> None:
    """
    Create the alembic/ directory and configuration files for a project.

    Args:
        project_path: Root of the generated project.
        module_name: Source module name (e.g. "src", "app") whose
            `database` and `models` will be imported by env.py.
    """
    alembic_dir = project_path / "alembic"
    versions_dir = alembic_dir / "versions"

    alembic_dir.mkdir(exist_ok=True)
    versions_dir.mkdir(exist_ok=True)
    (versions_dir / ".gitkeep").touch()

    (project_path / "alembic.ini").write_text(_ALEMBIC_INI, encoding="utf-8")
    (alembic_dir / "env.py").write_text(_env_py(module_name), encoding="utf-8")
    (alembic_dir / "script.py.mako").write_text(_SCRIPT_MAKO, encoding="utf-8")
