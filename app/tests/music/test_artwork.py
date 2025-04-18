import re

from litestar import status_codes

from app.db.models.users import User

URL = "/api/music/artwork"


async def test_artwork_when_not_logged_in(client):
    """
    Testing resolving artwork url when the user is not logged in. The endpoint
    should return a 401 status.
    """

    response = await client.get(URL, params={"URL": "https://testimage.jpeg"})
    assert response.status_code == status_codes.HTTP_401_UNAUTHORIZED


async def test_artwork_with_invalid_url(client, faker, create_user, login_user):
    """
    Test resolving artwork url logged in but with an invalid url. The endpoint should
    return a 400 error.
    """

    password = faker.password()
    user: User = await create_user(password=password)
    await login_user(email=user.email, password=password)
    response = await client.get(URL, params={"URL": "https://invalidurl"})
    assert response.status_code == status_codes.HTTP_400_BAD_REQUEST


async def test_artwork_with_valid_image_url(
    client, faker, create_user, login_user, test_image
):
    """
    Testing resolving an artwork url when logged in and given a valid image url. The
    endpoint should respond with a 200 response and the same image url.
    """

    password = faker.password()
    user: User = await create_user(password=password)
    await login_user(email=user.email, password=password)
    (test_image_url, test_image) = test_image
    response = await client.get(URL, params={"artwork_url": test_image_url})
    assert response.status_code == status_codes.HTTP_200_OK
    assert response.json() == {"resolvedArtworkUrl": test_image_url}


async def test_artwork_with_valid_soundcloud_url(
    client, faker, create_user, login_user
):
    """
    Test resolving an artwork url when logged in and given a soundcloud url. The endpoint
    should return a 200 status with the artwork url of the given song.
    """

    password = faker.password()
    user: User = await create_user(password=password)
    await login_user(email=user.email, password=password)
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
