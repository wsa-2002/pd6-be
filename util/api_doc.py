from textwrap import indent


def to_collapsible(content="", title=""):
    return f"""
<details>
<summary>{title}</summary>
</p>

{content.strip()}

</p>
</details>
"""


def gen_err_doc():
    import exceptions
    from exceptions import account, persistence

    modules = (exceptions, account, persistence)

    return f"""
### Exceptions
{to_collapsible(title=f"`{exceptions.SystemException.__name__}`: {exceptions.SystemException.__doc__}", 
                content=_gen_err_doc(modules, exceptions.SystemException))}

{to_collapsible(title=f"`{exceptions.PdogsException.__name__}`: {exceptions.PdogsException.__doc__}", 
                content=_gen_err_doc(modules, exceptions.PdogsException))}
"""


def _gen_err_doc(modules, base_cls):
    item_docs = []
    for module in modules:
        item_doc = _gen_err_items(module, base_cls)
        if item_doc:
            item_docs.append(f"#### {module.__name__.split('.', maxsplit=1)[-1].title()}\n{indent(item_doc, '  ')}")

    return '\n'.join(item_docs)


def _gen_err_items(exc_module, base_cls):
    import inspect
    return '\n'.join(f"- `{name}`: {base_cls.__doc__}"
                     for name, base_cls
                     in inspect.getmembers(exc_module, lambda obj: inspect.isclass(obj)
                                                                   and issubclass(obj, base_cls)
                                                                   and obj is not base_cls))
