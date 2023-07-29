import typing


class AnyInstanceOf:
    """
    A helper object that compares equal to any instance of a specific class.
    Implemented with reference of unittest.mock.ANY.
    """

    def __init__(self, target_class: typing.Type):
        self._target_class = target_class

    def __eq__(self, other):
        return isinstance(other, self._target_class)

    def __ne__(self, other):
        return not isinstance(other, self._target_class)

    def __repr__(self):
        return f'<ANY {self._target_class} instance>'


class AnyEqualValue:
    """
    A helper object that compares equality (using operator ==) to any given value.
    Implemented with reference of unittest.mock.ANY.
    """

    def __init__(self, equal_value: typing.Any):
        self._equal_value = equal_value

    def __eq__(self, other):
        return self._equal_value == other

    def __ne__(self, other):
        return self._equal_value != other

    def __repr__(self):
        return f'<ANY {self._equal_value} equivalent>'
