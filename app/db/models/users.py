import bcrypt
from litestar.plugins.sqlalchemy import base, repository
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column


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
        kwargs["password"] = bcrypt.hashpw(
            bytes(kwargs["password"], encoding="utf-8"), bcrypt.gensalt()
        )
