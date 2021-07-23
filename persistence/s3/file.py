from . import s3_handler


# upload: replace original file if file already exists
async def upload(bucket: str, key: str):
    async with s3_handler.client as client:
        filename = key[key.rfind('/') + 1:]
        await client.upload_file(filename, bucket, key)


async def delete(bucket: str, key: str):
    async with s3_handler.client as client:
        await client.delete_object(Bucket=bucket, Key=key)


async def download(bucket: str, key: str):
    async with s3_handler.client as client:
        filename = key[key.rfind('/') + 1:]
        await client.download_file(bucket, key, filename)
