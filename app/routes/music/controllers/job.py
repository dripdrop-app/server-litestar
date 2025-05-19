import re
from typing import Annotated, Any

from litestar import Controller, Request, Response, post, status_codes
from litestar.background_tasks import BackgroundTask, BackgroundTasks
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.exceptions import ClientException
from litestar.params import Body

from app.db.models.musicjob import (
    MusicJob,
    MusicJobRespository,
    provide_music_jobs_repo,
)
from app.db.models.users import User
from app.models.music import CreateMusicJob
from app.queue import enqueue_task


class JobController(Controller):
    path = "/job"

    dependencies = {"music_jobs_repo": Provide(provide_music_jobs_repo)}

    @post(path="/create", status_code=status_codes.HTTP_201_CREATED)
    async def create_job(
        self,
        request: Request[User, Any, Any],
        data: Annotated[
            CreateMusicJob, Body(media_type=RequestEncodingType.MULTI_PART)
        ],
        music_jobs_repo: MusicJobRespository,
    ) -> None:
        if data.file and data.video_url:
            raise ClientException(
                detail="'file' and 'video_url' cannot both be defined.",
                status_code=status_codes.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        elif data.file is None and data.video_url is None:
            raise ClientException(
                detail="'file' or 'video_url' must be defined.",
                status_code=status_codes.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        if data.file:
            if not re.match("^audio/", data.file.content_type):
                raise ClientException(
                    detail="File is incorrect format.",
                    status_code=status_codes.HTTP_422_UNPROCESSABLE_ENTITY,
                )
        music_job = await music_jobs_repo.add(
            MusicJob(
                user_email=request.user.email,
                video_url=data.video_url.unicode_string() if data.video_url else None,
                title=data.title,
                artist=data.artist,
                album=data.album,
                grouping=data.grouping,
                completed=False,
                failed=False,
            )
        )
        return Response(
            content=None,
            status_code=status_codes.HTTP_201_CREATED,
            background=BackgroundTasks(
                tasks=[
                    BackgroundTask(
                        music_job.upload_files,
                        data.file,
                        data.artwork_url,
                    ),
                    BackgroundTask(
                        enqueue_task,
                        func="run_music_job",
                        music_job_id=str(music_job.id),
                    ),
                ]
            ),
        )
