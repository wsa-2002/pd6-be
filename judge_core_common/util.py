import time
import typing

from . import log


# retry because I don't know why sometimes cannot download from s3
# it will sometimes show cannot find domain :(((
def retry(times: int, exceptions, cooldown: typing.Union[int, float]):
    """
    Retry Decorator
    Retries the wrapped function/method `times` times if the exceptions listed
    in ``exceptions`` are thrown
    """
    def decorator(func):
        def newfn(*args, **kwargs):
            attempt = 0
            while attempt < times:
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    log.warning(
                        'Exception thrown when attempting to run %s, attempt '
                        '%d of %d' % (func, attempt, times)
                    )
                    attempt += 1
                    time.sleep(cooldown)
            return func(*args, **kwargs)
        return newfn
    return decorator
