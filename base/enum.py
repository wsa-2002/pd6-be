from .cls import OrderedMixin, StrEnum


class RoleType(OrderedMixin, StrEnum):
    guest = 'GUEST'
    normal = 'NORMAL'
    manager = 'MANAGER'

    @property
    def is_manager(self):
        return self is self.manager

    @property
    def not_manager(self):
        return self is not self.manager

    @property
    def is_guest(self):
        return self is self.guest

    @property
    def not_guest(self):
        return self is not self.guest


class CourseType(StrEnum):
    lesson = 'LESSON'
    contest = 'CONTEST'


class ChallengeType(StrEnum):
    contest = 'CONTEST'
    homework = 'HOMEWORK'


class ProblemType(StrEnum):
    judge = 'JUDGE'
    options = 'OPTIONS'
    file = 'FILE'
    peer = 'PEER'
    project = 'PROJECT'
    special = 'SPECIAL'
