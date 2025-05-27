import re

from litestar import status_codes

URL = "/api/music/artwork"


async def test_artwork_when_not_logged_in(client):
    """
    Testing resolving artwork url when the user is not logged in. The endpoint
    should return a 401 status.
    """

    response = await client.get(URL, params={"artwork_url": "https://testimage.jpeg"})
    assert response.status_code == status_codes.HTTP_401_UNAUTHORIZED


async def test_artwork_with_invalid_url(client, faker, create_and_login_user):
    """
    Test resolving artwork url logged in but with an invalid url. The endpoint should
    return a 400 error.
    """

    await create_and_login_user()
    response = await client.get(URL, params={"artwork_url": faker.url([])})
    assert response.status_code == status_codes.HTTP_400_BAD_REQUEST


async def test_artwork_with_valid_image_url(client, create_and_login_user, test_image):
    """
    Testing resolving an artwork url when logged in and given a valid image url. The
    endpoint should respond with a 200 response and the same image url.
    """

    await create_and_login_user()
    image_url = test_image[0]
    response = await client.get(URL, params={"artwork_url": image_url})
    assert response.status_code == status_codes.HTTP_200_OK
    assert response.json() == {"resolvedArtworkUrl": image_url}


async def test_artwork_with_valid_soundcloud_url(client, create_and_login_user):
    """
    Test resolving an artwork url when logged in and given a soundcloud url. The endpoint
    should return a 200 status with the artwork url of the given song.
    """

    await create_and_login_user()
    response = await client.get(
        URL,
        params={
            "artwork_url": "https://soundcloud.com/badbunny15/bad-bunny-buscabulla-andrea"
        },
    )
    assert response.status_code == status_codes.HTTP_200_OK
    json = response.json()
    assert (
        re.match(
            r"https:\/\/i1\.sndcdn\.com\/artworks-[a-zA-Z0-9]+-0-t500x500\.jpg",
            json.get("resolvedArtworkUrl", ""),
        )
        is not None
    )
