import uuid
from enum import Enum
from urllib.parse import urlencode, urlunsplit

from litestar.events import listener

from app.dependencies import provide_redis
from app.settings import ENV, settings


class LISTENER(Enum):
    USER_CREATED = "user_created"


@listener(LISTENER.USER_CREATED)
async def send_verification_email(email: str, base_url: str):
    async with provide_redis() as redis:
        verification_code = str(uuid.uuid4())
        await redis.set(f"verify:{verification_code}", email, ex=3600)
        verify_url = urlunsplit(  # noqa: F841
            [
                "https" if settings.env == ENV.PRODUCTION else "http",
                base_url,
                "/api/auth/verify",
                urlencode({"code": verification_code}),
                "",
            ]
        )
