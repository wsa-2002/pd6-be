from .base import SafeExecutor


async def add_institute(name: str, email_domain: str) -> int:
    async with SafeExecutor(
            event='',
            sql=r'INSERT INTO institute'
                r'            (name, email_domain)'
                r'     VALUES (%(name)s, %(email_domain)s)'
                r'  RETURNING id',
            name=name,
            email_domain=email_domain,
            fetch=1,
    ) as (institute_id,):
        return institute_id
