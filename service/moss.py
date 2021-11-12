import io
import zipfile

import const
import log
from base import do
from persistence import database as db, s3, email, moss
import util.text


async def check_all_submissions_moss(account_id: int, challenge_id: int, as_attachment: bool) -> None:
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

    account, student_card = await db.account_vo.read_with_default_student_card(account_id=account_id)

    log.info(f'Create zip...')
    for problem in problems:
        log.info(f'preparing for moss {problem.id=}')
        submission_files = dict()

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
            submission_files[filename] = await s3.tools.get_file_content_from_do(s3_file)

        if not submission_files:
            log.info(f'No submission files found for moss task {problem.id=}')
            continue

        log.info(f'submitting moss {problem.id=}')

        # fixme: hardcoded
        moss_language = 'python' if (sum(filename.endswith('py') for filename in submission_files)
                                     > sum(filename.endswith('cpp') for filename in submission_files)) else 'cc'
        problem_title = challenge.title + ' ' + problem.challenge_label
        report_url = await moss.submit_report(moss.MossOptions(
            submission_files,
            language=moss_language,
            directory_mode=False,
            base_files={},
            ignore_threshold=max(10, len(submission_files) // 5),
            subtitle=problem_title,
            max_results=max(100, len(submission_files) // 2),
        ))

        if not report_url:
            log.error(f"{report_url=} for moss task {problem.id=} {account.id=}")
            continue

        log.info(f'send to email for moss {problem.id=}')

        if student_card.email:
            await email.notification.send(to=student_card.email,
                                          subject=f'[PDOGS] Plagiarism report for {problem_title}',
                                          msg=f'Plagiarism report for {problem_title}: {report_url}')
        if account.alternative_email:
            await email.notification.send(to=account.alternative_email,
                                          subject=f'[PDOGS] Plagiarism report for {problem_title}',
                                          msg=f'Plagiarism report for {problem_title}: {report_url}')

        log.info(f'downloading report for moss {problem.id=}')

        report_index_file, other_files = await moss.download_report(report_url, sub_folder='files')

        log.info(f'generating report zipfile for moss {problem.id=}')

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_STORED, False) as zipper:
            zipper.writestr('index.html', report_index_file)
            for filename, file in other_files.items():
                zipper.writestr(filename, file)

        log.info(f'Make report s3 file for moss {problem.id=}')

        s3_file = await s3.temp.put_object(body=zip_buffer.getvalue())

        file_url = await s3.tools.sign_url(
            bucket=s3_file.bucket, key=s3_file.key,
            expire_secs=const.SUBMISSION_PACKAGE_S3_EXPIRE_SECS,
            filename=util.text.get_valid_filename(f'{challenge.title}_plagiarism_report.zip'),
            as_attachment=as_attachment,
        )

        log.info(f'Send report to email for moss {problem.id=}')

        account, student_card = await db.account_vo.read_with_default_student_card(account_id=account_id)
        if student_card.email:
            await email.notification.send_file_download_url(
                to=student_card.email,
                file_url=file_url,
                subject=f'[PDOGS] Plagiarism report file for {problem_title}',
            )
        if account.alternative_email:
            await email.notification.send_file_download_url(
                to=account.alternative_email,
                file_url=file_url,
                subject=f'[PDOGS] Plagiarism report file for {problem_title}',
            )
