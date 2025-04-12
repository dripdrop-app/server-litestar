from typing import Callable
from unittest import IsolatedAsyncioTestCase

from faker import Faker
from litestar import status_codes
from litestar.testing import AsyncTestClient
from redis.asyncio.client import Redis
from saq import Queue
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import app
from app.db import sqlalchemy_config
from app.db.models.users import User, provide_users_repo
from app.queue import _is_registered_task, shutdown, startup
from app.queue.context import SAQContext
from app.services import temp_files
from app.settings import ENV, settings


class BaseTestCase(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.maxDiff = None
        self.assertEqual(settings.env, ENV.TESTING)

        self.client = await self.enterAsyncContext(AsyncTestClient(app))

        await self._init_temp()
        await self._init_db()
        await self._init_redis()

        self.faker = Faker()

    async def _init_temp(self):
        await temp_files.create_temp_directory()
        self.addAsyncCleanup(temp_files.cleanup_temp_directory)

    async def _init_db(self):
        sqlalchemy_engine = create_async_engine(settings.async_database_url)
        async with sqlalchemy_engine.begin() as conn:
            await conn.run_sync(sqlalchemy_config.metadata.drop_all)
            await conn.run_sync(sqlalchemy_config.metadata.create_all)
        sessionmaker = async_sessionmaker(sqlalchemy_engine)
        self.db_session = await self.enterAsyncContext(sessionmaker())
        self.addAsyncCleanup(sqlalchemy_engine.dispose)

    async def _init_redis(self):
        self.redis = Redis.from_url(settings.redis_url)
        await self.redis.flushall()

        async def cleanup():
            await self.redis.flushall()
            await self.redis.aclose()
            await self.redis.connection_pool.disconnect()

        self.addAsyncCleanup(cleanup)

    async def login_user(self, email: str, password: str):
        response = await self.client.post(
            "/api/auth/login", json={"email": email, "password": password}
        )
        self.assertEqual(response.status_code, status_codes.HTTP_200_OK)
        self.assertNotIn(self.client.cookies.get("session"), [None, "null"])

    async def create_user(
        self,
        email: str = None,
        password: str = None,
        admin: bool = False,
        verified: bool = True,
    ):
        users_repo = await provide_users_repo(db_session=self.db_session)
        return await users_repo.add(
            User(
                email=email or self.faker.email(),
                password=password or self.faker.password(),
                admin=admin,
                verified=verified,
            ),
            auto_commit=True,
        )


async def test_enqueue_task(
    queue: Queue, func: Callable, retries: int = 3, retry_backoff: bool = True, **kwargs
):
    if not _is_registered_task(func=func):
        raise Exception(f"{func.__qualname__} is not a registered task.")

    context = SAQContext()
    await startup(context)
    await func(context, **kwargs)
    await shutdown(context)
    return
