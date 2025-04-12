from smtp2go.core import Smtp2goClient

from app.settings import settings

smtp2go_client = Smtp2goClient(api_key=settings.smtp2go_api_key)


def send_email(sender: str, recipient: str, subject: str, html: str):
    response = smtp2go_client.send(
        sender=sender, recipients=[recipient], html=html, subject=subject
    )
    if not response.success:
        raise Exception("Failed to send email.", response.errors)
