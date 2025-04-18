from litestar import status_codes

from app.db.models.users import User

URL = "/api/music/grouping"


async def test_grouping_when_not_logged_in(client):
    """
    Test retrieving the grouping for a video when the user
    is not logged in. The response should return a 401 error.
    """

    response = await client.get(
        URL, params={"video_url": "https://www.youtube.com/watch?v=FCrJNvJ-NIU"}
    )
    assert response.status_code == status_codes.HTTP_401_UNAUTHORIZED


async def test_grouping_with_invalid_video_url(client, faker, create_user, login_user):
    """
    Test retrieving the grouping for a video with an invalid url. The endpoint
    should return a 400 error.
    """

    password = faker.password()
    user: User = await create_user(password=password)
    await login_user(email=user.email, password=password)
    response = await client.get(URL, params={"video_url": "https://invalidurl"})
    assert response.status_code == status_codes.HTTP_400_BAD_REQUEST


async def test_grouping_with_valid_video_url(
    client, faker, create_user, login_user, monkeypatch
):
    """
    Test retrieving the grouping for a valid youtube video. The endpoint should return
    a successful response.
    """

    password = faker.password()
    user: User = await create_user(password=password)
    await login_user(email=user.email, password=password)
    response = await client.get(
        URL,
        params={"video_url": "https://www.youtube.com/watch?v=FCrJNvJ-NIU"},
    )
    assert response.status_code == status_codes.HTTP_200_OK
    assert response.json() == {"grouping": "Food Dip"}
