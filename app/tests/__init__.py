from unittest import IsolatedAsyncioTestCase

from faker import Faker
from litestar.testing import AsyncTestClient
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import app
from app.db import sqlalchemy_config
from app.db.models.users import User, provide_users_repo
from app.services import temp_files
from app.settings import ENV, settings


class BaseTestCase(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.maxDiff = None
        self.assertEqual(settings.env, ENV.TESTING)

        await self._init_temp()
        await self._init_db()
        await self._init_redis()

        self.client = await self.enterAsyncContext(AsyncTestClient(app))

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
