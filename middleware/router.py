import typing
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Type,
    Union,
)

import fastapi.routing

from . import routing


class APIRouter(fastapi.routing.APIRouter):
    def __init__(
        self,
        *,
        prefix: str = "",
        tags: Optional[List[str]] = None,
        dependencies: Optional[Sequence[fastapi.routing.params.Depends]] = None,
        default_response_class: Type[fastapi.routing.Response] = fastapi.routing.Default(fastapi.routing.JSONResponse),
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        callbacks: Optional[List[fastapi.routing.BaseRoute]] = None,
        routes: Optional[List[fastapi.routing.BaseRoute]] = None,
        redirect_slashes: bool = True,
        default: Optional[fastapi.routing.ASGIApp] = None,
        dependency_overrides_provider: Optional[Any] = None,
        route_class: Type[fastapi.routing.APIRoute] = routing.APIRoute,  # Changed!
        on_startup: Optional[Sequence[Callable[[], Any]]] = None,
        on_shutdown: Optional[Sequence[Callable[[], Any]]] = None,
        deprecated: Optional[bool] = None,
        include_in_schema: bool = True,
    ) -> None:
        super().__init__(prefix=prefix, tags=tags, dependencies=dependencies,
                         default_response_class=default_response_class, responses=responses, callbacks=callbacks,
                         routes=routes, redirect_slashes=redirect_slashes, default=default,
                         dependency_overrides_provider=dependency_overrides_provider, route_class=route_class,
                         on_startup=on_startup, on_shutdown=on_shutdown, deprecated=deprecated,
                         include_in_schema=include_in_schema)

    def api_route(
        self,
        path: str,
        *,
        response_model: Optional[Type[Any]] = None,
        status_code: int = 200,
        tags: Optional[List[str]] = None,
        dependencies: Optional[Sequence[fastapi.routing.params.Depends]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        response_description: str = "Successful Response",
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        deprecated: Optional[bool] = None,
        methods: Optional[List[str]] = None,
        operation_id: Optional[str] = None,
        response_model_include: Optional[Union[fastapi.routing.SetIntStr, fastapi.routing.DictIntStrAny]] = None,
        response_model_exclude: Optional[Union[fastapi.routing.SetIntStr, fastapi.routing.DictIntStrAny]] = None,
        response_model_by_alias: bool = True,
        response_model_exclude_unset: bool = False,
        response_model_exclude_defaults: bool = False,
        response_model_exclude_none: bool = False,
        include_in_schema: bool = True,
        response_class: Type[fastapi.routing.Response] = fastapi.routing.Default(fastapi.routing.Response),
        name: Optional[str] = None,
        callbacks: Optional[List[fastapi.routing.BaseRoute]] = None,
    ) -> Callable[[fastapi.routing.DecoratedCallable], fastapi.routing.DecoratedCallable]:
        def decorator(func: fastapi.routing.DecoratedCallable) -> fastapi.routing.DecoratedCallable:

            # FOR THIS #
            # Auto get response model from function's return type hint
            model = response_model
            if not model:
                try:
                    model = typing.get_type_hints(func)['return']
                except KeyError:
                    # raise SyntaxError("No return type type-hint is given!")
                    pass

            self.add_api_route(
                path,
                func,
                response_model=model,
                status_code=status_code,
                tags=tags,
                dependencies=dependencies,
                summary=summary,
                description=description,
                response_description=response_description,
                responses=responses,
                deprecated=deprecated,
                methods=methods,
                operation_id=operation_id,
                response_model_include=response_model_include,
                response_model_exclude=response_model_exclude,
                response_model_by_alias=response_model_by_alias,
                response_model_exclude_unset=response_model_exclude_unset,
                response_model_exclude_defaults=response_model_exclude_defaults,
                response_model_exclude_none=response_model_exclude_none,
                include_in_schema=include_in_schema,
                response_class=response_class,
                name=name,
                callbacks=callbacks,
            )
            return func

        return decorator
