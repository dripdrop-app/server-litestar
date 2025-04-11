from typing import Any

from litestar.connection import ASGIConnection
from litestar.middleware.session.server_side import (
    ServerSideSessionBackend,
    ServerSideSessionConfig,
)
from litestar.security.session_auth import SessionAuth

from app.db import sqlalchemy_config
from app.db.models.users import User, provide_users_repo


async def retrieve_user_handler(session: dict[str, Any], connection: ASGIConnection):
    async with sqlalchemy_config.get_session() as db_session:
        users_repo = await provide_users_repo(db_session=db_session)
        return (
            await users_repo.get_one_or_none(User.id == user_id)
            if (user_id := session.get("user_id"))
            else None
        )


session_auth = SessionAuth[User, ServerSideSessionBackend](
    retrieve_user_handler=retrieve_user_handler,
    session_backend_config=ServerSideSessionConfig(),
    exclude=[
        "/auth/login",
        "/auth/signup",
        "/auth/verify",
        "/auth/sendreset",
        "/auth/reset",
        "/schema",
    ],
)
