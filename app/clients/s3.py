import asyncio
from urllib.parse import urljoin, urlparse, urlunparse

import boto3
from botocore.config import Config

from app.settings import settings

_client = boto3.client(
    "s3",
    endpoint_url=settings.aws_endpoint_url,
    region_name=settings.aws_region_name,
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
    config=Config(s3={"addressing_style": "virtual"}),
)


def resolve_url(filename: str):
    url = urlparse(urljoin(settings.aws_endpoint_url, filename))
    netloc = f"{settings.aws_s3_bucket}.{url.netloc}"
    return urlunparse(
        [url.scheme, netloc, url.path, url.params, url.query, url.fragment]
    )


async def upload_file(
    filename: str,
    body: bytes,
    content_type: str,
    acl="public-read",
):
    return await asyncio.to_thread(
        _client.put_object,
        Bucket=settings.aws_s3_bucket,
        Key=filename,
        Body=body,
        ACL=acl,
        ContentType=content_type,
    )


async def delete_file(filename: str):
    return await asyncio.to_thread(
        _client.delete_object, Bucket=settings.aws_s3_bucket, Key=filename
    )


async def list_filenames(prefix: str = ""):
    continuation_token = ""
    while True:
        params = {"Bucket": settings.aws_s3_bucket}
        if prefix:
            params["Prefix"] = prefix
        if continuation_token:
            params["ContinuationToken"] = continuation_token
        response = await asyncio.to_thread(_client.list_objects_v2, **params)
        objects: list[str] = list(
            map(lambda object: object["Key"], response.get("Contents", []))
        )
        yield objects
        if not response.get("IsTruncated"):
            break
        continuation_token = response.get("NextContinuationToken", "")
