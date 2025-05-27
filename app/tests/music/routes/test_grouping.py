from litestar import status_codes

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


async def test_grouping_with_invalid_video_url(client, faker, create_and_login_user):
    """
    Test retrieving the grouping for a video with an invalid url. The endpoint
    should return a 400 error.
    """

    await create_and_login_user()
    response = await client.get(URL, params={"video_url": faker.url([])})
    assert response.status_code == status_codes.HTTP_400_BAD_REQUEST


async def test_grouping_with_valid_video_url(client, create_and_login_user):
    """
    Test retrieving the grouping for a valid youtube video. The endpoint should return
    a successful response.
    """

    await create_and_login_user()
    response = await client.get(
        URL,
        params={"video_url": "https://www.youtube.com/watch?v=FCrJNvJ-NIU"},
    )
    assert response.status_code == status_codes.HTTP_200_OK
    assert response.json() == {"grouping": "Food Dip"}
