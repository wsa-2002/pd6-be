from datetime import datetime
from functools import wraps
import logging

import traceback
from uuid import uuid1

from config import logger_config
from util import get_request_uuid


class _Logger:
    """
    Logger is initialized in config_logger
    """
    event_logger = logging.getLogger(logger_config.event_logger_name)
    timing_logger = logging.getLogger(logger_config.timing_logger_name)


# Event logging


def info(msg):
    _Logger.event_logger.info(f"request {get_request_uuid()}\t{msg}")


def debug(msg):
    _Logger.event_logger.debug(f"request {get_request_uuid()}\t{msg}")


def error(msg):
    _Logger.event_logger.error(f"request {get_request_uuid()}\t{msg}")


def exception(exc: Exception, msg='', info_level=False):
    if info_level:
        _Logger.event_logger.info(f"{format_exc(exc)}\n{traceback.format_exc()}")
    else:
        _Logger.event_logger.error(f"request {get_request_uuid()}\t{msg}\t{exc.__repr__()}")
        _Logger.event_logger.exception(exc)


# Timing logging


def timed(error_on_exception=False):
    def decorator(timed_func):
        @wraps(timed_func)
        def wrapped(*args, **kwargs):
            uuid = uuid1()

            start = datetime.now()
            _Logger.timing_logger.info(f'request {get_request_uuid()}\t{uuid}\tENTER\t'
                                       f'{timed_func.__module__}.{timed_func.__qualname__}\t')

            try:
                return timed_func(*args, **kwargs)

            except Exception as exc:
                log_message = f"Timed func {timed_func.__qualname__} from {timed_func.__module__} uuid {uuid} " \
                              f"occurred exception"

                if error_on_exception:
                    exception(exc, msg=log_message)
                else:
                    info(f"{log_message}: {format_exc(exc)}")

                raise exc

            finally:
                end = datetime.now()
                _Logger.timing_logger.info(f'request {get_request_uuid()}\t{uuid}\tLEAVE\t'
                                           f'{timed_func.__module__}.{timed_func.__qualname__}\t{end - start}')

        return wrapped
    return decorator


def format_exc(e: Exception):
    return f"{type(e).__name__}: {e}"
