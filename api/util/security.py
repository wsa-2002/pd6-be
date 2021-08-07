import hashlib

from passlib.handlers.argon2 import argon2

from config import pd4s_config


def hash_password(password: str) -> str:
    return argon2.hash(password)


def verify_password(to_test: str, hashed: str) -> bool:
    return argon2.verify(to_test, hashed)


def verify_password_4s(to_test: str, hashed: str) -> bool:
    return hashlib.md5(to_test + pd4s_config.pd4s_salt) == hashed