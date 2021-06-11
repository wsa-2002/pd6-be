class PdogsException(Exception):
    """
    The base exception of PDOGS; exceptions raised that are subclass of this will not be written to error log
    """


class LoginExpired(PdogsException):
    """
    Login has expired, need to re-login
    """


class LoginFailed(PdogsException):
    """
    Failed to login, perhaps due to wrong password or wrong account
    """


class NoPermission(PdogsException):
    """
    The requester has no permission to do the action
    """


class NotFound(PdogsException):
    """
    Data not found, e.g. asked data not found in database
    """


class IllegalInput(PdogsException):
    """
    A malformed input is given
    """
    def __init__(self, *args, cause: Exception, **kwargs):
        """
        An optional `cause` exception can be given, mimicking the `raise from` syntax (and does almost the same thing).
        """
        super().__init__(*args, **kwargs)
        self.__cause__ = cause
