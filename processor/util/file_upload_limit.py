from fastapi import Header


def valid_file_length(file_length: int):
    async def validator(content_length: int = Header(..., lt=file_length)):  # 1mb
        return content_length
    return validator
