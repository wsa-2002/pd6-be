from fastapi import Header


async def valid_code_length(content_length: int = Header(..., lt=1000000)):  # 1mb
    return content_length


async def valid_essay_size(content_length: int = Header(..., lt=10000000)):  # 10mb
    return content_length
