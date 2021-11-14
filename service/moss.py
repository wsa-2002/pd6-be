from typing import Optional

import log
from base import do
from persistence import database as db, s3, moss
import util.text


async def check_all_submissions_moss(title: str, challenge: do.Challenge, problem: do.Problem) -> Optional[str]:
    log.info(f'Downloading all submissions for {problem=}')

    _submission_languages: dict[int, do.SubmissionLanguage] = dict()

    async def get_language_ext(language_id: int) -> str:
        try:
            language = _submission_languages[language_id]
        except KeyError:
            _submission_languages[language_id] = await db.submission.read_language(language_id)
            language = _submission_languages[language_id]

        # return language.file_extension
        return 'py' if language.name.lower().startswith('py') else 'cpp'  # FIXME: put into db

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
        return None

    log.info(f'submitting moss {problem.id=}')

    # fixme: hardcoded
    moss_language = 'python' if (sum(filename.endswith('py') for filename in submission_files)
                                 > sum(filename.endswith('cpp') for filename in submission_files)) else 'cc'
    report_url = await moss.submit_report(moss.MossOptions(
        submission_files,
        language=moss_language,
        directory_mode=False,
        base_files={},
        ignore_threshold=max(10, len(submission_files) // 5),
        subtitle=title,
        max_results=max(100, len(submission_files) // 2),
    ))

    return report_url
