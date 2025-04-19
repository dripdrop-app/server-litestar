from typing import TYPE_CHECKING

import bcrypt
from litestar.plugins.sqlalchemy import base, repository
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.db.models.musicjob import MusicJob


class User(base.UUIDAuditBase):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str] = mapped_column(nullable=False)
    admin: Mapped[bool] = mapped_column(nullable=False, default=False)
    verified: Mapped[bool] = mapped_column(nullable=False, default=False)
    jobs: Mapped[list["MusicJob"]] = relationship("MusicJob", back_populates="user")

    def set_password(self, new_password: str):
        self.password = str(
            bcrypt.hashpw(bytes(new_password, encoding="utf-8"), bcrypt.gensalt()),
            encoding="utf-8",
        )

    def check_password(self, password: str):
        return bcrypt.checkpw(
            bytes(password, encoding="utf-8"),
            bytes(self.password, encoding="utf-8"),
        )


class UserRespository(repository.SQLAlchemyAsyncRepository[User]):
    model_type = User


async def provide_users_repo(db_session: AsyncSession):
    return UserRespository(session=db_session, auto_commit=True)


@event.listens_for(User, "init")
def init_user(target, args, kwargs):
    if "password" in kwargs:
        kwargs["password"] = str(
            bcrypt.hashpw(
                bytes(kwargs["password"], encoding="utf-8"), bcrypt.gensalt()
            ),
            encoding="utf-8",
        )
