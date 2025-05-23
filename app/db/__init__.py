from pathlib import Path

from litestar.plugins.sqlalchemy import (
    AlembicAsyncConfig,
    AsyncSessionConfig,
    SQLAlchemyAsyncConfig,
)

from app.settings import settings

session_config = AsyncSessionConfig(expire_on_commit=False)
sqlalchemy_config = SQLAlchemyAsyncConfig(
    connection_string=settings.async_database_url,
    session_config=session_config,
    alembic_config=AlembicAsyncConfig(
        script_config=Path("app/db/alembic.ini"),
        script_location=Path("app/db/migrations"),
    ),
)
