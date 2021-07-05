from dataclasses import dataclass
import functools
import typing

import fastapi

import exceptions as exc
import log


def _make_enveloped_annotations(func):
    """
    Returns annotation with the return annotation enveloped
    """

    if original := func.__annotations__.get('return', None):
        new_return_annotation = {
            'success': bool,
            'data': original,
            'error': typing.Optional[str],
        }
    else:  # return is None -> no data
        new_return_annotation = {
            'success': bool,
            'error': typing.Optional[str],
        }

    # Create a model dataclass for return type annotation

    return_model_name = f"{func.__name__}_return"
    return_annotation_dict = {
        '__module__': func.__module__,
        '__qualname__': return_model_name,
        '__annotations__': new_return_annotation,
    }
    return_type = type(return_model_name, (), return_annotation_dict)
    return_type = dataclass()(return_type)

    new_annotations = dict(**func.__annotations__)
    new_annotations['return'] = return_type

    return new_annotations


_WRAPPER_ASSIGNMENTS = ('__module__', '__name__', '__qualname__', '__doc__')  # All except '__annotations__'
_WRAPPER_UPDATES = functools.WRAPPER_UPDATES


def enveloped(func):
    """
    Add envelope and handle error.
    """

    async def wrapped(*args, **kwargs):
        try:
            data = await func(*args, **kwargs)
        except Exception as e:
            return {
                'success': False,
                'data': None,
                'error': _handle_exc(e).__class__.__name__,
            }
        else:
            return {
                'success': True,
                'data': data,
                'error': None,
            }

    setattr(wrapped, '__annotations__', _make_enveloped_annotations(func))
    functools.update_wrapper(wrapped, func, _WRAPPER_ASSIGNMENTS, _WRAPPER_UPDATES)

    return wrapped


async def _handle_exc(error: Exception) -> Exception:
    # Convert pydantic-originated ValidationError to self-defined error
    if isinstance(error, fastapi.exceptions.ValidationError):
        error = exc.IllegalInput(cause=error)

    # Log the exception
    if isinstance(error, exc.PdogsException):
        log.exception(error, info_level=True)
    else:
        log.exception(error, info_level=False)
        error = exc.SystemException(cause=error)

    return error
