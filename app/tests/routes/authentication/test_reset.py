from litestar import status_codes

from app.db.models.users import User

URL = "/api/auth/reset"


async def test_reset_with_invalid_code(client, faker, create_user):
    """
    Test resetting password for an account with an invalid code. The endpoint should return
    a 400 error with the appropriate message.
    """

    await create_user()
    response = await client.post(
        URL, json={"token": faker.uuid4(), "password": faker.password()}
    )
    assert response.status_code == status_codes.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Token is not valid.",
        "status_code": status_codes.HTTP_400_BAD_REQUEST,
    }


async def test_reset_with_nonexistent_email(client, faker, redis):
    """
    Test resetting password with a code for an email that no longer exists. The endpoint should
    return a 400 error with the appropriate message.
    """

    token = faker.uuid4()
    await redis.set(f"reset:{token}", faker.email())
    response = await client.post(
        URL, json={"token": token, "password": faker.password()}
    )
    assert response.status_code == status_codes.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Account does not exist.",
        "status_code": status_codes.HTTP_400_BAD_REQUEST,
    }


async def test_reset(client, create_user, faker, db_session, redis):
    """
    Test resetting a password for an account with a valid token. The endpoint should return a 200
    response.
    """

    user: User = await create_user()
    token = faker.uuid4()
    await redis.set(f"reset:{token}", user.email)

    new_password = faker.password()
    response = await client.post(URL, json={"token": token, "password": new_password})
    assert response.status_code == status_codes.HTTP_200_OK

    await db_session.refresh(user)

    assert user.check_password(new_password) is True
