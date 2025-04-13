import asyncio
import uuid
from urllib.parse import urlencode, urlunsplit

from app.clients.smtp2go import send_email
from app.queue.context import SAQContext
from app.settings import ENV, settings
from app.templates import template_config


async def _get_and_render_template(template_name: str, *args, **kwargs):
    template_engine = template_config.to_engine()
    template = template_engine.get_template(template_name=template_name)
    return await template.render_async(*args, **kwargs)


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
    html = await _get_and_render_template(
        template_name="email/verify.jinja", link=verify_url
    )
    await asyncio.to_thread(
        send_email,
        sender="app@dripdrop.pro",
        recipient=email,
        subject="Verification",
        html=html,
    )


async def send_password_reset_email(ctx: SAQContext, email: str):
    redis = ctx["redis"]
    reset_code = str(uuid.uuid4())
    await redis.set(f"reset:{reset_code}", email, ex=3600)
    html = await _get_and_render_template(
        template_name="email/reset.jinja", code=reset_code
    )
    await asyncio.to_thread(
        send_email,
        sender="app@dripdrop.pro",
        recipient=email,
        subject="Reset Password",
        html=html,
    )


tasks = [send_verification_email, send_password_reset_email]
