from typing import Annotated

import bcrypt
from litestar import Controller, Request, post
from litestar.exceptions import HTTPException, NotFoundException
from litestar.params import Body

from app.db.models.users import User, UserRespository
from app.models.authentication import LoginUser


class AuthenticationController(Controller):
    path = "auth"

    @post("/login")
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
            raise HTTPException(detail="Incorrect Credentials.")
        if not existing_user.verified:
            raise HTTPException(detail="Account is not verified.")
        request.set_session({"user_id": existing_user.id})
        return {"detail": "Success."}
