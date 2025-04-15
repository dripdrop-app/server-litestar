from datetime import datetime

from litestar.plugins.sqlalchemy import base, repository
from sqlalchemy import TIMESTAMP, ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.clients import s3
from app.db.models.users import User


class MusicJob(base.UUIDAuditBase):
    __tablename__ = "music_jobs"

    user_email: Mapped[str] = mapped_column(
        ForeignKey(User.email, onupdate="CASCADE", ondelete="CASCADE"), nullable=False
    )
    artwork_url: Mapped[str | None] = mapped_column(nullable=True)
    artwork_filename: Mapped[str | None] = mapped_column(nullable=True)
    original_filename: Mapped[str | None] = mapped_column(nullable=True)
    filename_url: Mapped[str | None] = mapped_column(nullable=True)
    video_url: Mapped[str | None] = mapped_column(nullable=True)
    download_filename: Mapped[str | None] = mapped_column(nullable=True)
    download_url: Mapped[str | None] = mapped_column(nullable=True)
    title: Mapped[str] = mapped_column(nullable=False)
    artist: Mapped[str] = mapped_column(nullable=False)
    album: Mapped[str] = mapped_column(nullable=False)
    grouping: Mapped[str | None] = mapped_column(nullable=True)
    completed: Mapped[bool] = mapped_column(nullable=False)
    failed: Mapped[bool] = mapped_column(nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    user: Mapped[User] = relationship(back_populates="jobs", uselist=True)

    async def cleanup(self):
        if self.artwork_filename:
            await s3.delete_file(filename=self.artwork_filename)
        if self.download_filename:
            await s3.delete_file(filename=self.download_filename)
        if self.original_filename:
            await s3.delete_file(filename=self.original_filename)


class MusicJobRespository(repository.SQLAlchemyAsyncRepository[MusicJob]):
    model_type = MusicJob


async def provide_music_jobs_repo(db_session: AsyncSession):
    return MusicJobRespository(session=db_session, auto_commit=True)
