import fastapi


def register_routers(app: fastapi.FastAPI):
    """
    A function to register routers without possibility of cyclic import.
    """
    from . import (
        public,

        institute,
        account,
        student_card,

        course,
        class_,
        team,
        grade,

        challenge,

        problem,
        testcase,
        submission,
        judgment,

        # peer_review,

        announcement,
        system,
    )

    app.include_router(public.router)

    app.include_router(institute.router)
    app.include_router(account.router)
    app.include_router(student_card.router)

    app.include_router(course.router)
    app.include_router(class_.router)
    app.include_router(team.router)
    app.include_router(grade.router)

    app.include_router(challenge.router)

    app.include_router(problem.router)
    app.include_router(testcase.router)
    app.include_router(submission.router)
    app.include_router(judgment.router)

    app.include_router(announcement.router)
    app.include_router(system.router)
