import asyncio
import uuid
from urllib.parse import urlencode, urlunsplit

from app.clients.smtp2go import send_email
from app.queue.context import SAQContext
from app.settings import ENV, settings
from app.templates import template_config


async def send_verification_email(ctx: SAQContext, email: str, base_url: str):
    redis = ctx["redis"]
    verification_code = str(uuid.uuid4())
    await redis.set(f"verify:{verification_code}", email, ex=3600)
    verify_url = urlunsplit(
        [
            "https" if settings.env == ENV.PRODUCTION else "http",
            base_url,
            "/api/auth/verify",
            urlencode({"code": verification_code}),
            "",
        ]
    )
    template_engine = template_config.to_engine()
    verify_template = template_engine.get_template("email/verify.jinja")
    html = await verify_template.render_async(link=verify_url)
    await asyncio.to_thread(
        send_email,
        sender="app@dripdrop.pro",
        recipient=email,
        subject="Verification",
        html=html,
    )


tasks = [send_verification_email]
