import pytest
from advanced_alchemy.exceptions import NotFoundError

from app.db.models.musicjob import MusicJob
from app.db.models.users import User
from app.queue.music import run_music_job


async def test_run_music_job_with_non_existent_job(faker):
    """
    Test executing a music job with a non-existent job ID. The task should
    raise an exception and fail.
    """

    with pytest.raises(NotFoundError):
        await run_music_job(music_job_id=faker.uuid4())


async def test_run_music_job_with_non_existent_file(create_user, create_music_job):
    """
    Test executing a music job with a non-existent audio file. The task should
    raise an exception and fail.
    """

    user: User = await create_user()
    music_job: MusicJob = await create_music_job(
        email=user.email,
    )

    with pytest.raises(Exception, match="File not found"):
        await run_music_job(music_job_id=str(music_job.id))
