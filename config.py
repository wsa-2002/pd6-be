from distutils.util import strtobool
import os

from dotenv import dotenv_values


env_values = {
    **dotenv_values(".env"),
    **os.environ,  # Override with OS
}


class Config:
    ...


class DBConfig:
    host = env_values.get('MYSQL_HOST')
    port = env_values.get('MYSQL_PORT')
    username = env_values.get('MYSQL_USERNAME')
    password = env_values.get('MYSQL_PASSWORD')
    db_name = env_values.get('MYSQL_DBNAME')
    autocommit = bool(strtobool(env_values.get('MYSQL_AUTOCOMMIT')))


# default config objects
config = Config()
db_config = DBConfig()
