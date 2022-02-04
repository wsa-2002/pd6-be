import logging
import threading
import traceback

_local = threading.local()
_local.submission_id = None
_local.worker_id = None


def set_task(submission_id):
    global _local
    _local.submission_id = submission_id


def set_worker(worker_id):
    global _local
    _local.worker_id = worker_id


class _Logger:
    """
    Logger is initialized in config_logger
    """
    event_logger = logging.getLogger('_log_.event')


# Event logging


def info(msg):
    _Logger.event_logger.info(f"Worker {_local.worker_id}\tSubmission {_local.submission_id}\t{msg}")


def debug(msg):
    _Logger.event_logger.debug(f"Worker {_local.worker_id}\tSubmission {_local.submission_id}\t{msg}")


def warning(msg):
    _Logger.event_logger.warning(f"Worker {_local.worker_id}\tSubmission {_local.submission_id}\t{msg}")


def error(msg):
    _Logger.event_logger.error(f"Worker {_local.worker_id}\tSubmission {_local.submission_id}\t{msg}")


def exception(exc: Exception, msg='', info_level=False):
    if info_level:
        _Logger.event_logger.info(f"Worker {_local.worker_id}\tSubmission {_local.submission_id}\n"
                                  f"{format_exc(exc)}\n"
                                  f"{traceback.format_exc()}")
    else:
        _Logger.event_logger.error(
            f"Worker {_local.worker_id}\tSubmission {_local.submission_id}\t{msg}\t{exc.__repr__()}")
        _Logger.event_logger.exception(exc)


def format_exc(e: Exception):
    return f"{type(e).__name__}: {e}"
