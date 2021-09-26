from typing import Sequence
from datetime import datetime

from base import vo
from base.enum import SortOrder, FilterOperator, ChallengePublicizeType
from base.popo import Filter, Sorter

from .base import SafeExecutor
from .util import execute_count, compile_filters


async def account(limit: int, offset: int, filters: list[Filter], sorters: list[Sorter]) \
        -> tuple[Sequence[vo.ViewAccount], int]:

    cond_sql, cond_params = compile_filters(filters)
    sort_sql = ' ,'.join(f"{sorter.col_name} {sorter.order}" for sorter in sorters)
    if sort_sql:
        sort_sql += ','

    async with SafeExecutor(
            event='browse account with default student card',
            sql=fr'SELECT account.id              AS account_id,'
                fr'       account.username        AS username,'
                fr'       student_card.student_id AS student_id,'
                fr'       account.real_name       AS real_name'
                fr'  FROM account'
                fr'  LEFT JOIN student_card'
                fr'         ON student_card.account_id = account.id'
                fr'        AND student_card.is_default'
                fr' WHERE NOT account.is_deleted'
                fr'{f" AND {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY {sort_sql} account_id ASC'
                fr' LIMIT %(limit)s OFFSET %(offset)s',
            **cond_params,
            limit=limit, offset=offset,
            fetch='all',
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        data = [vo.ViewAccount(account_id=account_id,
                               username=username,
                               real_name=real_name,
                               student_id=student_id)
                for (account_id, username, real_name, student_id) in records]

    total_count = await execute_count(
        sql=fr'SELECT *'
            fr'  FROM view_account'
            fr'{f" WHERE {cond_sql}" if cond_sql else ""}',
        **cond_params,
    )

    return data, total_count


async def class_member(limit: int, offset: int, filters: Sequence[Filter], sorters: Sequence[Sorter]) \
        -> tuple[Sequence[vo.ViewClassMember], int]:

    sorters += [Sorter(col_name='role',
                       order=SortOrder.desc)]

    cond_sql, cond_params = compile_filters(filters)
    sort_sql = ' ,'.join(f"{sorter.col_name} {sorter.order}" for sorter in sorters)
    if sort_sql:
        sort_sql += ','

    async with SafeExecutor(
            event='browse class members with student card',
            sql=fr'SELECT class_member.member_id     AS account_id,'
                fr'       account.username           AS username,'
                fr'       student_card.student_id    AS student_id,'
                fr'       account.real_name          AS real_name,'
                fr'       institute.abbreviated_name AS abbreviated_name,'
                fr'       class_member.role          AS role,'
                fr'       class_member.class_id      AS class_id'
                fr'  FROM class_member'
                fr' INNER JOIN account'
                fr'         ON class_member.member_id = account.id'
                fr'        AND NOT account.is_deleted'
                fr'  LEFT JOIN student_card'
                fr'         ON account.id = student_card.account_id'
                fr'        AND student_card.is_default'
                fr'  LEFT JOIN institute'
                fr'         ON student_card.institute_id = institute.id'
                fr'{f" WHERE {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY {sort_sql} account_id ASC'
                fr' LIMIT %(limit)s OFFSET %(offset)s',
            **cond_params,
            limit=limit, offset=offset,
            fetch='all',
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        data = [vo.ViewClassMember(account_id=account_id,
                                   username=username,
                                   student_id=student_id,
                                   real_name=real_name,
                                   abbreviated_name=abbreviated_name,
                                   role=role,
                                   class_id=class_id)
                for (account_id, username, student_id, real_name, abbreviated_name, role, class_id)
                in records]

    total_count = await execute_count(
        sql=fr'SELECT *'
            fr'  FROM view_class_member'
            fr'{f" WHERE {cond_sql}" if cond_sql else ""}',
        **cond_params,
    )
    return data, total_count


async def class_submission(class_id: int, limit: int, offset: int,
                           filters: Sequence[Filter], sorters: Sequence[Sorter]) \
        -> tuple[Sequence[vo.ViewSubmissionUnderClass], int]:

    filters += [Filter(col_name='class_id',
                       op=FilterOperator.eq,
                       value=class_id)]

    cond_sql, cond_params = compile_filters(filters)
    sort_sql = ' ,'.join(f"{sorter.col_name} {sorter.order}" for sorter in sorters)
    if sort_sql:
        sort_sql += ','

    async with SafeExecutor(
            event='browse submissions',
            sql=fr'SELECT *'
                fr'FROM ('
                fr'    SELECT DISTINCT ON (submission.id)'
                fr'           submission.id           AS submission_id,'
                fr'           account.id              AS account_id,'
                fr'           account.username        AS username,'
                fr'           student_card.student_id AS student_id,'
                fr'           account.real_name       AS real_name,'
                fr'           problem.challenge_id    AS challenge_id,'
                fr'           challenge.title         AS challenge_title,'
                fr'           problem.id              AS problem_id,'
                fr'           problem.challenge_label AS challenge_label,'
                fr'           judgment.verdict        AS verdict,'
                fr'           submission.submit_time  AS submit_time,'
                fr'           challenge.class_id      AS class_id'
                fr'      FROM submission'
                fr'      LEFT JOIN account'
                fr'             ON account.id = submission.account_id'
                fr'            AND NOT account.is_deleted'
                fr'      LEFT JOIN student_card'
                fr'             ON student_card.account_id = submission.account_id'
                fr'            AND student_card.is_default'
                fr'      LEFT JOIN problem'
                fr'             ON problem.id = submission.problem_id'
                fr'            AND NOT problem.is_deleted'
                fr'      LEFT JOIN challenge'
                fr'             ON challenge.id = problem.challenge_id'
                fr'            AND NOT challenge.is_deleted'
                fr'      LEFT JOIN judgment'
                fr'             ON judgment.submission_id = submission.id'
                fr'    {f" WHERE {cond_sql}" if cond_sql else ""}'
                fr'     ORDER BY submission.id DESC, judgment.judge_time DESC'
                fr') __TABLE__'
                fr' ORDER BY {sort_sql}'
                fr' LIMIT %(limit)s OFFSET %(offset)s',
            **cond_params,
            limit=limit, offset=offset,
            fetch='all',
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        data = [vo.ViewSubmissionUnderClass(submission_id=submission_id,
                                            account_id=account_id,
                                            username=username,
                                            student_id=student_id,
                                            real_name=real_name,
                                            challenge_id=challenge_id,
                                            challenge_title=challenge_title,
                                            problem_id=problem_id,
                                            challenge_label=challenge_label,
                                            verdict=verdict,
                                            submit_time=submit_time,
                                            class_id=class_id)
                for (submission_id, account_id, username, student_id, real_name, challenge_id,
                     challenge_title, problem_id, challenge_label, verdict, submit_time, class_id)
                in records]

    total_count = await execute_count(
        sql=fr'SELECT *'
            fr'  FROM view_submission_under_class'
            fr'{f" WHERE {cond_sql}" if cond_sql else ""}',
        **cond_params,
        class_id=class_id,
    )
    return data, total_count


async def my_submission(limit: int, offset: int, filters: Sequence[Filter], sorters: Sequence[Sorter]) \
        -> tuple[Sequence[vo.ViewMySubmission], int]:

    cond_sql, cond_params = compile_filters(filters)
    sort_sql = ' ,'.join(f"{sorter.col_name} {sorter.order}" for sorter in sorters)
    if sort_sql:
        sort_sql += ','

    async with SafeExecutor(
            event='browse submissions',
            sql=fr'SELECT *'
                fr'FROM ('
                fr'    SELECT DISTINCT ON (submission.id)'
                fr'           submission.id           AS submission_id,'
                fr'           course.id               AS course_id,'
                fr'           course.name             AS course_name,'
                fr'           class.id                AS class_id,'
                fr'           class.name              AS class_name,'
                fr'           challenge.id            AS challenge_id,'
                fr'           challenge.title         AS challenge_title,'
                fr'           problem.id              AS problem_id,'
                fr'           problem.challenge_label AS challenge_label,'
                fr'           judgment.verdict        AS verdict,'
                fr'           submission.submit_time  AS submit_time,'
                fr'           account.id              AS account_id'
                fr'      FROM submission'
                fr'      LEFT JOIN judgment'
                fr'             ON submission.id = judgment.submission_id'
                fr'      LEFT JOIN problem'
                fr'             ON problem.id = submission.problem_id'
                fr'            AND NOT problem.is_deleted'
                fr'      LEFT JOIN challenge'
                fr'             ON challenge.id = problem.challenge_id'
                fr'            AND NOT challenge.is_deleted'
                fr'      LEFT JOIN class'
                fr'             ON class.id = challenge.class_id'
                fr'            AND NOT class.is_deleted'
                fr'      LEFT JOIN course'
                fr'             ON course.id = class.course_id'
                fr'            AND NOT course.is_deleted'
                fr'      LEFT JOIN account'
                fr'             ON account.id = submission.account_id'
                fr' {f" WHERE {cond_sql}" if cond_sql else ""}'
                fr'     ORDER BY submission.id DESC, judgment.id DESC'
                fr') __TABLE__'
                fr' ORDER BY {sort_sql}'
                fr' LIMIT %(limit)s OFFSET %(offset)s',
            **cond_params,
            limit=limit, offset=offset,
            fetch='all',
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        data = [vo.ViewMySubmission(submission_id=submission_id,
                                    course_id=course_id,
                                    course_name=course_name,
                                    class_id=class_id,
                                    class_name=class_name,
                                    challenge_id=challenge_id,
                                    challenge_title=challenge_title,
                                    problem_id=problem_id,
                                    challenge_label=challenge_label,
                                    verdict=verdict,
                                    submit_time=submit_time,
                                    account_id=account_id)
                for (submission_id, course_id, course_name, class_id, class_name, challenge_id,
                     challenge_title, problem_id, challenge_label, verdict, submit_time, account_id)
                in records]

    total_count = await execute_count(
        sql=fr'SELECT *'
            fr'  FROM view_my_submission'
            fr'{f" WHERE {cond_sql}" if cond_sql else ""}',
        **cond_params,
    )

    return data, total_count


async def my_submission_under_problem(limit: int, offset: int, filters: Sequence[Filter], sorters: Sequence[Sorter]) \
        -> tuple[Sequence[vo.ViewMySubmissionUnderProblem], int]:

    cond_sql, cond_params = compile_filters(filters)
    sort_sql = ' ,'.join(f"{sorter.col_name} {sorter.order}" for sorter in sorters)
    if sort_sql:
        sort_sql += ','

    async with SafeExecutor(
            event='browse my submissions under problem',
            sql=fr'SELECT submission_id, verdict, score, total_time, max_memory, submit_time, account_id, problem_id'
                fr'  FROM view_my_submission_by_problem'
                fr'{f" WHERE {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY {sort_sql} submission_id DESC'
                fr' LIMIT %(limit)s OFFSET %(offset)s',
            **cond_params,
            limit=limit, offset=offset,
            fetch='all',
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        data = [vo.ViewMySubmissionUnderProblem(submission_id=submission_id,
                                                verdict=verdict,
                                                score=score,
                                                total_time=total_time,
                                                max_memory=max_memory,
                                                submit_time=submit_time,
                                                account_id=account_id,
                                                problem_id=problem_id)
                for (submission_id, verdict, score, total_time, max_memory, submit_time, account_id, problem_id)
                in records]

    total_count = await execute_count(
        sql=fr'SELECT *'
            fr'  FROM view_my_submission_by_problem'
            fr'{f" WHERE {cond_sql}" if cond_sql else ""}',
        **cond_params,
    )

    return data, total_count


async def problem_set(limit: int, offset: int, filters: Sequence[Filter], sorters: Sequence[Sorter], ref_time: datetime)\
        -> tuple[Sequence[vo.ViewProblemSet], int]:

    cond_sql, cond_params = compile_filters(filters)
    sort_sql = ' ,'.join(f"{sorter.col_name} {sorter.order}" for sorter in sorters)
    if sort_sql:
        sort_sql += ','

    async with SafeExecutor(
            event='browse problem set',
            sql=fr'SELECT challenge_id, challenge_title, problem_id, '
                fr'       challenge_label, problem_title, class_id'
                fr'  FROM view_problem_set'
                fr'{f" WHERE {cond_sql} AND" if cond_sql else " WHERE "}'
                fr'  CASE WHEN publicize_type = %(start_time)s'
                fr'            THEN start_time <= %(ref_time)s'
                fr'       WHEN publicize_type = %(end_time)s'
                fr'            THEN end_time <= %(ref_time)s'
                fr'   END'
                fr' ORDER BY {sort_sql} problem_id ASC'
                fr' LIMIT %(limit)s OFFSET %(offset)s',
            **cond_params,
            start_time=ChallengePublicizeType.start_time, end_time=ChallengePublicizeType.end_time,
            ref_time=ref_time,
            limit=limit, offset=offset,
            fetch='all',
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        data = [vo.ViewProblemSet(challenge_id=challenge_id,
                                  challenge_title=challenge_title,
                                  problem_id=problem_id,
                                  challenge_label=challenge_label,
                                  problem_title=problem_title,
                                  class_id=class_id)
                for (challenge_id, challenge_title, problem_id, challenge_label, problem_title, class_id)
                in records]

    total_count = await execute_count(
        sql=fr'SELECT *'
            fr'  FROM view_problem_set'
            fr'{f" WHERE {cond_sql}" if cond_sql else ""}',
        **cond_params,
    )

    return data, total_count


async def grade(limit: int, offset: int, filters: Sequence[Filter], sorters: Sequence[Sorter]) \
        -> tuple[Sequence[vo.ViewGrade], int]:

    cond_sql, cond_params = compile_filters(filters)
    sort_sql = ' ,'.join(f"{sorter.col_name} {sorter.order}" for sorter in sorters)
    if sort_sql:
        sort_sql += ','

    async with SafeExecutor(
            event='browse grades under class',
            sql=fr'SELECT account_id, username, student_id, real_name,'
                fr'       title, score, update_time, grade_id, class_id'
                fr'  FROM view_grade'
                fr'{f" WHERE {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY {sort_sql} class_id ASC, grade_id ASC'
                fr' LIMIT %(limit)s OFFSET %(offset)s',
            **cond_params,
            limit=limit, offset=offset,
            fetch='all',
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        data = [vo.ViewGrade(account_id=account_id,
                             username=username,
                             student_id=student_id,
                             real_name=real_name,
                             title=title,
                             score=score,
                             update_time=update_time,
                             grade_id=grade_id,
                             class_id=class_id)
                for (account_id, username, student_id, real_name, title, score, update_time, grade_id, class_id)
                in records]

    total_count = await execute_count(
        sql=fr'SELECT *'
            fr'  FROM view_grade'
            fr'{f" WHERE {cond_sql}" if cond_sql else ""}',
        **cond_params,
    )

    return data, total_count


async def access_log(limit: int, offset: int, filters: Sequence[Filter], sorters: Sequence[Sorter]) \
        -> tuple[Sequence[vo.ViewAccessLog], int]:

    cond_sql, cond_params = compile_filters(filters)
    sort_sql = ' ,'.join(f"{sorter.col_name} {sorter.order}" for sorter in sorters)
    if sort_sql:
        sort_sql += ','

    async with SafeExecutor(
            event='browse access_logs',
            sql=fr'SELECT account_id, username, student_id, real_name, ip, resource_path,'
                fr'       request_method, access_time, access_log_id'
                fr'  FROM view_access_log'
                fr'{f" WHERE {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY {sort_sql} access_log_id ASC'
                fr' LIMIT %(limit)s OFFSET %(offset)s',
            **cond_params,
            limit=limit, offset=offset,
            fetch='all',
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        data = [vo.ViewAccessLog(account_id=account_id,
                                 username=username,
                                 student_id=student_id,
                                 real_name=real_name,
                                 ip=ip,
                                 resource_path=resource_path,
                                 request_method=request_method,
                                 access_time=access_time,
                                 access_log_id=access_log_id)
                for (account_id, username, student_id, real_name, ip, resource_path,
                     request_method, access_time, access_log_id) in records]

    total_count = await execute_count(
        sql=fr'SELECT *'
            fr'  FROM view_access_log'
            fr'{f" WHERE {cond_sql}" if cond_sql else ""}',
        **cond_params,
    )

    return data, total_count