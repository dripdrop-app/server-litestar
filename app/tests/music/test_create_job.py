from litestar import status_codes

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


async def test_create_job_with_invalid_file(client, create_and_login_user, test_image):
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
            "file": ("dripdrop.mp3", test_image[1], "audio/mpeg"),
        },
    )
    assert response.status_code == status_codes.HTTP_201_CREATED
