from textwrap import indent
import typing


def to_collapsible(content="", title="", open_=False):
    content = content.strip('\n')
    content_indent = ' ' * (len(content) - len(content.lstrip(' ')))
    return f"""<details{" open" if open_ else ""}><summary>{title}</summary>
{content_indent}</p>
{content_indent}
{content}
{content_indent}
{content_indent}</p>
</details>
"""


def all_docs():
    return f"""
{to_collapsible(title="**Error codes**", content=gen_err_doc())}
{to_collapsible(title="**Enums**", content=gen_enum_doc())}
""".strip()


def _get_members(module, base_cls):
    import inspect
    return inspect.getmembers(module, lambda obj: inspect.isclass(obj)
                                                  and issubclass(obj, base_cls)
                                                  and obj is not base_cls)


def gen_enum_doc():
    return f"""
{_gen_enum_doc()}
"""


def _gen_enum_doc():
    """
    [collapsible] Enum Cls:
        - enum val1
        - enum val2
    """
    from base import cls, enum
    return '\n'.join('- ' + to_collapsible(title=f"`{name}`",
                                           content="\n".join(indent(f"- `{enum_obj._value_}`: {enum_obj._name_}", '  ')
                                                             for enum_obj in enum_cls))
                     for name, enum_cls in _get_members(enum, cls.enum.Enum)
                     if len(enum_cls) > 0)


def gen_err_doc():
    import exceptions
    from exceptions import account, persistence

    modules = (exceptions, account, persistence)

    return f"""
{to_collapsible(title=f"`{exceptions.SystemException.__name__}`: {exceptions.SystemException.__doc__}",
                content=_gen_err_doc(modules, exceptions.SystemException))}

{to_collapsible(title=f"`{exceptions.PdogsException.__name__}`: {exceptions.PdogsException.__doc__}",
                content=_gen_err_doc(modules, exceptions.PdogsException))}
"""


def _gen_err_doc(modules, base_cls):
    item_docs = []
    for module in modules:
        item_doc = '\n'.join(f"- `{name}`: {cls.__doc__}"
                             for name, cls in _get_members(module, base_cls))
        if item_doc:
            item_docs.append(f"#### {module.__name__.split('.', maxsplit=1)[-1].title()}\n{indent(item_doc, '  ')}")

    return '\n'.join(item_docs)


_T = typing.TypeVar('_T')
_P = typing.ParamSpec('_P')
_AsyncFunc = typing.Callable[_P, typing.Awaitable[_T]]


def add_to_docstring(doc) -> typing.Callable[[_AsyncFunc], _AsyncFunc]:
    """
    Add stuff to docstring.
    """
    def decorator(func: _AsyncFunc) -> _AsyncFunc:
        func.__doc__ += str(doc)
        return func

    return decorator
