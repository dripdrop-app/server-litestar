from typing import Callable

import pytest
from faker import Faker
from litestar import status_codes
from litestar.testing import AsyncTestClient
from redis.asyncio.client import Redis
from saq import Queue
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app import app
from app.db import sqlalchemy_config
from app.db.models.users import User, provide_users_repo
from app.queue import _is_registered_task, shutdown, startup
from app.queue.context import SAQContext
from app.services import temp_files
from app.settings import ENV, settings


@pytest.fixture(scope="function")
async def client():
    async with AsyncTestClient(app) as client:
        yield client


@pytest.fixture(scope="function", autouse=True)
async def env():
    assert settings.env == ENV.TESTING


@pytest.fixture(scope="function", autouse=True)
async def init_temp():
    await temp_files.create_temp_directory()
    yield
    await temp_files.cleanup_temp_directory()


@pytest.fixture(scope="function", autouse=True)
async def db_session():
    sqlalchemy_engine = create_async_engine(settings.async_database_url)
    async with sqlalchemy_engine.begin() as conn:
        await conn.run_sync(sqlalchemy_config.metadata.drop_all)
        await conn.run_sync(sqlalchemy_config.metadata.create_all)
    sessionmaker = async_sessionmaker(sqlalchemy_engine)
    async with sessionmaker() as session:
        yield session
    await sqlalchemy_engine.dispose()


@pytest.fixture(scope="function", autouse=True)
async def redis():
    redis = Redis.from_url(settings.redis_url)
    await redis.flushall()
    yield redis
    await redis.aclose()


@pytest.fixture(scope="function", autouse=True)
async def faker():
    return Faker()


@pytest.fixture(scope="function")
async def create_user(db_session: AsyncSession, faker: Faker):
    async def _run(
        email: str = None,
        password: str = None,
        admin: bool = False,
        verified: bool = True,
    ):
        users_repo = await provide_users_repo(db_session=db_session)
        return await users_repo.add(
            User(
                email=email or faker.email(),
                password=password or faker.password(),
                admin=admin,
                verified=verified,
            ),
            auto_commit=True,
        )

    return _run


@pytest.fixture(scope="function")
async def login_user(client: AsyncTestClient):
    async def _run(email: str, password: str):
        response = await client.post(
            "/api/auth/login", json={"email": email, "password": password}
        )
        assert response.status_code == status_codes.HTTP_200_OK
        assert client.cookies.get("session") not in [None, "null"]

    return _run


@pytest.fixture(scope="function", autouse=True)
async def mock_enqueue_task(monkeypatch: pytest.MonkeyPatch):
    async def test_enqueue_task(
        queue: Queue,
        func: Callable,
        retries: int = 3,
        retry_backoff: bool = True,
        **kwargs,
    ):
        if not _is_registered_task(func=func):
            raise Exception(f"{func.__qualname__} is not a registered task.")

        context = SAQContext()
        await startup(context)
        await func(context, **kwargs)
        await shutdown(context)
        return

    monkeypatch.setattr("app.routes.authentication.enqueue_task", test_enqueue_task)
