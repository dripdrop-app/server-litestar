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


async def test_create(client, faker, db_session, mock_enqueue_task, monkeypatch):
    """
    Test creating an account. The endpoint should return a 200
    response and the user should not be verified.
    """

    mock_send_email = MagicMock()
    monkeypatch.setattr("app.queue.email.send_email", mock_send_email)

    email = faker.email()
    response = await client.post(
        URL, json={"email": email, "password": faker.password()}
    )
    assert response.status_code == status_codes.HTTP_200_OK

    mock_send_email.assert_called_once()
    kwargs = mock_send_email.call_args.kwargs
    assert kwargs["sender"] == "app@dripdrop.pro"
    assert kwargs["recipient"] == email
    assert kwargs["subject"] == "Verification"
    users_repo = UserRespository(session=db_session)
    user = await users_repo.get_one_or_none(User.email == email)
    assert user is not None
    assert user.email == email
    assert user.verified is False
