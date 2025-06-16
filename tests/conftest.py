import httpx
import pytest
from faker import Faker
from litestar import status_codes
from litestar.testing import AsyncTestClient
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app import app
from app.clients import s3
from app.db import sqlalchemy_config
from app.db.models.musicjob import MusicJob, provide_music_jobs_repo
from app.db.models.users import User, provide_users_repo
from app.pubsub import PubSub
from app.services import tempfiles
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
    await tempfiles.create_temp_directory()
    yield
    await tempfiles.cleanup_temp_directory()


@pytest.fixture(scope="session", autouse=True)
async def clean_s3():
    yield
    async for filenames in s3.list_filenames(prefix="music/"):
        for filename in filenames:
            await s3.delete_file(filename=filename)


@pytest.fixture(scope="function", autouse=True)
async def db_session():
    engine = create_async_engine(settings.async_database_url)
    async with engine.begin() as conn:
        await conn.run_sync(sqlalchemy_config.metadata.drop_all)
        await conn.run_sync(sqlalchemy_config.metadata.create_all)
    session_maker = async_sessionmaker(engine)
    async with session_maker() as session:
        yield session
    await engine.dispose()


@pytest.fixture(scope="function", autouse=True)
async def redis():
    redis = Redis.from_url(settings.redis_url)
    await redis.flushall()
    yield redis
    await redis.aclose()


@pytest.fixture(scope="function")
async def get_pubsub_channel_messages():
    async def _run(channel: str, max_num_messages: int, timeout: int = 60):
        pubsub = PubSub(channels=[channel])
        messages = []
        async for message in pubsub.listen(
            ignore_subscribe_messages=True, timeout=timeout
        ):
            if not message:
                pubsub.stop_listening()
            messages.append(message)
            if len(messages) == max_num_messages:
                pubsub.stop_listening()
        return messages

    return _run


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


@pytest.fixture(scope="function")
async def create_and_login_user(faker, create_user, login_user):
    async def _run(
        email: str = None,
        password: str = None,
        admin: bool = False,
        verified: bool = True,
    ):
        password = password or faker.password()
        user: User = await create_user(
            email=email,
            password=password,
            admin=admin,
            verified=verified,
        )
        await login_user(email=user.email, password=password)
        return user

    return _run


@pytest.fixture(scope="session")
async def test_video_url():
    return "https://www.youtube.com/watch?v=C0DPdy98e4c"


@pytest.fixture(scope="session")
async def test_audio_url():
    return s3.resolve_url("assets/07 tun suh.mp3")


@pytest.fixture(scope="session")
async def test_image():
    image_url = s3.resolve_url("assets/dripdrop.png")
    async with httpx.AsyncClient() as client:
        response = await client.get(image_url)
        assert response.is_success is True
        yield image_url, response.content


@pytest.fixture(scope="session")
async def test_audio(test_audio_url):
    async with httpx.AsyncClient() as client:
        response = await client.get(test_audio_url)
        assert response.is_success is True
        yield response.content


@pytest.fixture(scope="function")
async def create_music_job(db_session: AsyncSession, faker: Faker):
    async def _run(
        email: str,
        file: bytes = None,
        video_url: str = None,
        artwork_url: str = None,
        title: str = None,
        artist: str = None,
        album: str = None,
        grouping: str = None,
    ):
        music_job_repo = await provide_music_jobs_repo(db_session=db_session)
        music_job = await music_job_repo.add(
            MusicJob(
                user_email=email,
                video_url=video_url,
                title=title or faker.sentence(),
                artist=artist or faker.name(),
                album=album or faker.word(),
                grouping=grouping,
            ),
        )
        await music_job.upload_files(
            file=file,
            artwork_url=artwork_url,
        )
        return music_job

    return _run
