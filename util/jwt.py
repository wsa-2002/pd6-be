from datetime import datetime, timedelta

import jwt

import exceptions as exc


SECRET = 'aaa'  # TODO
DEFAULT_VALID = timedelta(days=7)  # TODO
ENCODE_ALGORITHM = 'HS256'


async def encode(account_id: int, expire: timedelta = DEFAULT_VALID) -> str:
    return jwt.encode({
        'account-id': account_id,
        'expire': (datetime.now() + expire).isoformat(),
    }, key=SECRET, algorithm=ENCODE_ALGORITHM)


async def decode(encoded: str) -> int:
    decoded = jwt.decode(encoded, key=SECRET, algorithms=[ENCODE_ALGORITHM])
    expire = datetime.fromisoformat(decoded['expire'])
    if expire > datetime.now():
        raise exc.LoginExpired
    return decoded['account-id']
