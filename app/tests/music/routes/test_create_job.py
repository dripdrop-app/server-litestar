import asyncio

import httpx
from litestar import status_codes

from app.clients import s3
from app.db.models.musicjob import MusicJobRespository

URL = "/api/music/job/create"


async def test_create_job_when_not_logged_in(client):
    """
    Test creating a music job when not logged in. The endpoint should return a
    401 status.
    """

    response = await client.post(URL)
    assert response.status_code == status_codes.HTTP_401_UNAUTHORIZED


async def test_create_job_with_file_and_video_url(
    client, create_and_login_user, test_video_url, test_audio
):
    """
    Test creating a music job when logged in with a file and video_url. The
    endpoint should return a 422 status.
    """

    await create_and_login_user()
    response = await client.post(
        URL,
        data={
            "title": "title",
            "artist": "artist",
            "album": "album",
            "grouping": "grouping",
            "video_url": test_video_url,
        },
        files={
            "file": ("dripdrop.mp3", test_audio, "audio/mpeg"),
        },
    )
    assert response.status_code == status_codes.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": "'file' and 'video_url' cannot both be defined.",
        "status_code": status_codes.HTTP_422_UNPROCESSABLE_ENTITY,
    }


async def test_create_job_with_invalid_content_type_file(client, create_and_login_user):
    """
    Test creating a music job when logged in but with invalid content type.
    The endpoint should return a 422 status.
    """

    await create_and_login_user()
    response = await client.post(
        URL,
        data={
            "title": "title",
            "artist": "artist",
            "album": "album",
            "grouping": "grouping",
        },
        files={"file": b""},
    )
    assert response.status_code == status_codes.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": "File is incorrect format.",
        "status_code": status_codes.HTTP_422_UNPROCESSABLE_ENTITY,
    }


async def test_create_job_with_file(
    client, create_and_login_user, test_audio, db_session
):
    """
    Test creating a job with an image file but with an audio content type. The endpoint
    should return a 201 status, but the job should fail.
    """

    await create_and_login_user()
    response = await client.post(
        URL,
        data={
            "title": "title",
            "artist": "artist",
            "album": "album",
            "grouping": "grouping",
        },
        files={
            "file": ("dripdrop.mp3", test_audio, "audio/mpeg"),
        },
    )
    assert response.status_code == status_codes.HTTP_201_CREATED

    music_jobs_repo = MusicJobRespository(session=db_session)
    music_jobs = await music_jobs_repo.list()
    assert len(music_jobs) == 1
    music_job = music_jobs[0]
    assert music_job.title == "title"
    assert music_job.artist == "artist"
    assert music_job.album == "album"
    assert music_job.grouping == "grouping"
