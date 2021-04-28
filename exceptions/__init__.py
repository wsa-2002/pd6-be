class PdogsException:
    pass


class LoginExpired(PdogsException):
    pass


class NoPermission(PdogsException):
    pass


class NotFound(PdogsException):
    pass
