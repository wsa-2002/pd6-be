from typing import Callable

import exceptions as exc

FORMULA_AVAILABLE_PARAMS = [
    'class_max',
    'class_min',
    'baseline',
    'team_score',

    'if',
    'else',
]


async def validate_formula(formula: str) -> bool:
    if not formula:
        return False

    for param in FORMULA_AVAILABLE_PARAMS:
        formula = formula.replace(param, '')

    return not any(char.isalpha() for char in formula)


def get_team_project_calculator(formula: str, class_max: int, class_min: int, baseline: int = 0) \
        -> Callable[[int], float]:
    """
    :return: function that calculate a raw score (int) to actual score (float)
    """
    params = {
        'class_max': class_max,
        'class_min': class_min,
        'baseline': baseline,
    }

    def calculate(raw_score: int) -> float:
        try:
            return eval(formula, params | {'team_score': raw_score})
        except ZeroDivisionError:
            return 0  # Team score will be 0 if divided by zero in formula
        except (TypeError, NameError, SyntaxError):
            raise exc.InvalidFormula

    return calculate


PENALTY_FORMULA_AVAILABLE_PARAMS = [
    'solved_time_mins',
    'wrong_submissions',
]


def validate_penalty_formula(formula: str) -> bool:
    if not formula:
        return False

    for param in PENALTY_FORMULA_AVAILABLE_PARAMS:
        formula = formula.replace(param, '')

    return not any(char.isalpha() for char in formula)


def calculate_penalty(formula: str, solved_time_mins: int, wrong_submissions: int):
    try:
        return eval(formula, {
            'solved_time_mins': solved_time_mins,
            'wrong_submissions': wrong_submissions,
        })
    except ZeroDivisionError:
        raise exc.InvalidFormula
    except (TypeError, NameError, SyntaxError):
        raise exc.InvalidFormula
