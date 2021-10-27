class _CauseMixin:
    """
    Allows another Exception to be registered as the cause of new Exception,
    i.e. mimicking the `raise from` syntax (and does almost the same thing).
    """
    def __init__(self, *args, cause: Exception = None, **kwargs):
        """
        An optional `cause` exception can be given, mimicking the `raise from` syntax (and does almost the same thing).
        """
        super().__init__(*args, **kwargs)
        if cause is not None:
            self.__cause__ = cause


class SystemException(_CauseMixin, Exception):
    """
    All system errors (i.e. not a PdogsException) will be raised and wrapped under this exception.
    """


class PdogsException(Exception):
    """
    The base exception of PDOGS; exceptions raised that are subclass of this will NOT be written to error log
    """


class LoginExpired(PdogsException):
    """
    Login has expired, need to re-login
    """


class NoPermission(PdogsException):
    """
    The requester has no permission to do the action
    """


class IllegalInput(_CauseMixin, PdogsException):
    """
    A malformed input is given
    """


class FileDecodeError(PdogsException):
    """
    File format not in utf-8
    """


class MaxPeerReviewCount(PdogsException):
    """
    User had reached the maximum of peer review count
    """


# Team Project Scoreboard


class InvalidFormula(PdogsException):
    """
    A malformed scoring formula is given
    """


class InvalidTeamLabelFilter(PdogsException):
    """
    A malformed team label filter is given
    """


# For import usage
from . import (
    account,
    persistence,
)
