# from distutils.util import strtobool
import os

from dotenv import dotenv_values


env_values = {
    **dotenv_values(".env"),
    **os.environ,  # Override with OS
}


class Config:
    ...


class AppConfig:
    title = env_values.get('APP_TITLE')


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
