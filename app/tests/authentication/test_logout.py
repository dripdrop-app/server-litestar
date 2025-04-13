from litestar import status_codes

from app.db.models.users import User

URL = "/api/auth/logout"


async def test_logout_when_not_logged_in(client):
    """
    Test logging out when not logged in. The endpoint should
    return a 401 error.
    """

    response = await client.get(URL)
    assert response.status_code == status_codes.HTTP_401_UNAUTHORIZED


async def test_session_when_logged_in(client, faker, create_user, login_user):
    """
    Test logging out when logged in. The endpoint should return a 200
    response but with cleared cookies.
    """

    password = faker.password()
    user: User = await create_user(password=password)
    await login_user(email=user.email, password=password)
    response = await client.get(URL)
    assert response.status_code == status_codes.HTTP_200_OK
    assert client.cookies.get("session") in ["null", None]
