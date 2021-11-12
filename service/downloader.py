import io
import zipfile

import const
import log
import persistence.database as db
import persistence.email as email
import persistence.s3 as s3
import util.text
from base import do

ESSAY_FILENAME = 'essay_submission.zip'


async def all_essay(account_id: int, essay_id: int, as_attachment: bool) -> None:
    result = await db.essay_submission.browse_with_essay_id(essay_id=essay_id)
    files = []
    for essay_submission in result:
        s3_file = await db.s3_file.read(s3_file_uuid=essay_submission.content_file_uuid)
        files.append((s3_file, essay_submission.filename))

    zip_buffer = await s3.tools.zipper(files=files)

    s3_file = await s3.temp.put_object(body=zip_buffer.getvalue())

    file_url = await s3.tools.sign_url(bucket=s3_file.bucket, key=s3_file.key,
                                       filename=ESSAY_FILENAME, as_attachment=as_attachment)

    account, student_card = await db.account_vo.read_with_default_student_card(account_id=account_id)
    await email.notification.send_file_download_url(to=student_card.email, file_url=file_url)


async def all_submissions(account_id: int, challenge_id: int, as_attachment: bool) -> None:
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

            submissions = await db.submission.browse_by_problem_selected(problem_id=problem.id,
                                                                         selection_type=challenge.selection_type,
                                                                         end_time=challenge.end_time)
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
        await email.notification.send_file_download_url(to=student_card.email, file_url=file_url,
                                                        subject=f'[PDOGS] All submissions for {challenge.title}')
    if account.alternative_email:
        await email.notification.send_file_download_url(to=account.alternative_email, file_url=file_url,
                                                        subject=f'[PDOGS] All submissions for {challenge.title}')


ASSISTING_DATA_FILENAME = 'assisting_data.zip'


async def all_assisting_data(account_id: int, problem_id: int, as_attachment: bool) -> None:
    result = await db.assisting_data.browse(problem_id=problem_id)
    files = []
    for assisting_data in result:
        s3_file = await db.s3_file.read(s3_file_uuid=assisting_data.s3_file_uuid)
        files.append((s3_file, assisting_data.filename))

    zip_buffer = await s3.tools.zipper(files=files)

    s3_file = await s3.temp.put_object(body=zip_buffer.getvalue())

    file_url = await s3.tools.sign_url(bucket=s3_file.bucket, key=s3_file.key,
                                       filename=ASSISTING_DATA_FILENAME, as_attachment=as_attachment)

    account, student_card = await db.account_vo.read_with_default_student_card(account_id=account_id)
    await email.notification.send_file_download_url(to=student_card.email, file_url=file_url)


SAMPLE_FILENAME = 'sample_testcase.zip'
NON_SAMPLE_FILENAME = 'non_sample_testcase.zip'


async def all_sample_testcase(account_id: int, problem_id: int, as_attachment: bool) -> None:
    result = await db.testcase.browse(problem_id=problem_id, is_sample=True, include_disabled=True)
    files = []
    for testcase in result:
        try:
            input_s3_file = await db.s3_file.read(s3_file_uuid=testcase.input_file_uuid)
            files.append((input_s3_file, testcase.input_filename))
            output_s3_file = await db.s3_file.read(s3_file_uuid=testcase.output_file_uuid)
            files.append((output_s3_file, testcase.output_filename))
        except:
            pass

    zip_buffer = await s3.tools.zipper(files=files)

    s3_file = await s3.temp.put_object(body=zip_buffer.getvalue())

    file_url = await s3.tools.sign_url(bucket=s3_file.bucket, key=s3_file.key,
                                       filename=SAMPLE_FILENAME, as_attachment=as_attachment)

    account, student_card = await db.account_vo.read_with_default_student_card(account_id=account_id)
    await email.notification.send_file_download_url(to=student_card.email, file_url=file_url)


async def all_non_sample_testcase(account_id: int, problem_id: int, as_attachment: bool) -> None:
    result = await db.testcase.browse(problem_id=problem_id, is_sample=False, include_disabled=True)
    files = []
    for testcase in result:
        try:
            input_s3_file = await db.s3_file.read(s3_file_uuid=testcase.input_file_uuid)
            files.append((input_s3_file, testcase.input_filename))
            output_s3_file = await db.s3_file.read(s3_file_uuid=testcase.output_file_uuid)
            files.append((output_s3_file, testcase.output_filename))
        except:
            pass

    zip_buffer = await s3.tools.zipper(files=files)

    s3_file = await s3.temp.put_object(body=zip_buffer.getvalue())

    file_url = await s3.tools.sign_url(bucket=s3_file.bucket, key=s3_file.key,
                                       filename=NON_SAMPLE_FILENAME, as_attachment=as_attachment)

    account, student_card = await db.account_vo.read_with_default_student_card(account_id=account_id)
    await email.notification.send_file_download_url(to=student_card.email, file_url=file_url)
