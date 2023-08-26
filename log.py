import logging

import traceback

from config import logger_config
from util.context import context


class _Logger:
    """
    Logger is initialized in config_logger
    """
    event_logger = logging.getLogger(logger_config.event_logger_name)
    timing_logger = logging.getLogger(logger_config.timing_logger_name)


# Event logging


def info(msg):
    _Logger.event_logger.info(f"request {context.get_request_uuid()}\t{msg}")


def debug(msg):
    _Logger.event_logger.debug(f"request {context.get_request_uuid()}\t{msg}")


def error(msg):
    _Logger.event_logger.error(f"request {context.get_request_uuid()}\t{msg}")


def exception(exc: Exception, msg='', info_level=False):
    if info_level:
        _Logger.event_logger.info(f"{format_exc(exc)}\n{traceback.format_exc()}")
    else:
        _Logger.event_logger.error(f"request {context.get_request_uuid()}\t{msg}\t{exc.__repr__()}")
        _Logger.event_logger.exception(exc)


# TODO: fix type hint for async decorators: need new feature in Py 3.10
# # Timing logging
#
# def timed(timed_func):
#     @wraps(timed_func)
#     def wrapped(*args, **kwargs):
#         exec_uuid = uuid1()
#
#         start = datetime.now()
#         _Logger.timing_logger.info(f'request {get_request_uuid()}\t{exec_uuid}\tENTER\t'
#                                    f'{timed_func.__module__}.{timed_func.__qualname__}\t')
#
#         try:
#             return timed_func(*args, **kwargs)
#         finally:
#             end = datetime.now()
#             _Logger.timing_logger.info(f'request {get_request_uuid()}\t{exec_uuid}\tLEAVE\t'
#                                        f'{timed_func.__module__}.{timed_func.__qualname__}\t{end - start}')
#
#     return wrapped


def format_exc(e: Exception):
    return f"{type(e).__name__}: {e}"
