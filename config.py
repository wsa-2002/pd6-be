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

    scoreboard_hardcode_ttl = float(env_values.get('SCOREBOARD_HARDCODE_TTL', '1'))


class ServiceConfig:
    domain = env_values.get('SERVICE_DOMAIN')
    port = env_values.get('SERVICE_PORT')
    use_https = bool(strtobool(env_values.get('SERVICE_USE_HTTPS', 'false')))

    @property
    def url(self) -> str:
        protocol = 'https' if self.use_https else 'http'
        port_postfix = f':{self.port}' if self.port else ''
        return f"{protocol}://{self.domain}{port_postfix}"


class AppConfig:
    title = env_values.get('APP_TITLE') or "PDOGS 6.0"
    docs_username = env_values.get('APP_DOCS_USERNAME', None)
    docs_password = env_values.get('APP_DOCS_PASSWORD', None)
    docs_url = env_values.get('APP_DOCS_URL', None)
    redoc_url = env_values.get('APP_REDOC_URL', None)
    openapi_url = env_values.get('APP_OPENAPI_URL', "/openapi.json")


class DBConfig:
    host = env_values.get('PG_HOST')
    port = env_values.get('PG_PORT')
    username = env_values.get('PG_USERNAME')
    password = env_values.get('PG_PASSWORD')
    db_name = env_values.get('PG_DBNAME')
    max_pool_size = int(env_values.get('PG_MAX_POOL_SIZE', '10'))


class SMTPConfig:
    host = env_values.get('SMTP_HOST')
    port = env_values.get('SMTP_PORT')
    username = env_values.get('SMTP_USERNAME')
    password = env_values.get('SMTP_PASSWORD')
    use_tls = strtobool(env_values.get('SMTP_USE_TLS') or 'False')


class LoggerConfig:
    event_logger_name = env_values.get('EVENT_LOGGER_NAME')
    timing_logger_name = env_values.get('TIMING_LOGGER_NAME')


class PD4SConfig:
    pd4s_salt = env_values.get('PD4S_SALT')


class S3Config:
    endpoint = env_values.get('S3_ENDPOINT')
    access_key = env_values.get('S3_ACCESS_KEY')
    secret_key = env_values.get('S3_SECRET_KEY')


class AmqpConfig:
    host = env_values.get('AMQP_HOST')
    port = int(env_values.get('AMQP_PORT') or '0')
    username = env_values.get('AMQP_USERNAME')
    password = env_values.get('AMQP_PASSWORD')
    report_queue_name = env_values.get('REPORT_QUEUE_NAME', 'report')
    prefetch_count = int(env_values.get('AMQP_PREFETCH_COUNT', '1'))


class ProfilerConfig:
    enabled = bool(strtobool(env_values.get('PROFILER_ENABLED', 'false')))
    interval = float(env_values.get('PROFILER_INTERVAL', '0.0001'))
    file_dir = env_values.get('PROFILER_FILE_DIR')


# default config objects
config = Config()
service_config = ServiceConfig()
app_config = AppConfig()
db_config = DBConfig()
smtp_config = SMTPConfig()
logger_config = LoggerConfig()
pd4s_config = PD4SConfig()
s3_config = S3Config()
amqp_config = AmqpConfig()
profiler_config = ProfilerConfig()
