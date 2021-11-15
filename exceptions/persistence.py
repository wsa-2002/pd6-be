from . import PdogsException, _CauseMixin


class NotFound(PdogsException):
    """
    Object not found, e.g. asked data not found in database
    """


class UniqueViolationError(_CauseMixin, PdogsException):
    """
    Operation violates the unique constraint
    """


class ForeignKeyViolationError(_CauseMixin, PdogsException):
    """
    Operation violates the foreign key constraint
    """
