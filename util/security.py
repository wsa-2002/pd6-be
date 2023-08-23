"""
Handles encryption stuff
"""


from datetime import datetime, timedelta
from functools import partial
from typing import NamedTuple

import jwt
from passlib.hash import argon2
import hashlib

from config import config, pd4s_config
import exceptions as exc


_jwt_encoder = partial(jwt.encode, key=config.jwt_secret, algorithm=config.jwt_encode_algorithm)
_jwt_decoder = partial(jwt.decode, key=config.jwt_secret, algorithms=[config.jwt_encode_algorithm])


def encode_jwt(account_id: int, expire: timedelta, cached_username: str) -> str:
    return _jwt_encoder({
        'account_id': account_id,
        'expire': (datetime.now() + expire).isoformat(),
        'cached_username': cached_username,
    })


class AuthedAccount(NamedTuple):  # Immutable
    id: int
    cached_username: str


def decode_jwt(encoded: str, time: datetime) -> AuthedAccount:
    try:
        decoded = _jwt_decoder(encoded)
    except jwt.DecodeError:
        raise exc.LoginExpired

    expire = datetime.fromisoformat(decoded['expire'])
    if time >= expire:
        raise exc.LoginExpired

    # legacy support
    account_id = decoded.get('account_id', None)
    if not account_id:
        account_id = decoded.get('account-id', None)
    cached_username = decoded.get('cached_username', None)

    return AuthedAccount(
        id=account_id,
        cached_username=cached_username,
    )


def hash_password(password: str) -> str:
    return argon2.hash(password)


def verify_password(to_test: str, hashed: str) -> bool:
    return argon2.verify(to_test, hashed)


def verify_password_4s(to_test: str, hashed: str) -> bool:
    return hashlib.sha1((to_test + pd4s_config.pd4s_salt).encode()).hexdigest() == hashed
