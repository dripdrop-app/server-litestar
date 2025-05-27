from litestar import status_codes

from app.db.models.users import User

URL = "/api/auth/verify"


async def test_verify_with_invalid_code(client, faker, create_user):
    """
    Test verifying an account with an invalid code. The endpoint should return
    a 400 error with the appropriate message.
    """

    await create_user(verified=False)
    response = await client.get(URL, params={"token": faker.uuid4()})
    assert response.status_code == status_codes.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Token is not valid.",
        "status_code": status_codes.HTTP_400_BAD_REQUEST,
    }


async def test_verify_with_nonexistent_email(client, faker, redis):
    """
    Test verifying with a code for an email that no longer exists. The endpoint should
    return a 400 error with the appropriate message.
    """

    token = faker.uuid4()
    await redis.set(f"verify:{token}", faker.email())
    response = await client.get(URL, params={"token": token})
    assert response.status_code == status_codes.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Account does not exist.",
        "status_code": status_codes.HTTP_400_BAD_REQUEST,
    }


async def test_verify(client, create_user, faker, redis):
    """
    Test verifying an account with a valid token. The endpoint should return a redirect.
    """

    user: User = await create_user(verified=False)
    token = faker.uuid4()
    await redis.set(f"verify:{token}", user.email)

    response = await client.get(URL, params={"token": token}, follow_redirects=False)
    assert response.status_code == status_codes.HTTP_302_FOUND
