from litestar.plugins.sqlalchemy import base, repository
from sqlalchemy import event
from sqlalchemy.orm import Mapped, mapped_column
from passlib.context import CryptContext

from sqlalchemy.ext.asyncio import AsyncSession

password_context = CryptContext(schemes=["bcrypt", "argon2"])


class User(base.UUIDAuditBase):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str] = mapped_column(nullable=False)
    admin: Mapped[bool] = mapped_column(nullable=False, default=False)
    verified: Mapped[bool] = mapped_column(nullable=False, default=False)


class UserRespository(repository.SQLAlchemyAsyncRepository[User]):
    model_type = User


async def provide_users_repo(db_session: AsyncSession):
    return UserRespository(session=db_session)


@event.listens_for(User, "init")
def init_user(target, args, kwargs):
    if "password" in kwargs:
        kwargs["password"] = password_context.hash(kwargs["password"])
