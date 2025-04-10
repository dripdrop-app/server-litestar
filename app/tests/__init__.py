from pathlib import Path
from unittest import IsolatedAsyncioTestCase

from faker import Faker
from litestar.testing import subprocess_async_client
from redis.asyncio.client import Redis

from app.db import sqlalchemy_config
from app.db.models import users
from app.services import temp_files
from app.settings import ENV, settings


class BaseTestCase(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.maxDiff = None
        self.assertEqual(settings.env, ENV.TESTING)

        await self._init_temp()
        await self._init_db()
        await self._init_redis()

        self.client = await self.enterAsyncContext(
            subprocess_async_client(
                workdir=Path(__file__).parent.parent.parent, app="app:app"
            )
        )

        self.faker = Faker()

    async def _init_temp(self):
        await temp_files.create_temp_directory()
        self.addAsyncCleanup(temp_files.cleanup_temp_directory)

    async def _init_db(self):
        sqlalchemy_async_engine = sqlalchemy_config.get_engine()
        async with sqlalchemy_async_engine.begin() as conn:
            await conn.run_sync(sqlalchemy_config.metadata.drop_all)
            await conn.run_sync(sqlalchemy_config.metadata.create_all)
        self.db_session = await self.enterAsyncContext(sqlalchemy_config.get_session())

    async def _init_redis(self):
        self.redis = Redis.from_url(settings.redis_url)
        await self.redis.flushall()

        async def cleanup():
            await self.redis.flushall()
            await self.redis.aclose()
            await self.redis.connection_pool.disconnect()

        self.addAsyncCleanup(cleanup)

    async def create_user(
        self,
        email: str = None,
        password: str = None,
        admin: bool = False,
        verified: bool = True,
    ):
        users_repo = await users.provide_users_repo(db_session=self.db_session)
        return await users_repo.add(
            users.User(
                email=email or self.faker.email(),
                password=password or self.faker.password(),
                admin=admin,
                verified=verified,
            )
        )
