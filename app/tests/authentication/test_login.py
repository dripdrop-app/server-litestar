from litestar import status_codes

from app.db.models.users import User

URL = "/api/auth/login"


async def test_login_with_non_existent_user(client, faker):
    """
    Test logging in with a user email that does not exist. The endpoint should
    return a 404 error.
    """

    response = await client.post(
        URL,
        json={"email": faker.email(), "password": faker.password()},
    )
    assert response.status_code == status_codes.HTTP_404_NOT_FOUND


async def test_login_with_incorrect_password(client, faker, create_user):
    """
    Test logging in with an incorrect password. The endpoint should return a
    401 status.
    """

    user: User = await create_user(password=faker.password())
    response = await client.post(
        URL, json={"email": user.email, "password": faker.password()}
    )
    assert response.status_code == status_codes.HTTP_401_UNAUTHORIZED


async def test_login_with_unverified_user(client, faker, create_user):
    """
    Test logging in with a user that is not verified. The endpoint should return a
    401 status.
    """

    password = faker.password()
    user: User = await create_user(password=password, verified=False)
    response = await client.post(URL, json={"email": user.email, "password": password})
    assert response.status_code == status_codes.HTTP_401_UNAUTHORIZED


async def test_login_with_correct_credentials(client, faker, create_user):
    """
    Test logging in with correct credentials. The endpoint should return a 200 status
    and the session should be set with the correct user_id.
    """

    password = faker.password()
    user: User = await create_user(password=password)
    response = await client.post(URL, json={"email": user.email, "password": password})
    assert response.status_code == status_codes.HTTP_200_OK
    assert client.cookies.get("session") not in ["null", None]
