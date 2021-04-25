from .cls import OrderedMixin, StrEnum


class Role(OrderedMixin, StrEnum):
    guest = 'GUEST'
    normal = 'NORMAL'
    manager = 'MANAGER'

    @property
    def is_manager(self):
        return self is self.manager

    @property
    def not_manager(self):
        return self is not self.manager
