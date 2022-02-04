import os
import typing
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

from .. import base, log, util
from . import DownloaderABC


@util.retry(times=3, exceptions=urllib.error.URLError, cooldown=0.25)
def _download_single(url: str, location: str):
    with urllib.request.urlopen(url) as f, open(location, 'wb+') as bf:
        bf.write(f.read() or b'')


@util.retry(times=3, exceptions=urllib.error.URLError, cooldown=0.25)
def _get_single(url: str) -> bytes:
    if not url:
        return b''
    with urllib.request.urlopen(url) as f:
        return f.read() or b''


class ThreadedHttpDownloader(DownloaderABC):
    def as_bytes(self, url: str) -> typing.Tuple[bytes, typing.Optional[base.VerdictType]]:
        if not url:
            log.error('error while downloading as bytes, received url that is empty')
            return b'', base.VerdictType.system_error

        try:
            return _get_single(url), None
        except Exception as e:
            log.exception(e, msg='error while downloading as bytes')
            return b'', base.VerdictType.system_error

    def batch_as_bytes(self, urls: typing.Sequence[str]) \
            -> typing.Tuple[typing.Sequence[bytes], typing.Optional[base.VerdictType]]:
        raise NotImplementedError

    def to_dir(self, url: str, directory: str, filename: str) -> typing.Tuple[str, typing.Optional[base.VerdictType]]:
        if not url:
            log.error('error while downloading as bytes, received url that is empty')
            return '', base.VerdictType.system_error

        location = os.path.join(directory, filename)

        try:
            _download_single(url, location), None
        except Exception as e:
            log.exception(e, msg='error while downloading as bytes')
            return '', base.VerdictType.system_error
        else:
            return location, None

    def batch_to_dir(self, urls: typing.Sequence[str], directory: str, filenames: typing.Sequence[str]) \
            -> typing.Tuple[typing.Sequence[str], typing.Optional[base.VerdictType]]:
        locations = [os.path.join(directory, filename) for filename in filenames]

        try:
            with ThreadPoolExecutor() as pool:
                tasks = [pool.submit(_download_single, url, location)
                         for url, location in zip(urls, locations)]
                as_completed(tasks)
        except Exception as e:
            log.exception(e, msg='error while downloading as bytes')
            return [''], base.VerdictType.system_error
        else:
            return locations, None
