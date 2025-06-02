from unittest.mock import MagicMock

from litestar import status_codes

from app.db.models.users import User, UserRespository

URL = "/api/auth/create"


async def test_create_when_user_exists(client, faker, create_user):
    """
    Test creating a user when an account with the email exists. The endpoint should
    return a 400 error.
    """

    user: User = await create_user()
    response = await client.post(
        URL, json={"email": user.email, "password": faker.password()}
    )
    assert response.status_code == status_codes.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "User with this email exists.",
        "status_code": status_codes.HTTP_400_BAD_REQUEST,
    }


async def test_create(client, faker, db_session, monkeypatch):
    """
    Test creating an account. The endpoint should return a 200
    response and the user should not be verified.
    """

    mock_task = MagicMock()
    monkeypatch.setattr("app.queue.email.send_verification_email.delay", mock_task)

    email = faker.email()
    password = faker.password()
    response = await client.post(URL, json={"email": email, "password": password})
    assert response.status_code == status_codes.HTTP_200_OK

    users_repo = UserRespository(session=db_session)
    user = await users_repo.get_one_or_none(User.email == email)
    assert user is not None
    assert user.email == email
    assert user.verified is False
    assert user.check_password(password) is True

    mock_task.assert_called_once()
    kwargs = mock_task.call_args.kwargs
    assert kwargs["email"] == email
