from datetime import datetime, timedelta

import jwt

import exceptions as exc


SECRET = 'aaa'  # TODO
DEFAULT_VALID = timedelta(days=7)  # TODO


async def encode(account_id: int, expire: timedelta = DEFAULT_VALID) -> str:
    return jwt.encode({
        'account-id': account_id,
        'expire': (datetime.now() + expire).isoformat(),
    }, key=SECRET)


async def decode(encoded: str) -> int:
    decoded = jwt.decode(encoded, key=SECRET)
    expire = datetime.fromisoformat(decoded['expire'])
    if expire > datetime.now():
        raise exc.LoginExpired
    return decoded['account-id']
