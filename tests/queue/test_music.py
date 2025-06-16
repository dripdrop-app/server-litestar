import json

import httpx
import pytest
from advanced_alchemy.exceptions import NotFoundError
from litestar.datastructures import UploadFile

from app.clients import audiotags
from app.db.models.musicjob import MusicJob
from app.db.models.users import User
from app.pubsub import PubSub
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


async def test_run_music_job_messages(
    create_user,
    create_music_job,
    test_video_url,
    get_pubsub_channel_messages,
):
    """
    Test running a music job with correct parameters. The music job
    should properly send messages to the music job redis channel.
    """

    user: User = await create_user()
    music_job: MusicJob = await create_music_job(
        email=user.email, video_url=test_video_url
    )

    task = run_music_job(music_job_id=str(music_job.id))

    pubsub_messages = await get_pubsub_channel_messages(
        PubSub.Channels.MUSIC_JOB_UPDATE, max_num_messages=2
    )

    await task

    assert len(pubsub_messages) == 2
    assert json.loads(pubsub_messages[0]["data"]) == {
        "id": str(music_job.id),
        "status": "STARTED",
    }
    assert json.loads(pubsub_messages[1]["data"]) == {
        "id": str(music_job.id),
        "status": "COMPLETED",
    }


async def test_run_music_job_with_audio_url(
    create_user,
    create_music_job,
    db_session,
    test_audio_url,
):
    """
    Test running a music job with a video url. The music job
    should finish successfully and with the correct tag values.
    """

    user: User = await create_user()
    music_job: MusicJob = await create_music_job(
        email=user.email, video_url=test_audio_url
    )

    expected_title = music_job.title
    expected_artist = music_job.artist
    expected_album = music_job.album
    expected_grouping = music_job.grouping

    await run_music_job(music_job_id=str(music_job.id))

    await db_session.refresh(music_job)

    assert music_job.title == expected_title
    assert music_job.artist == expected_artist
    assert music_job.album == expected_album
    assert music_job.grouping == expected_grouping
    assert music_job.completed is not None
    assert music_job.download_url is not None
    assert music_job.download_filename is not None

    async with httpx.AsyncClient() as client:
        response = await client.get(music_job.download_url)
        assert response.status_code == 200
        assert response.headers.get("Content-Type") == "audio/mpeg"
        tags = await audiotags.AudioTags.read_tags(
            file=response.content, filename="test.mp3"
        )
        assert tags.title == expected_title
        assert tags.artist == expected_artist
        assert tags.album == expected_album
        assert tags.grouping == expected_grouping


async def test_run_music_job_with_file(
    create_user,
    create_music_job,
    db_session,
    test_audio,
):
    """
    Test running a music job with a music file. The music job
    should finish successfully and with the correct tag values.
    """

    test_file = UploadFile(
        content_type="audio/mpeg", filename="test.mp3", file_data=test_audio
    )

    user: User = await create_user()
    music_job: MusicJob = await create_music_job(email=user.email, file=test_file)

    expected_title = music_job.title
    expected_artist = music_job.artist
    expected_album = music_job.album
    expected_grouping = music_job.grouping

    await run_music_job(music_job_id=str(music_job.id))

    await db_session.refresh(music_job)

    assert music_job.title == expected_title
    assert music_job.artist == expected_artist
    assert music_job.album == expected_album
    assert music_job.grouping == expected_grouping
    assert music_job.completed is not None
    assert music_job.filename_url is not None
    assert music_job.original_filename is not None

    async with httpx.AsyncClient() as client:
        response = await client.get(music_job.download_url)
        assert response.status_code == 200
        assert response.headers.get("Content-Type") == "audio/mpeg"
        tags = await audiotags.AudioTags.read_tags(
            file=response.content, filename="test.mp3"
        )
        assert tags.title == expected_title
        assert tags.artist == expected_artist
        assert tags.album == expected_album
        assert tags.grouping == expected_grouping


async def test_run_music_job_with_external_artwork(
    create_user,
    create_music_job,
    db_session,
    test_audio_url,
    test_image_url,
    test_image,
):
    """
    Test running a music job with an artwork url given. The music job
    should complete successfully with an artwork tag set.
    """

    user: User = await create_user()
    music_job: MusicJob = await create_music_job(
        email=user.email, video_url=test_audio_url, artwork_url=test_image_url
    )

    expected_title = music_job.title
    expected_artist = music_job.artist
    expected_album = music_job.album
    expected_grouping = music_job.grouping

    await run_music_job(music_job_id=str(music_job.id))

    await db_session.refresh(music_job)

    assert music_job.title == expected_title
    assert music_job.artist == expected_artist
    assert music_job.album == expected_album
    assert music_job.grouping == expected_grouping
    assert music_job.completed is not None
    assert music_job.download_url is not None
    assert music_job.download_filename is not None
    assert music_job.artwork_url is not None
    assert music_job.artwork_filename is None

    async with httpx.AsyncClient() as client:
        response = await client.get(music_job.download_url)
        assert response.status_code == 200
        assert response.headers.get("Content-Type") == "audio/mpeg"
        tags = await audiotags.AudioTags.read_tags(
            file=response.content, filename="test.mp3"
        )
        assert tags.title == expected_title
        assert tags.artist == expected_artist
        assert tags.album == expected_album
        assert tags.grouping == expected_grouping
        assert tags.artwork_url == audiotags.AudioTags.get_image_as_base64(
            test_image, "image/png"
        )
