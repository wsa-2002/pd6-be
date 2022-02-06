from typing import TypeVar, Optional

import common.base

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


class ChallengePublicizeType(StrEnum):
    start_time = 'START_TIME'
    end_time = 'END_TIME'


class TaskSelectionType(StrEnum):
    last = 'LAST'
    best = 'BEST'


VerdictType = common.base.VerdictType


class ProblemJudgeType(StrEnum):
    normal = 'NORMAL'
    customized = 'CUSTOMIZED'


class FilterOperator(StrEnum):
    gt = greater_than = '>'
    ge = greater_equal = '>='
    eq = equal = '='
    ne = neq = not_equal = '!='
    lt = less_than = '<'
    le = less_equal = '<='

    in_ = 'IN'
    nin = not_in = 'NOT IN'
    bt = between = 'BETWEEN'
    nbt = not_between = 'NOT BETWEEN'

    like = 'LIKE'
    nlike = not_like = 'NOT LIKE'


class SortOrder(StrEnum):
    asc = 'ASC'
    desc = 'DESC'


class ScoreboardType(StrEnum):
    team_project = 'TEAM_PROJECT'
    team_contest = 'TEAM_CONTEST'


class ReviserSettingType(StrEnum):
    customized = 'CUSTOMIZED'
