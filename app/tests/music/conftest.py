import httpx
import pytest

from app.clients import s3


@pytest.fixture(scope="session")
async def test_image():
    image_url = s3.resolve_url("assets/dripdrop.png")
    async with httpx.AsyncClient() as client:
        response = await client.get(image_url)
        yield image_url, response.content
