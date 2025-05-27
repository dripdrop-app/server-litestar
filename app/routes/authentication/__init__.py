from typing import Annotated, Any

from litestar import Request, Response, Router, get, post, status_codes
from litestar.background_tasks import BackgroundTask
from litestar.di import Provide
from litestar.exceptions import (
    ClientException,
    NotAuthorizedException,
    NotFoundException,
)
from litestar.params import Body
from litestar.response import Redirect
from redis.asyncio import Redis

from app.db.models.users import User, UserRespository, provide_users_repo
from app.models.authentication import (
    CreateUser,
    LoginUser,
    PasswordReset,
    SendResetPassword,
    SessionUser,
)
from app.queue.email import send_password_reset_email, send_verification_email


@get("/session", status_code=status_codes.HTTP_200_OK)
async def get_session(request: Request[User, Any, Any]) -> SessionUser:
    user = request.user
    return SessionUser(email=user.email, admin=user.admin)


@post(
    "/login",
    status_code=status_codes.HTTP_200_OK,
    raises=[NotFoundException, NotAuthorizedException],
)
async def login(
    data: Annotated[LoginUser, Body()],
    users_repo: UserRespository,
    request: Request,
) -> dict:
    if existing_user := await users_repo.get_one_or_none(User.email == data.email):
        if not existing_user.check_password(data.password):
            raise NotAuthorizedException(detail="Incorrect Credentials.")
        if not existing_user.verified:
            raise NotAuthorizedException(detail="Account is not verified.")
        request.set_session({"user_id": existing_user.id})
        return {"detail": "Success."}
    raise NotFoundException()


@get("/logout", status_code=status_codes.HTTP_200_OK)
async def logout(request: Request) -> dict:
    request.clear_session()
    return {"detail": "Success."}


@post("/create", status_code=status_codes.HTTP_200_OK, raises=[ClientException])
async def create_account(
    data: Annotated[CreateUser, Body()],
    users_repo: UserRespository,
    request: Request,
) -> dict:
    if await users_repo.get_one_or_none(User.email == data.email):
        raise ClientException(detail="User with this email exists.")
    await users_repo.add(User(email=data.email, password=data.password))
    return Response(
        content={"detail": "Success."},
        status_code=status_codes.HTTP_200_OK,
        background=BackgroundTask(
            send_verification_email.delay,
            email=data.email,
            base_url=request.headers.get("Host", request.base_url),
        ),
    )


@get("/verify", status_code=status_codes.HTTP_200_OK, raises=[ClientException])
async def verify_email(
    token: str, users_repo: UserRespository, redis: Redis
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


@post(
    "/sendreset",
    status_code=status_codes.HTTP_200_OK,
    raises=[ClientException],
)
async def send_reset_email(
    data: Annotated[SendResetPassword, Body()],
    users_repo: UserRespository,
) -> dict:
    if user := await users_repo.get_one_or_none(User.email == data.email):
        if not user.verified:
            raise ClientException(detail="Account is not verified.")
        return Response(
            content={"detail": "Success."},
            status_code=status_codes.HTTP_200_OK,
            background=BackgroundTask(
                send_password_reset_email.delay,
                email=data.email,
            ),
        )
    raise ClientException(detail="Account does not exist.")


@post("/reset", status_code=status_codes.HTTP_200_OK, raises=[ClientException])
async def reset_password(
    data: Annotated[PasswordReset, Body()],
    users_repo: UserRespository,
    redis: Redis,
) -> dict:
    redis_key = f"reset:{data.token}"
    if email := await redis.get(redis_key):
        if user := await users_repo.get_one_or_none(User.email == email.decode()):
            user.set_password(data.password)
            await users_repo.update(user)
            await redis.delete(redis_key)
            return {"detail": "Success."}
        raise ClientException(detail="Account does not exist.")
    raise ClientException(detail="Token is not valid.")


router = Router(
    path="/auth",
    dependencies={"users_repo": Provide(provide_users_repo)},
    route_handlers=[
        get_session,
        login,
        logout,
        create_account,
        verify_email,
        send_reset_email,
        reset_password,
    ],
    tags=["Authentication"],
)
