from unittest.mock import MagicMock

from litestar import status_codes

from app.db.models.users import User

URL = "/api/auth/sendreset"


async def test_send_reset_with_nonexistent_user(client, faker):
    """
    Test sending a password reset email to a user that does not exist. The endpoint should
    return a 400 error.
    """

    response = await client.post(URL, json={"email": faker.email()})
    assert response.status_code == status_codes.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Account does not exist.",
        "status_code": status_codes.HTTP_400_BAD_REQUEST,
    }


async def test_send_reset_with_unverified_user(client, create_user):
    """
    Test sending a password reset email to a user that is not verified. The endpoint should
    return a 400 error.
    """

    user: User = await create_user(verified=False)
    response = await client.post(URL, json={"email": user.email})
    assert response.status_code == status_codes.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "detail": "Account is not verified.",
        "status_code": status_codes.HTTP_400_BAD_REQUEST,
    }


async def test_send_reset(client, create_user, monkeypatch):
    """
    Test sending a password reset email to a user. The endpoint should return a 200 response and the
    email should be sent out.
    """

    mock_send_email = MagicMock()
    monkeypatch.setattr("app.queue.email.send_email", mock_send_email)

    user: User = await create_user()
    response = await client.post(URL, json={"email": user.email})
    assert response.status_code == status_codes.HTTP_200_OK

    mock_send_email.assert_called_once()
    kwargs = mock_send_email.call_args.kwargs
    assert kwargs["sender"] == "app@dripdrop.pro"
    assert kwargs["recipient"] == user.email
    assert kwargs["subject"] == "Reset Password"
