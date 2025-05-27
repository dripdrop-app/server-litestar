import httpx
import pytest

from app.clients import s3


@pytest.fixture(scope="session")
async def test_video_url():
    return "https://www.youtube.com/watch?v=C0DPdy98e4c"


@pytest.fixture(scope="session")
async def test_audio_url():
    return s3.resolve_url("assets/07 tun suh.mp3")


@pytest.fixture(scope="session")
async def test_image():
    image_url = s3.resolve_url("assets/dripdrop.png")
    async with httpx.AsyncClient() as client:
        response = await client.get(image_url)
        assert response.is_success is True
        yield image_url, response.content


@pytest.fixture(scope="session")
async def test_audio(test_audio_url):
    async with httpx.AsyncClient() as client:
        response = await client.get(test_audio_url)
        assert response.is_success is True
        yield response.content
