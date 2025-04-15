import asyncio

import boto3

from app.settings import settings


def resolve_url(filename: str):
    return f"{settings.aws_endpoint_url}/{settings.aws_s3_bucket}/{filename}"


_client = boto3.client(
    "s3",
    endpoint_url=settings.aws_endpoint_url,
    region_name=settings.aws_region_name,
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
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


async def list_objects():
    continuation_token = ""
    while True:
        params = {"Bucket": settings.aws_s3_bucket}
        if continuation_token:
            params["ContinuationToken"] = continuation_token
        response = await asyncio.to_thread(_client.list_objects_v2, **params)
        objects = map(lambda object: object["Key"], response.get("Contents", []))
        yield objects
        if not response.get("IsTruncated"):
            break
        continuation_token = response.get("NextContinuationToken", "")
