from typing import TypeVar, Optional

from .cls import OrderedMixin, StrEnum


T = TypeVar("T")


class RoleType(OrderedMixin, StrEnum):
    guest = 'GUEST'
    normal = 'NORMAL'
    manager = 'MANAGER'

    def __gt__(self: T, other: Optional[T]):
        if other is None:
            return True
        return super().__gt__(other)

    def __lt__(self: T, other: Optional[T]):
        if other is None:
            return False
        return super().__lt__(other)


class CourseType(StrEnum):
    lesson = 'LESSON'
    contest = 'CONTEST'


class ChallengeType(StrEnum):
    contest = 'CONTEST'
    homework = 'HOMEWORK'


class ChallengePublicizeType(StrEnum):
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
