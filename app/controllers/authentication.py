from typing import Annotated, Any

import bcrypt
from litestar import Controller, Request, get, post, status_codes
from litestar.di import Provide
from litestar.exceptions import (
    ClientException,
    NotAuthorizedException,
    NotFoundException,
)
from litestar.params import Body
from litestar.response import Redirect
from litestar_saq.config import TaskQueues
from redis.asyncio import Redis

from app.db.models.users import User, UserRespository, provide_users_repo
from app.models.authentication import CreateUser, LoginUser, SessionUser
from app.queue import enqueue_task
from app.queue.email import send_verification_email


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
        if existing_user := await users_repo.get_one_or_none(User.email == data.email):
            if not bcrypt.checkpw(
                bytes(data.password, encoding="utf-8"),
                bytes(existing_user.password, encoding="utf-8"),
            ):
                raise NotAuthorizedException(detail="Incorrect Credentials.")
            if not existing_user.verified:
                raise NotAuthorizedException(detail="Account is not verified.")
            request.set_session({"user_id": existing_user.id})
            return {"detail": "Success."}
        raise NotFoundException()

    @get("/logout", status_code=status_codes.HTTP_200_OK)
    async def logout(self, request: Request) -> dict:
        request.clear_session()
        return {"detail": "Success."}

    @post("/create", status_code=status_codes.HTTP_200_OK, raises=[ClientException])
    async def create_account(
        self,
        data: Annotated[CreateUser, Body()],
        users_repo: UserRespository,
        task_queues: TaskQueues,
        request: Request,
    ) -> dict:
        if await users_repo.get_one_or_none(User.email == data.email):
            raise ClientException(detail="User with this email exists.")
        await users_repo.add(User(email=data.email, password=data.password))
        await enqueue_task(
            queue=task_queues.get("default"),
            func=send_verification_email,
            email=data.email,
            base_url=request.headers.get("Host", request.base_url),
        )
        return {"detail": "Success."}

    @get("/verify", raises=[ClientException])
    async def verify_email(
        self, token: str, users_repo: UserRespository, redis: Redis
    ) -> Redirect:
        redis_key = f"verify:{token}"
        if email := await redis.get(redis_key):
            if user := await users_repo.get_one_or_none(User.email == email.decode()):
                user.verified = True
                await users_repo.update(user)
                await redis.delete(redis_key)
                return Redirect(path="/account")
            raise ClientException(detail="Account does not exist.")
        raise ClientException(detail="Token is not valid.")
