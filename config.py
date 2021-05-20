# from distutils.util import strtobool
from datetime import timedelta
import os

from dotenv import dotenv_values


env_values = {
    **dotenv_values(".env"),
    **os.environ,  # Override with OS
}


class Config:
    jwt_secret = env_values.get('JWT_SECRET', 'aaa')
    jwt_encode_algorithm = env_values.get('JWT_ENCODE_ALGORITHM', 'HS256')
    login_expire = timedelta(days=float(env_values.get('LOGIN_EXPIRE_DAYS', '7')))


class AppConfig:
    title = env_values.get('APP_TITLE')
    docs_url = env_values.get('APP_DOCS_URL', None)
    redoc_url = env_values.get('APP_REDOC_URL', None)


class DBConfig:
    host = env_values.get('PG_HOST')
    port = env_values.get('PG_PORT')
    username = env_values.get('PG_USERNAME')
    password = env_values.get('PG_PASSWORD')
    db_name = env_values.get('PG_DBNAME')


# default config objects
config = Config()
app_config = AppConfig()
db_config = DBConfig()
