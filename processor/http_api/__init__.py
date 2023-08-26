import fastapi


def register_routers(app: fastapi.FastAPI):
    """
    A function to register routers without possibility of cyclic import.
    """
    from . import (
        public,

        s3_file,

        institute,
        account,
        student_card,
        email_verification,

        course,
        class_,
        team,
        grade,

        challenge,

        problem,
        testcase,
        assisting_data,
        submission,
        judgment,

        essay,
        essay_submission,

        peer_review,

        scoreboard,
        scoreboard_setting_team_project,
        scoreboard_setting_team_contest,

        announcement,
        system,

        view,

        hardcode,

        secret,

        docs,
    )

    app.include_router(public.router)

    app.include_router(s3_file.router)

    app.include_router(institute.router)
    app.include_router(account.router)
    app.include_router(student_card.router)
    app.include_router(email_verification.router)

    app.include_router(course.router)
    app.include_router(class_.router)
    app.include_router(team.router)
    app.include_router(grade.router)

    app.include_router(challenge.router)

    app.include_router(problem.router)
    app.include_router(testcase.router)
    app.include_router(assisting_data.router)
    app.include_router(submission.router)
    app.include_router(judgment.router)

    app.include_router(essay.router)
    app.include_router(essay_submission.router)

    app.include_router(peer_review.router)

    app.include_router(scoreboard.router)
    app.include_router(scoreboard_setting_team_project.router)
    app.include_router(scoreboard_setting_team_contest.router)

    app.include_router(announcement.router)
    app.include_router(system.router)

    app.include_router(view.router)

    app.include_router(hardcode.router)

    app.include_router(secret.router)

    docs.hook_docs(app)
