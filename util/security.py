"""
Handles encryption stuff
"""


from datetime import datetime, timedelta
from functools import partial

import jwt
from passlib.hash import argon2, md5_crypt

import log
from config import config, PD4_config
import exceptions as exc


_jwt_encoder = partial(jwt.encode, key=config.jwt_secret, algorithm=config.jwt_encode_algorithm)
_jwt_decoder = partial(jwt.decode, key=config.jwt_secret, algorithms=[config.jwt_encode_algorithm])


def encode_jwt(account_id: int, expire: timedelta) -> str:
    return _jwt_encoder({
        'account-id': account_id,
        'expire': (datetime.now() + expire).isoformat(),
    })


def decode_jwt(encoded: str) -> int:
    try:
        decoded = _jwt_decoder(encoded)
    except jwt.DecodeError:
        raise exc.LoginFailed

    expire = datetime.fromisoformat(decoded['expire'])
    if datetime.now() >= expire:
        raise exc.LoginExpired
    return decoded['account-id']


def hash_password(password: str) -> str:
    return argon2.hash(password)


def verify_password(to_test: str, hashed: str) -> bool:
    return argon2.verify(to_test, hashed)


def verify_password_4s(to_test: str, hashed: str) -> bool:
    return md5_crypt.verify(to_test + PD4_config.PD4_salt, hashed)
