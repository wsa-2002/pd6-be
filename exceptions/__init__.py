class _CauseMixin:
    """
    Allows another Exception to be registered as the cause of new Exception,
    i.e. mimicking the `raise from` syntax (and does almost the same thing).
    """
    def __init__(self, *args, cause: Exception, **kwargs):
        """
        An optional `cause` exception can be given, mimicking the `raise from` syntax (and does almost the same thing).
        """
        super().__init__(*args, **kwargs)
        self.__cause__ = cause


class SystemException(_CauseMixin, Exception):
    """
    All system errors (i.e. not a PdogsException) will be raised and wrapped under this exception.
    """


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


class AccountExists(PdogsException):
    """
    Failed to register due to duplicate account
    """


class StudentCardExists(PdogsException):
    """
    Student card already exists
    """


class EmailNotMatchId(PdogsException):
    """
    Failed to register due to email and student id not match
    """


class NoPermission(PdogsException):
    """
    The requester has no permission to do the action
    """


class NotFound(PdogsException):
    """
    Data not found, e.g. asked data not found in database
    """


class IllegalInput(_CauseMixin, PdogsException):
    """
    A malformed input is given
    """


class PasswordVerificationFailed(PdogsException):
    """
    Wrong old_password while changing password
    """
