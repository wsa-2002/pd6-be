class PdogsException(Exception):
    pass


class LoginExpired(PdogsException):
    pass


class NoPermission(PdogsException):
    pass


class NotFound(PdogsException):
    pass
