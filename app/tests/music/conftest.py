import httpx
import pytest


@pytest.fixture(scope="session")
async def test_image():
    image_url = "https://ewr1.vultrobjects.com/dripdrop-prod/assets/dripdrop.png"
    async with httpx.AsyncClient() as client:
        response = await client.get(image_url)
        yield image_url, response.content
