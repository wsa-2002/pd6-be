from distutils.util import strtobool
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


class ServiceConfig:
    domain = env_values.get('SERVICE_DOMAIN')
    port = env_values.get('SERVICE_PORT')
    use_https = strtobool(env_values.get('SERVICE_USE_HTTPS'))

    @property
    def url(self) -> str:
        protocol = 'https' if self.use_https else 'http'
        port_postfix = f':{self.port}' if self.port else ''
        return f"{protocol}://{self.domain}{port_postfix}"


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


class SMTPConfig:
    host = env_values.get('SMTP_HOST')
    port = env_values.get('SMTP_PORT')
    username = env_values.get('SMTP_USERNAME')
    password = env_values.get('SMTP_PASSWORD')
    use_tls = strtobool(env_values.get('SMTP_USE_TLS'))


class LoggerConfig:
    event_logger_name = env_values.get('EVENT_LOGGER_NAME')
    timing_logger_name = env_values.get('TIMING_LOGGER_NAME')


class PD4SConfig:
    pd4s_salt = env_values.get('PD4S_SALT')


# default config objects
config = Config()
service_config = ServiceConfig()
app_config = AppConfig()
db_config = DBConfig()
smtp_config = SMTPConfig()
logger_config = LoggerConfig()
pd4s_config = PD4SConfig()
