from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

from app import models
from app.config import settings
from app.database import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata

IS_SQLITE = settings.DATABASE_URL.startswith("sqlite")


def _configure(connection=None, url=None, **extra) -> None:
    options = {
        "target_metadata": target_metadata,
        "compare_type": True,
        "render_as_batch": IS_SQLITE,
    }
    options.update(extra)
    if connection is not None:
        options["connection"] = connection
    if url is not None:
        options["url"] = url
    context.configure(**options)


def run_migrations_offline() -> None:
    _configure(
        url=settings.DATABASE_URL,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        _configure(connection=connection)

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
