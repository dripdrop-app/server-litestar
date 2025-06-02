from unittest.mock import MagicMock
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

from app.db.models.users import User
from app.queue.email import send_password_reset_email, send_verification_email


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


async def test_send_verification(create_user, redis, monkeypatch):
    """
    Test sending a verification email to a user. The send email function
    should be called with the appropriate information.
    """

    mock_send_email = MagicMock()
    monkeypatch.setattr("app.queue.email.send_email", mock_send_email)

    user: User = await create_user()
    await send_verification_email(user.email, "http://testserver")
    mock_send_email.assert_called_once()
    kwargs = mock_send_email.call_args.kwargs
    assert kwargs["sender"] == "app@dripdrop.pro"
    assert kwargs["recipient"] == user.email
    assert kwargs["subject"] == "Verification"

    html_content = kwargs["html"]
    soup = BeautifulSoup(html_content, "html.parser")
    link = soup.find("a", href=True)

    assert link is not None

    url_parts = urlparse(link["href"])
    query_params = parse_qs(url_parts.query)

    assert "code" in query_params
    assert len(query_params["code"]) == 1

    verification_code = query_params["code"][0]
    key = f"verify:{verification_code}"
    assert await redis.exists(key)
    assert await redis.get(key) == user.email.encode()
