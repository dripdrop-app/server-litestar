from typing import Annotated, Any

import bcrypt
from litestar import Controller, Request, get, post, status_codes
from litestar.di import Provide
from litestar.exceptions import (
    NotAuthorizedException,
    NotFoundException,
)
from litestar.params import Body

from app.db.models.users import User, UserRespository, provide_users_repo
from app.models.authentication import LoginUser, SessionUser


class AuthenticationController(Controller):
    path = "auth"

    dependencies = {"users_repo": Provide(provide_users_repo)}

    @get("/session", status_code=status_codes.HTTP_200_OK)
    async def get_session(self, request: Request[User, Any, Any]) -> SessionUser:
        user = request.user
        return SessionUser(email=user.email, admin=user.admin)

    @post(
        "/login",
        status_code=status_codes.HTTP_200_OK,
        raises=[NotFoundException, NotAuthorizedException],
    )
    async def login(
        self,
        data: Annotated[LoginUser, Body()],
        users_repo: UserRespository,
        request: Request,
    ) -> dict:
        existing_user = await users_repo.get_one_or_none(User.email == data.email)
        if not existing_user:
            raise NotFoundException()
        password_verified = bcrypt.checkpw(
            bytes(data.password, encoding="utf-8"),
            bytes(existing_user.password, encoding="utf-8"),
        )
        if not password_verified:
            raise NotAuthorizedException(detail="Incorrect Credentials.")
        if not existing_user.verified:
            raise NotAuthorizedException(detail="Account is not verified.")
        request.set_session({"user_id": existing_user.id})
        return {"detail": "Success."}

    @get("/logout", status_code=status_codes.HTTP_200_OK)
    async def logout(self, request: Request) -> dict:
        request.clear_session()
        return {"detail": "Success."}
