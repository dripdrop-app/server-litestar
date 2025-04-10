from unittest import IsolatedAsyncioTestCase
from litestar.stores.redis import RedisStore
from litestar.testing import AsyncTestClient
from faker import Faker
from app import app
from app.db import sqlalchemy_config
from app.settings import settings, ENV
from app.services import temp_files
from app.db.models import users


class BaseTestCase(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.maxDiff = None
        self.assertEqual(settings.env, ENV.TESTING)
        await temp_files.create_temp_directory()
        self.addAsyncCleanup(temp_files.cleanup_temp_directory)
        sqlalchemy_async_engine = sqlalchemy_config.get_engine()
        async with sqlalchemy_async_engine.begin() as conn:
            await conn.run_sync(sqlalchemy_config.metadata.drop_all)
            await conn.run_sync(sqlalchemy_config.metadata.create_all)
        app.debug = True
        self.client = await self.enterAsyncContext(AsyncTestClient(app))
        self.db_session = await self.enterAsyncContext(sqlalchemy_config.get_session())
        self.redis = RedisStore.with_client(settings.redis_url)
        self.redis.handle_client_shutdown = True
        self.addAsyncCleanup(self.redis._shutdown)
        await self.redis.delete_all()
        self.faker = Faker()

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
