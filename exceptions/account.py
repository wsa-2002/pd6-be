"""
只有 account 相關的 api 會噴的 exception
"""


from . import PdogsException


class LoginFailed(PdogsException):
    """
    Failed to login, perhaps due to wrong password or wrong account
    """


class IllegalCharacter(PdogsException):
    """
    Illegal character in input
    """


class UsernameExists(PdogsException):
    """
    Failed to register due to duplicate username
    """


class StudentCardExists(PdogsException):
    """
    Student card already exists
    """


class StudentCardDoesNotBelong(PdogsException):
    """
    Student card does not belong to this account
    """


class InvalidEmail(PdogsException):
    """
    Email is not valid
    """


class InvalidInstitute(PdogsException):
    """
    Institute is not valid (not exist or disabled)
    """


class StudentIdNotMatchEmail(PdogsException):
    """
    Failed to register due to email and student info not match
    """


class PasswordVerificationFailed(PdogsException):
    """
    Wrong old_password while changing password
    """
