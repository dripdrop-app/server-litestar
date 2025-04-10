from typing import Any
from litestar.connection import ASGIConnection
from litestar.di import Provide
from litestar.middleware.session.server_side import (
    ServerSideSessionBackend,
    ServerSideSessionConfig,
)
from litestar.security.session_auth import SessionAuth

from app.db.models.users import User, UserRespository, provide_users_repo


async def retrieve_user_handler(
    session: dict[str, Any],
    connection: ASGIConnection,
    users_repo: UserRespository,
) -> User | None:
    return (
        users_repo.get_one_or_none(User.id == user_id)
        if (user_id := session.get("user_id"))
        else None
    )


session_auth = SessionAuth[User, ServerSideSessionBackend](
    retrieve_user_handler=retrieve_user_handler,
    session_backend_config=ServerSideSessionConfig(),
    dependencies={"users_repo": Provide(provide_users_repo)},
    exclude=[
        "/auth/login",
        "/auth/signup",
        "/auth/verify",
        "/auth/sendreset",
        "/auth/reset",
        "/schema",
    ],
)
