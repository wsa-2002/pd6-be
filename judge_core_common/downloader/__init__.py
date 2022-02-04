import abc
import typing

from .. import base


class DownloaderABC(abc.ABC):
    @abc.abstractmethod
    def as_bytes(self, url: str) -> typing.Tuple[bytes, typing.Optional[base.VerdictType]]:
        pass

    @abc.abstractmethod
    def batch_as_bytes(self, urls: typing.Sequence[str]) \
            -> typing.Tuple[typing.Sequence[bytes], typing.Optional[base.VerdictType]]:
        pass

    @abc.abstractmethod
    def to_dir(self, url: str, directory: str, filename: str) -> typing.Tuple[str, typing.Optional[base.VerdictType]]:
        pass

    @abc.abstractmethod
    def batch_to_dir(self, urls: typing.Sequence[str], directory: str, filenames: typing.Sequence[str]) \
            -> typing.Tuple[typing.Sequence[str], typing.Optional[base.VerdictType]]:
        pass
