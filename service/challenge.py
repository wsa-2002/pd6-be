import io
import zipfile
from typing import Tuple, Sequence

import const
import log
from base import do
from base.enum import RoleType
import exceptions as exc
from persistence import database as db, s3, email
import util.text


add = db.challenge.add
browse = db.challenge.browse
read = db.challenge.read
edit = db.challenge.edit
delete = db.challenge.delete_cascade


async def browse_task(challenge_id: int) -> Tuple[
    Sequence[do.Problem],
    Sequence[do.PeerReview],
    Sequence[do.Essay]
]:
    problems = []
    try:
        problems = await db.problem.browse_by_challenge(challenge_id=challenge_id)
    except exc.persistence.NotFound:
        pass

    peer_reviews = []
    try:
        peer_reviews = await db.peer_review.browse_by_challenge(challenge_id=challenge_id)
    except exc.persistence.NotFound:
        pass

    essays = []
    try:
        essays = await db.essay.browse_by_challenge(challenge_id=challenge_id)
    except exc.persistence.NotFound:
        pass

    return problems, peer_reviews, essays


async def browse_task_status(challenge_id: int, account_id: int) \
        -> Sequence[Tuple[do.Problem, do.Submission]]:
    challenge = await db.challenge.read(challenge_id=challenge_id, include_scheduled=True)
    problems = await db.problem.browse_by_challenge(challenge_id=challenge_id)

    return [await db.problem.read_task_status_by_type(
        problem_id=problem.id,
        selection_type=challenge.selection_type,
        challenge_end_time=challenge.end_time,
        account_id=account_id)
            for problem in problems]


async def get_challenge_statistics(challenge_id: int) -> Sequence[Tuple[str, int, int, int]]:
    problems = await db.problem.browse_by_challenge(challenge_id)
    return [(problem.challenge_label,
             await db.problem.total_ac_member_count(problem.id),
             await db.problem.total_submission_count(problem.id),
             await db.problem.total_member_count(problem.id))
            for problem in problems]


async def get_member_submission_statistics(challenge_id: int) \
        -> Sequence[Tuple[int, Sequence[tuple[int, do.Judgment]], Sequence[do.EssaySubmission]]]:
    """
    :return: [id, [problem_id, judgment], [essay_submission]]
    """

    challenge = await db.challenge.read(challenge_id, include_scheduled=True)
    class_members = await db.class_.browse_members(class_id=challenge.class_id)
    problems = await db.problem.browse_by_challenge(challenge_id=challenge_id)
    essays = await db.essay.browse_by_challenge(challenge_id=challenge_id)

    problem_to_member_judgments = {
        problem.id: await db.judgment.browse_by_problem_class_members(problem_id=problem.id,
                                                                      selection_type=challenge.selection_type)
        for problem in problems
    }

    essay_to_member_essay_submissions = {
        essay.id: await db.essay_submission.browse_by_essay_class_members(essay_id=essay.id)
        for essay in essays
    }

    result = []
    for class_member in class_members:
        if class_member.role != RoleType.normal:
            continue

        problem_judgments = []
        for problem in problems:
            try:
                judgment = problem_to_member_judgments[problem.id][class_member.member_id]
            except KeyError:
                pass
            else:
                problem_judgments.append((problem.id, judgment))

        essay_submissions = []
        for essay in essays:
            try:
                essay_submission = essay_to_member_essay_submissions[essay.id][class_member.member_id]
            except KeyError:
                pass
            else:
                essay_submissions.append(essay_submission)

        result.append((class_member.member_id, problem_judgments, essay_submissions))

    return result


async def download_all_submissions(account_id: int, challenge_id: int, as_attachment: bool) -> None:
    log.info(f'Downloading all submissions for {account_id=} {challenge_id=}')

    challenge = await db.challenge.read(challenge_id, include_scheduled=True)
    problems = await db.problem.browse_by_challenge(challenge_id=challenge_id)

    _submission_languages: dict[int, do.SubmissionLanguage] = dict()

    async def get_language_ext(language_id: int) -> str:
        try:
            language = _submission_languages[language_id]
        except KeyError:
            _submission_languages[language_id] = await db.submission.read_language(language_id)
            language = _submission_languages[language_id]

        # return language.file_extension
        return 'py' if language.name.lower().startswith('py') else 'cpp'  # FIXME: put into db

    log.info(f'Create zip...')

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_STORED, False) as zipper:
        for problem in problems:
            problem_folder_name = util.text.get_valid_filename(problem.challenge_label)

            submissions = await db.submission.browse_by_problem_class_members(problem_id=problem.id,
                                                                              selection_type=challenge.selection_type)
            account_referrals = await db.account.browse_referral_wth_ids(submission.account_id
                                                                         for submission in submissions)
            s3_files = await db.s3_file.browse_with_uuids(submission.content_file_uuid for submission in submissions)

            for referral, submission, s3_file in zip(account_referrals, submissions, s3_files):
                if not referral or not s3_file:
                    continue
                file_ext = await get_language_ext(submission.language_id)
                filename = util.text.get_valid_filename(f'{referral}.{file_ext}')
                zipper.writestr(f'{problem_folder_name}/{filename}',
                                data=await s3.tools.get_file_content_from_do(s3_file))

    log.info(f'Make s3 file...')

    s3_file = await s3.temp.put_object(body=zip_buffer.getvalue())

    file_url = await s3.tools.sign_url(bucket=s3_file.bucket, key=s3_file.key,
                                       expire_secs=const.SUBMISSION_PACKAGE_S3_EXPIRE_SECS,
                                       filename=util.text.get_valid_filename(f'{challenge.title}.zip'),
                                       as_attachment=as_attachment)

    log.info(f'Send to email...')

    account, student_card = await db.account_vo.read_with_default_student_card(account_id=account_id)
    if student_card.email:
        await email.notification.send_file_download_url(to=student_card.email, file_url=file_url)
    if account.alternative_email:
        await email.notification.send_file_download_url(to=account.alternative_email, file_url=file_url)
