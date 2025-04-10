from datetime import timezone as tz
from enum import Enum

from pydantic_settings import BaseSettings, SettingsConfigDict


class ENV(Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", env_file=".env")

    async_database_url: str
    aws_access_key_id: str
    aws_endpoint_url: str
    aws_region_name: str
    aws_secret_access_key: str
    aws_s3_artwork_folder: str
    aws_s3_bucket: str
    aws_s3_music_folder: str
    database_url: str
    env: ENV = ENV.DEVELOPMENT
    google_api_key: str
    invidious_api_url: str
    redis_url: str
    secret_key: str
    sendgrid_api_key: str
    test_async_database_url: str
    test_aws_s3_bucket: str
    test_redis_url: str
    timeout: int = 600
    timezone: tz | None = tz.utc


settings = Settings()


if settings.env == ENV.TESTING or settings.env == ENV.DEVELOPMENT:
    settings.aws_s3_bucket = settings.test_aws_s3_bucket

if settings.env == ENV.TESTING:
    settings.async_database_url = settings.test_async_database_url
    # settings.redis_url = settings.test_redis_url

if settings.async_database_url.find("sqlite") != -1:
    settings.timezone = None
