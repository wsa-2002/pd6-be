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


class ChallengeInSetType(StrEnum):
    start_time = 'START_TIME'
    end_time = 'END_TIME'


class TaskSelectionType(StrEnum):
    last = 'LAST'
    best = 'BEST'


class JudgmentStatusType(StrEnum):
    wfj = 'WAITING FOR JUDGE'
    judging = 'JUDGING'
    ac = 'ACCEPTED'
    wa = 'WRONG ANSWER'
    mle = 'MEMORY LIMIT EXCEED'
    tle = 'TIME LIMIT EXCEED'
    re = 'RUNTIME ERROR'
    ce = 'COMPILE ERROR'
    other = 'OTHER - CONTACT STAFF'
    rf = 'RESTRICTED FUNCTION'
    se = 'SYSTEM ERROR'
