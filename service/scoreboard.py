from typing import Callable

import exceptions as exc

FORMULA_AVAILABLE_PARAMS = ['class_max', 'class_min', 'baseline', 'team_score']


# TODO: More Validation
async def validate_formula(formula: str) -> bool:
    for param in FORMULA_AVAILABLE_PARAMS:
        formula = formula.replace(param, '')

    return formula is '' or not any(char.isalpha() for char in formula)


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
