from unittest.mock import MagicMock

from app.db.models.users import User
from app.queue.email import send_password_reset_email


async def test_send_reset(create_user, monkeypatch):
    """
    Test sending a password reset email to a user. The send email function
    should be called with the appropriate information.
    """

    mock_send_email = MagicMock()
    monkeypatch.setattr("app.queue.email.send_email", mock_send_email)

    user: User = await create_user()
    await send_password_reset_email(user.email)
    mock_send_email.assert_called_once()
    kwargs = mock_send_email.call_args.kwargs
    assert kwargs["sender"] == "app@dripdrop.pro"
    assert kwargs["recipient"] == user.email
    assert kwargs["subject"] == "Reset Password"
