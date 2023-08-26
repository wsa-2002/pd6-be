import io
import zipfile

import log
import persistence.database as db
import persistence.s3 as s3
import util.text
from base import do

from . import moss


async def all_essay_submissions(essay_id: int) -> do.S3File:
    log.info(f'Downloading all essay submissions for {essay_id=}')

    essay_submissions = await db.essay_submission.browse_with_essay_id(essay_id=essay_id)
    files = {
        essay_submission.filename: await db.s3_file.read(s3_file_uuid=essay_submission.content_file_uuid)
        for essay_submission in essay_submissions
    }

    zip_buffer = await s3.tools.zipper(files=files)

    s3_file = await s3.temp.put_object(body=zip_buffer.getvalue())

    return s3_file


async def all_submissions(challenge_id: int) -> do.S3File:
    log.info(f'Downloading all submissions for {challenge_id=}')

    challenge = await db.challenge.read(challenge_id)
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

    log.info('Create zip...')

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

    log.info('Make s3 file...')

    s3_file = await s3.temp.put_object(body=zip_buffer.getvalue())
    return s3_file


async def all_assisting_data(problem_id: int) -> do.S3File:
    assisting_datas = await db.assisting_data.browse(problem_id=problem_id)
    files = {
        assisting_data.filename: await db.s3_file.read(s3_file_uuid=assisting_data.s3_file_uuid)
        for assisting_data in assisting_datas
    }

    zip_buffer = await s3.tools.zipper(files=files)

    s3_file = await s3.temp.put_object(body=zip_buffer.getvalue())
    return s3_file


async def all_testcase(problem_id: int, is_sample: bool) -> do.S3File:
    testcases = await db.testcase.browse(problem_id=problem_id, is_sample=is_sample, include_disabled=True)
    input_files = {
        testcase.input_filename: await db.s3_file.read(s3_file_uuid=testcase.input_file_uuid)
        for testcase in testcases
        if testcase.input_file_uuid
    }
    output_files = {
        testcase.output_filename: await db.s3_file.read(s3_file_uuid=testcase.output_file_uuid)
        for testcase in testcases
        if testcase.output_file_uuid
    }

    zip_buffer = await s3.tools.zipper(files=input_files | output_files)

    s3_file = await s3.temp.put_object(body=zip_buffer.getvalue())
    return s3_file


async def moss_report(report_url: str) -> do.S3File:
    log.info(f'downloading report for moss {report_url=}')

    report_index_file, other_files = await moss.download_report(report_url, sub_folder='files')

    log.info(f'generating report zipfile for moss {report_url=}')

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_STORED, False) as zipper:
        zipper.writestr('index.html', report_index_file)
        for filename, file in other_files.items():
            zipper.writestr(filename, file)

    log.info(f'Make report s3 file for moss {report_url=}')

    s3_file = await s3.temp.put_object(body=zip_buffer.getvalue())
    return s3_file
