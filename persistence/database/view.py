from typing import Sequence
from datetime import datetime

from base import vo
from base.enum import SortOrder, FilterOperator, ChallengePublicizeType, RoleType
from base.popo import Filter, Sorter

from .base import FetchAll
from .util import execute_count, compile_filters


async def account(limit: int, offset: int, filters: list[Filter], sorters: list[Sorter]) \
        -> tuple[Sequence[vo.ViewAccount], int]:
    column_mapper = {
        'account_id': 'account.id',
        'username': 'account.username',
        'student_id': 'student_card.student_id',
        'real_name': 'account.real_name',
    }
    filters = [Filter(col_name=column_mapper[f.col_name], op=f.op, value=f.value) for f in filters]

    cond_sql, cond_params = compile_filters(filters)
    view_sql = (fr'SELECT account.id              AS account_id,'
                fr'       account.username        AS username,'
                fr'       student_card.student_id AS student_id,'
                fr'       account.real_name       AS real_name'
                fr'  FROM account'
                fr'  LEFT JOIN student_card'
                fr'         ON student_card.account_id = account.id'
                fr'        AND student_card.is_default'
                fr' WHERE NOT account.is_deleted'
                fr'{f" AND {cond_sql}" if cond_sql else ""}')
    sort_sql = ' ,'.join(f"{sorter.col_name} {sorter.order}" for sorter in sorters)

    async with FetchAll(
            event='browse account with default student card',
            sql=fr'{view_sql}'
                fr' ORDER BY {sort_sql + "," if sort_sql else ""} account_id ASC'
                fr' LIMIT %(limit)s OFFSET %(offset)s',
            **cond_params,
            limit=limit, offset=offset,
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        data = [vo.ViewAccount(account_id=account_id,
                               username=username,
                               real_name=real_name,
                               student_id=student_id)
                for (account_id, username, student_id, real_name) in records]

    total_count = await execute_count(view_sql, **cond_params)

    return data, total_count


async def class_member(limit: int, offset: int, filters: Sequence[Filter], sorters: Sequence[Sorter]) \
        -> tuple[Sequence[vo.ViewClassMember], int]:
    column_mapper = {
        'account_id': 'class_member.member_id',
        'username': 'account.username',
        'student_id': 'student_card.student_id',
        'real_name': 'account.real_name',
        'abbreviated_name': 'institute.abbreviated_name',
        'role': 'class_member.role',
        'class_id': 'class_member.class_id',
    }
    filters = [Filter(col_name=column_mapper[f.col_name], op=f.op, value=f.value) for f in filters]

    sorters += [Sorter(col_name='role',
                       order=SortOrder.desc)]

    cond_sql, cond_params = compile_filters(filters)
    view_sql = (fr'SELECT class_member.member_id     AS account_id,'
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
                fr'{f" WHERE {cond_sql}" if cond_sql else ""}')
    sort_sql = ' ,'.join(f"{sorter.col_name} {sorter.order}" for sorter in sorters)

    async with FetchAll(
            event='browse class members with student card',
            sql=fr'{view_sql}'
                fr' ORDER BY {sort_sql + "," if sort_sql else ""} account_id ASC'
                fr' LIMIT %(limit)s OFFSET %(offset)s',
            **cond_params,
            limit=limit, offset=offset,
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

    total_count = await execute_count(view_sql, **cond_params)

    return data, total_count


async def class_submission(class_id: int, limit: int, offset: int,
                           filters: Sequence[Filter], sorters: Sequence[Sorter]) \
        -> tuple[Sequence[vo.ViewSubmissionUnderClass], int]:
    column_mapper = {
        'submission_id': 'submission.id',
        'account_id': 'account.id',
        'username': 'account.username',
        'student_id': 'student_card.student_id',
        'real_name': 'account.real_name',
        'challenge_id': 'problem.challenge_id',
        'challenge_title': 'challenge.title',
        'problem_id': 'problem.id',
        'challenge_label': 'problem.challenge_label',
        'verdict': 'judgment.verdict',
        'submit_time': 'submission.submit_time',
        'class_id': 'challenge.class_id',
    }
    filters = [Filter(col_name=column_mapper[f.col_name], op=f.op, value=f.value) for f in filters]

    filters += [Filter(col_name='class_id',
                       op=FilterOperator.eq,
                       value=class_id)]

    cond_sql, cond_params = compile_filters(filters)
    sort_sql = ' ,'.join(f"{sorter.col_name} {sorter.order}" for sorter in sorters)

    view_sql = (fr'SELECT *'
                fr'FROM ('
                fr'    SELECT submission.id           AS submission_id,'
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
                fr'     INNER JOIN problem'
                fr'             ON problem.id = submission.problem_id'
                fr'            AND NOT problem.is_deleted'
                fr'     INNER JOIN challenge'
                fr'             ON challenge.id = problem.challenge_id'
                fr'            AND NOT challenge.is_deleted'
                fr'      LEFT JOIN judgment'
                fr'             ON judgment.submission_id = submission.id'
                fr'            AND judgment.id = submission_last_judgment_id(submission.id)'
                fr'    {f" WHERE {cond_sql}" if cond_sql else ""}'
                fr'     ORDER BY submission.submit_time DESC, submission.id DESC'
                fr') __TABLE__')
    async with FetchAll(
            event='browse class submissions',
            sql=fr'{view_sql}'
                fr'{f" ORDER BY {sort_sql}" if sort_sql else ""}'
                fr' LIMIT %(limit)s OFFSET %(offset)s',
            **cond_params,
            limit=limit, offset=offset,
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

    total_count = await execute_count(sql=view_sql, **cond_params)

    return data, total_count


async def my_submission(limit: int, offset: int, filters: Sequence[Filter], sorters: Sequence[Sorter]) \
        -> tuple[Sequence[vo.ViewMySubmission], int]:
    column_mapper = {
        'submission_id': 'submission.id',
        'course_id': 'course.id',
        'course_name': 'course.name',
        'class_id': 'class.id',
        'class_name': 'class.name',
        'challenge_id': 'challenge.id',
        'challenge_title': 'challenge.title',
        'problem_id': 'problem.id',
        'challenge_label': 'problem.challenge_label',
        'verdict': 'judgment.verdict',
        'submit_time': 'submission.submit_time',
        'account_id': 'account.id',
    }
    filters = [Filter(col_name=column_mapper[f.col_name], op=f.op, value=f.value) for f in filters]

    cond_sql, cond_params = compile_filters(filters)
    view_sql = (fr'SELECT *'
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
                fr') __TABLE__')
    sort_sql = ' ,'.join(f"{sorter.col_name} {sorter.order}" for sorter in sorters)

    async with FetchAll(
            event='browse my submissions',
            sql=fr'{view_sql}'
                fr'{f" ORDER BY {sort_sql}" if sort_sql else ""}'
                fr' LIMIT %(limit)s OFFSET %(offset)s',
            **cond_params,
            limit=limit, offset=offset,
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

    total_count = await execute_count(view_sql, **cond_params)

    return data, total_count


async def my_submission_under_problem(limit: int, offset: int, filters: Sequence[Filter], sorters: Sequence[Sorter]) \
        -> tuple[Sequence[vo.ViewMySubmissionUnderProblem], int]:
    column_mapper = {
        'submission_id': 'submission.id',
        'judgment_id': 'judgment.id',
        'verdict': 'judgment.verdict',
        'score': 'judgment.score',
        'total_time': 'judgment.total_time',
        'max_memory': 'judgment.max_memory',
        'submit_time': 'submission.submit_time',
        'account_id': 'submission.account_id',
        'problem_id': 'submission.problem_id',
    }
    filters = [Filter(col_name=column_mapper[f.col_name], op=f.op, value=f.value) for f in filters]

    cond_sql, cond_params = compile_filters(filters)
    view_sql = (fr'SELECT * '
                fr'FROM ('
                fr'    SELECT DISTINCT ON (submission.id)'
                fr'           submission.id           AS submission_id,'
                fr'           judgment.id             AS judgment_id,'
                fr'           judgment.verdict        AS verdict,'
                fr'           judgment.score          AS score,'
                fr'           judgment.total_time     AS total_time,'
                fr'           judgment.max_memory     AS max_memory,'
                fr'           submission.submit_time  AS submit_time,'
                fr'           submission.account_id   AS account_id,'
                fr'           submission.problem_id   AS problem_id'
                fr'      FROM submission'
                fr'      LEFT JOIN judgment'
                fr'             ON submission.id = judgment.submission_id'
                fr' {f" WHERE {cond_sql}" if cond_sql else ""}'
                fr'     ORDER BY submission.id DESC, judgment.id DESC'
                fr') __TABLE__')
    sort_sql = ' ,'.join(f"{sorter.col_name} {sorter.order}" for sorter in sorters)

    async with FetchAll(
            event='browse my submission under problem',
            sql=fr'{view_sql}'
                fr'{f" ORDER BY {sort_sql}" if sort_sql else ""}'
                fr' LIMIT %(limit)s OFFSET %(offset)s',
            **cond_params,
            limit=limit, offset=offset,
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        data = [vo.ViewMySubmissionUnderProblem(submission_id=submission_id,
                                                judgment_id=judgment_id,
                                                verdict=verdict,
                                                score=score,
                                                total_time=total_time,
                                                max_memory=max_memory,
                                                submit_time=submit_time,
                                                account_id=account_id,
                                                problem_id=problem_id)
                for (submission_id, judgment_id, verdict, score, total_time,
                     max_memory, submit_time, account_id, problem_id)
                in records]

    total_count = await execute_count(view_sql, **cond_params)

    return data, total_count


async def problem_set(
    limit: int, offset: int,
    filters: Sequence[Filter], sorters: Sequence[Sorter], ref_time: datetime,
) -> tuple[Sequence[vo.ViewProblemSet], int]:
    cond_sql, cond_params = compile_filters(filters)
    sort_sql = ' ,'.join(f"{sorter.col_name} {sorter.order}" for sorter in sorters)
    if sort_sql:
        sort_sql += ','

    async with FetchAll(
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
            fr'{f" WHERE {cond_sql} AND" if cond_sql else " WHERE "}'
            fr'  CASE WHEN publicize_type = %(start_time)s'
            fr'            THEN start_time <= %(ref_time)s'
            fr'       WHEN publicize_type = %(end_time)s'
            fr'            THEN end_time <= %(ref_time)s'
            fr'   END',
        **cond_params,
        start_time=ChallengePublicizeType.start_time, end_time=ChallengePublicizeType.end_time,
        ref_time=ref_time,
    )

    return data, total_count


async def grade(limit: int, offset: int, filters: Sequence[Filter], sorters: Sequence[Sorter]) \
        -> tuple[Sequence[vo.ViewGrade], int]:
    cond_sql, cond_params = compile_filters(filters)
    sort_sql = ' ,'.join(f"{sorter.col_name} {sorter.order}" for sorter in sorters)

    view_sql = (fr'SELECT * '
                fr'FROM ('
                fr'    SELECT grade.receiver_id AS account_id,'
                fr'           account.username,'
                fr'           student_card.student_id,'
                fr'           account.real_name,'
                fr'           grade.title,'
                fr'           grade.score,'
                fr'           grade.update_time,'
                fr'           grade.id AS grade_id,'
                fr'           grade.class_id'
                fr'      FROM grade'
                fr'      JOIN account'
                fr'        ON account.id = grade.receiver_id'
                fr'       AND NOT account.is_deleted'
                fr'      LEFT JOIN student_card '
                fr'        ON student_card.account_id = grade.receiver_id '
                fr'       AND student_card.is_default'
                fr'     WHERE NOT grade.is_deleted'
                fr'{f" AND {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY class_id ASC, grade_id ASC'
                fr') __TABLE__')
    async with FetchAll(
            event='browse grades under class',
            sql=fr'{view_sql}'
                fr'{f" ORDER BY {sort_sql}, grade_id ASC" if sort_sql else ""}'
                fr' LIMIT %(limit)s OFFSET %(offset)s',
            **cond_params,
            limit=limit, offset=offset,
            raise_not_found=False,
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

    total_count = await execute_count(view_sql, **cond_params)

    return data, total_count


async def access_log(limit: int, offset: int, filters: Sequence[Filter], sorters: Sequence[Sorter]) \
        -> tuple[Sequence[vo.ViewAccessLog], int]:
    column_mapper = {
        'account_id': 'account.id',
        'username': 'account.username',
        'student_id': 'student_card.student_id',
        'real_name': 'account.real_name',
        'ip': 'access_log.ip',
        'resource_path': 'access_log.resource_path',
        'request_method': 'access_log.request_method',
        'access_time': 'access_log.access_time',
        'access_log_id': 'access_log.id',
    }
    filters = [Filter(col_name=column_mapper[f.col_name], op=f.op, value=f.value) for f in filters]

    cond_sql, cond_params = compile_filters(filters)
    sort_sql = ' ,'.join(f"{sorter.col_name} {sorter.order}" for sorter in sorters)
    if sort_sql:
        sort_sql += ','

    async with FetchAll(
            event='browse access_logs',
            sql=fr'SELECT account.id                AS account_id,'
                fr'       account.username          AS username,'
                fr'       student_card.student_id   AS student_id,'
                fr'       account.real_name         AS real_name,'
                fr'       access_log.ip             AS ip,'
                fr'       access_log.resource_path  AS resource_path,'
                fr'       access_log.request_method AS request_method,'
                fr'       access_log.access_time    AS access_time,'
                fr'       access_log.id             AS access_log_id'
                fr'  FROM access_log'
                fr'  LEFT JOIN account'
                fr'         ON account.id = access_log.account_id'
                fr'  LEFT JOIN student_card'
                fr'         ON student_card.account_id = account.id'
                fr'        AND student_card.is_default'
                fr'{f" WHERE {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY {sort_sql} access_log_id DESC'
                fr' LIMIT %(limit)s OFFSET %(offset)s',
            **cond_params,
            limit=limit, offset=offset,
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
            fr'  FROM access_log'
            fr'  LEFT JOIN account'
            fr'         ON account.id = access_log.account_id'
            fr'  LEFT JOIN student_card'
            fr'         ON student_card.account_id = account.id'
            fr'        AND student_card.is_default'
            fr'{f" WHERE {cond_sql}" if cond_sql else ""}',
        use_estimate_if_rows=offset+10000,
        **cond_params,
    )

    return data, total_count


async def view_peer_review_record(
        peer_review_id: int, limit: int, offset: int,
        filters: Sequence[Filter], sorters: Sequence[Sorter],
        is_receiver: bool, class_role=RoleType.normal,
) -> tuple[Sequence[vo.ViewPeerReviewRecord], int]:
    column_mapper = {
        'account_id': 'account.id',
        'username': 'account.username',
        'real_name': 'account.real_name',
        'student_id': 'student_card.student_id',
        'average_score': 'AVG(peer_review_record.score)',
    }
    filters = [Filter(col_name=column_mapper[f.col_name], op=f.op, value=f.value) for f in filters]

    cond_sql, cond_params = compile_filters(filters)
    sort_sql = ' ,'.join(f"{sorter.col_name} {sorter.order}" for sorter in sorters)
    if sort_sql:
        sort_sql += ','

    async with FetchAll(
            event=f'view peer review record by {"receiver" if is_receiver else "grader"}',
            sql=fr'SELECT account.id                          AS account_id,'
                fr'       account.username                    AS username,'
                fr'       account.real_name                   AS real_name,'
                fr'       student_card.student_id             AS student_id,'
                fr'       ARRAY_AGG(peer_review_record.id)    AS ids,'
                fr'       ARRAY_AGG(peer_review_record.score) AS scores,'
                fr'       AVG(peer_review_record.score)       AS average_score'
                fr'  FROM class_member'
                fr' INNER JOIN account'
                fr'         ON account.id = class_member.member_id'
                fr'        AND NOT account.is_deleted '
                fr'  LEFT JOIN student_card'
                fr'         ON student_card.account_id = account.id'
                fr'        AND student_card.is_default '
                fr'  LEFT JOIN peer_review_record'
                fr'         ON class_member.member_id = peer_review_record.{"receiver_id" if is_receiver else "grader_id"}'
                fr'        AND peer_review_record.peer_review_id = %(peer_review_id)s'
                fr' WHERE class_id = (SELECT challenge.class_id '
                fr'                     FROM peer_review'
                fr'                     LEFT JOIN challenge'
                fr'                            ON peer_review.challenge_id = challenge.id'
                fr'                           AND NOT challenge.is_deleted'
                fr'                    WHERE peer_review.id = %(peer_review_id)s)'
                fr'   AND class_member.role = %(class_role)s'
                fr'{f" AND {cond_sql}" if cond_sql else ""}'
                fr' GROUP BY account.id, student_card.student_id'
                fr' ORDER BY {sort_sql} account.id ASC'
                fr' LIMIT %(limit)s OFFSET %(offset)s',
                **cond_params, peer_review_id=peer_review_id, class_role=class_role,
                limit=limit, offset=offset,
                raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        data = [vo.ViewPeerReviewRecord(account_id=account_id,
                                        username=username,
                                        real_name=real_name,
                                        student_id=student_id,
                                        peer_review_record_ids=record_ids,
                                        peer_review_record_scores=record_scores,
                                        average_score=average_score)
                for (account_id, username, real_name, student_id, record_ids, record_scores, average_score) in records]

    total_count = await execute_count(
        sql=fr'SELECT account.id, account.username'
            fr'  FROM class_member'
            fr' INNER JOIN account'
            fr'         ON account.id = class_member.member_id'
            fr'        AND NOT account.is_deleted '
            fr'  LEFT JOIN student_card'
            fr'         ON student_card.account_id = account.id'
            fr'        AND student_card.is_default '
            fr'  LEFT JOIN peer_review_record'
            fr'         ON class_member.member_id = peer_review_record.{"receiver_id" if is_receiver else "grader_id"}'
            fr'        AND peer_review_record.peer_review_id = %(peer_review_id)s'
            fr' WHERE class_id = (SELECT challenge.class_id '
            fr'                     FROM peer_review'
            fr'                     LEFT JOIN challenge'
            fr'                            ON peer_review.challenge_id = challenge.id'
            fr'                           AND NOT challenge.is_deleted'
            fr'                    WHERE peer_review.id = %(peer_review_id)s)'
            fr'   AND class_member.role = %(class_role)s'
            fr'{f" AND {cond_sql}" if cond_sql else ""}'
            fr' GROUP BY account.id, student_card.student_id',
        **cond_params, peer_review_id=peer_review_id, class_role=class_role,
    )

    return data, total_count
