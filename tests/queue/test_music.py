import json

import httpx
import pytest
from advanced_alchemy.exceptions import NotFoundError

from app.channels import MUSIC_JOB_UPDATE
from app.clients import audiotags
from app.db.models.musicjob import MusicJob
from app.db.models.users import User
from app.queue.music import run_music_job


async def test_run_music_job_with_non_existent_job(faker):
    """
    Test running a music job with a non-existent job ID. The task should
    raise an exception and fail.
    """

    with pytest.raises(NotFoundError):
        await run_music_job(music_job_id=faker.uuid4())


async def test_run_music_job_with_non_existent_file(create_user, create_music_job):
    """
    Test running a music job with a non-existent audio file. The task should
    raise an exception and fail.
    """

    user: User = await create_user()
    music_job: MusicJob = await create_music_job(
        email=user.email,
    )

    with pytest.raises(Exception, match="File not found"):
        await run_music_job(music_job_id=str(music_job.id))


async def test_run_music_job(
    create_user,
    create_music_job,
    db_session,
    test_video_url,
    get_pubsub_channel_messages,
):
    """
    Test running a music job with appropriate parameters. The task should
    complete successfully and with expected published events.
    """

    user: User = await create_user()
    music_job: MusicJob = await create_music_job(
        email=user.email, video_url=test_video_url
    )

    expected_title = music_job.title
    expected_artist = music_job.artist
    expected_album = music_job.album
    expected_grouping = music_job.grouping

    task = run_music_job(music_job_id=str(music_job.id))

    pubsub_messages = await get_pubsub_channel_messages(
        MUSIC_JOB_UPDATE, max_num_messages=2
    )

    await task

    await db_session.refresh(music_job)

    assert music_job.title == expected_title
    assert music_job.artist == expected_artist
    assert music_job.album == expected_album
    assert music_job.grouping == expected_grouping
    assert music_job.completed is not None
    assert music_job.download_url is not None
    assert music_job.download_filename is not None

    assert len(pubsub_messages) == 2
    assert json.loads(pubsub_messages[0]["data"]) == {
        "id": str(music_job.id),
        "status": "STARTED",
    }
    assert json.loads(pubsub_messages[1]["data"]) == {
        "id": str(music_job.id),
        "status": "COMPLETED",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(music_job.download_url)
        assert response.status_code == 200
        tags = await audiotags.AudioTags.read_tags(
            file=response.content, filename="test.mp3"
        )
        assert tags.title == expected_title
        assert tags.artist == expected_artist
        assert tags.album == expected_album
        assert tags.grouping == expected_grouping
