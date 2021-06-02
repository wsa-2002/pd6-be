import fastapi


def register_routers(app: fastapi.FastAPI):
    """
    A function to register routers without possibility of cyclic import.
    """
    from . import (
        public,
        account_control,
        # administrative,
        # challenge_problem,
        course,
        class_,
        team,
        # submission,
        # system,
    )

    app.include_router(public.router)
    app.include_router(account_control.router)
    # app.include_router(administrative.router)
    # app.include_router(challenge_problem.router)
    app.include_router(course.router)
    app.include_router(class_.router)
    app.include_router(team.router)
    # app.include_router(submission.router)
    # app.include_router(system.router)
