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


class AnySetOfValues:
    """
    A helper object that compares equal to any instance of a specific class.
    Implemented with reference of unittest.mock.ANY.
    """

    def __init__(self, values: typing.Iterable):
        self._set_of_values = set(values)

    def __eq__(self, other):
        return self._set_of_values.__eq__(set(other))

    def __ne__(self, other):
        return self._set_of_values.__ne__(set(other))

    def __repr__(self):
        return f'<ANY {self._set_of_values} value set>'
