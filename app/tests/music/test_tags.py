import httpx
from litestar import status_codes

from app.clients import audiotags, s3

URL = "/api/music/tags"


async def test_tags_when_not_logged_in(client):
    """
    Test retrieving id3 tags from an audio file when not logged in.
    """

    response = await client.post(URL, files={"file": b"test"})
    assert response.status_code == status_codes.HTTP_401_UNAUTHORIZED


async def test_tags_with_an_invalid_file(client, create_and_login_user):
    """
    Test retrieving id3 tags from an audio file when logged in but with
    a non-audio file.
    """

    await create_and_login_user()
    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(s3.resolve_url("assets/dripdrop.png"))
        assert response.status_code == status_codes.HTTP_200_OK
        file = response.content
    response = await client.post(URL, files={"file": file})
    assert response.status_code == status_codes.HTTP_200_OK
    assert response.json() == {
        "title": None,
        "artist": None,
        "album": None,
        "grouping": None,
        "artworkUrl": None,
    }


async def test_tags_with_a_mp3_without_tags(client, create_and_login_user):
    """
    Test retrieving id3 tags from an audio file when logged in and with an audio
    file without id3 tags.
    """

    await create_and_login_user()
    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(s3.resolve_url("/assets/sample4.mp3"))
        assert response.status_code == status_codes.HTTP_200_OK
        file = response.content
    response = await client.post(URL, files={"file": file})
    assert response.status_code == status_codes.HTTP_200_OK
    assert response.json() == {
        "title": None,
        "artist": None,
        "album": None,
        "grouping": None,
        "artworkUrl": None,
    }


async def test_tags_with_a_valid_mp3_file(client, create_and_login_user):
    """
    Test retrieving id3 tags from an audio file when logged in and with an audio
    file with id3 tags.
    """

    await create_and_login_user()
    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(
            s3.resolve_url("assets/Criminal%20Sinny%20&%20Fako.mp3")
        )
        assert response.status_code == status_codes.HTTP_200_OK
        file = response.content
    tags = await audiotags.AudioTags.read_tags(file=file, filename="test.mp3")
    response = await client.post(URL, files={"file": file})
    assert response.status_code == status_codes.HTTP_200_OK
    assert response.json() == {
        "title": "Criminal",
        "artist": "Sinny & Fako",
        "album": "Criminal - Single",
        "grouping": "Tribal Trap",
        "artworkUrl": tags.artwork_url,
    }
