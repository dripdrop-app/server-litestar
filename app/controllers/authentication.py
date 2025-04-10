from typing import Annotated
from litestar import Controller, post, Request
from litestar.exceptions import NotFoundException, HTTPException
from litestar.params import Body

from app.db.models.users import (
    UserRespository,
    User,
    password_context,
)
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
        password_verified, new_hashed_password = password_context.verify_and_update(
            secret=data.password, hash=existing_user.password
        )
        if new_hashed_password:
            existing_user.password = new_hashed_password
            await users_repo.update(existing_user)
        if not password_verified:
            raise HTTPException(detail="Incorrect Credentials.")
        if not existing_user.verified:
            raise HTTPException(detail="Account is not verified.")
        request.set_session({"user_id": existing_user.id})
        return {"detail": "Success."}
