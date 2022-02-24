import dataclasses
from typing import (
    Any,
    Callable,
    Optional,
    Type,
    Union,
)
import urllib.parse

import fastapi.routing
from fastapi import params
from fastapi.datastructures import Default
from fastapi.encoders import DictIntStrAny, SetIntStr
# Followings are originally imported from starlette
from fastapi.routing import JSONResponse, Response

import log
from util.context import context


def jsonable_encoder(
    obj: Any,
    include: Optional[Union[SetIntStr, DictIntStrAny]] = None,
    exclude: Optional[Union[SetIntStr, DictIntStrAny]] = None,
    by_alias: bool = True,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    custom_encoder: fastapi.encoders.Dict[Any, Callable[[Any], Any]] = {},
    sqlalchemy_safe: bool = True,
) -> Any:
    if include is not None and not isinstance(include, set):
        include = set(include)
    if exclude is not None and not isinstance(exclude, set):
        exclude = set(exclude)

    if isinstance(obj, fastapi.encoders.BaseModel):
        encoder = getattr(obj.__config__, "json_encoders", {})
        if custom_encoder:
            encoder.update(custom_encoder)
        obj_dict = obj.dict(
            include=include,  # type: ignore # in Pydantic
            exclude=exclude,  # type: ignore # in Pydantic
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_none=exclude_none,
            exclude_defaults=exclude_defaults,
        )
        if "__root__" in obj_dict:
            obj_dict = obj_dict["__root__"]
        return jsonable_encoder(
            obj_dict,
            exclude_none=exclude_none,
            exclude_defaults=exclude_defaults,
            custom_encoder=encoder,
            sqlalchemy_safe=sqlalchemy_safe,
        )
    if isinstance(obj, fastapi.encoders.Enum):
        return obj.value
    if isinstance(obj, fastapi.encoders.PurePath):
        return str(obj)
    if isinstance(obj, (str, int, float, type(None))):
        return obj
    if isinstance(obj, dict):
        encoded_dict = {}
        for key, value in obj.items():
            if (
                (
                    not sqlalchemy_safe
                    or (not isinstance(key, str))
                    or (not key.startswith("_sa"))
                )
                and (value is not None or not exclude_none)
                and ((include and key in include) or not exclude or key not in exclude)
            ):
                encoded_key = jsonable_encoder(
                    key,
                    by_alias=by_alias,
                    exclude_unset=exclude_unset,
                    exclude_none=exclude_none,
                    custom_encoder=custom_encoder,
                    sqlalchemy_safe=sqlalchemy_safe,
                )
                encoded_value = jsonable_encoder(
                    value,
                    by_alias=by_alias,
                    exclude_unset=exclude_unset,
                    exclude_none=exclude_none,
                    custom_encoder=custom_encoder,
                    sqlalchemy_safe=sqlalchemy_safe,
                )
                encoded_dict[encoded_key] = encoded_value
        return encoded_dict
    if isinstance(obj, (list, set, frozenset, fastapi.encoders.GeneratorType, tuple)):
        encoded_list = []
        for item in obj:
            encoded_list.append(
                jsonable_encoder(
                    item,
                    include=include,
                    exclude=exclude,
                    by_alias=by_alias,
                    exclude_unset=exclude_unset,
                    exclude_defaults=exclude_defaults,
                    exclude_none=exclude_none,
                    custom_encoder=custom_encoder,
                    sqlalchemy_safe=sqlalchemy_safe,
                )
            )
        return encoded_list

    if custom_encoder:
        if type(obj) in custom_encoder:
            return custom_encoder[type(obj)](obj)
        else:
            for encoder_type, encoder in custom_encoder.items():
                if isinstance(obj, encoder_type):
                    return encoder(obj)

    if type(obj) in fastapi.encoders.ENCODERS_BY_TYPE:
        return fastapi.encoders.ENCODERS_BY_TYPE[type(obj)](obj)
    for encoder, classes_tuple in fastapi.encoders.encoders_by_class_tuples.items():
        if isinstance(obj, classes_tuple):
            return encoder(obj)

    # FOR THIS #
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)

    errors: fastapi.encoders.List[Exception] = []
    try:
        data = dict(obj)
    except Exception as e:
        errors.append(e)
        try:
            data = vars(obj)
        except Exception as e:
            errors.append(e)
            raise ValueError(errors)
    return jsonable_encoder(
        data,
        by_alias=by_alias,
        exclude_unset=exclude_unset,
        exclude_defaults=exclude_defaults,
        exclude_none=exclude_none,
        custom_encoder=custom_encoder,
        sqlalchemy_safe=sqlalchemy_safe,
    )


async def serialize_response(
    *,
    field: Optional[fastapi.routing.ModelField] = None,
    response_content: Any,
    include: Optional[Union[SetIntStr, DictIntStrAny]] = None,
    exclude: Optional[Union[SetIntStr, DictIntStrAny]] = None,
    by_alias: bool = True,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False,
    is_coroutine: bool = True,
) -> Any:
    if field:
        errors = []
        response_content = fastapi.routing._prepare_response_content(
            response_content,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )
        if is_coroutine:
            value, errors_ = field.validate(response_content, {}, loc=("response",))
        else:
            value, errors_ = await fastapi.routing.run_in_threadpool(
                field.validate, response_content, {}, loc=("response",)
            )
        if isinstance(errors_, fastapi.routing.ErrorWrapper):
            errors.append(errors_)
        elif isinstance(errors_, list):
            errors.extend(errors_)
        if errors:
            raise fastapi.routing.ValidationError(errors, field.type_)
        return jsonable_encoder(
            value,
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )
    else:
        return jsonable_encoder(response_content)


def get_request_handler(
    dependant: fastapi.routing.Dependant,
    body_field: Optional[fastapi.routing.ModelField] = None,
    status_code: int = 200,
    response_class: Union[Type[Response], fastapi.routing.DefaultPlaceholder] = Default(JSONResponse),
    response_field: Optional[fastapi.routing.ModelField] = None,
    response_model_include: Optional[Union[SetIntStr, DictIntStrAny]] = None,
    response_model_exclude: Optional[Union[SetIntStr, DictIntStrAny]] = None,
    response_model_by_alias: bool = True,
    response_model_exclude_unset: bool = False,
    response_model_exclude_defaults: bool = False,
    response_model_exclude_none: bool = False,
    dependency_overrides_provider: Optional[Any] = None,
) -> Callable[[fastapi.routing.Request], fastapi.routing.Coroutine[Any, Any, Response]]:
    assert dependant.call is not None, "dependant.call must be a function"
    is_coroutine = fastapi.routing.asyncio.iscoroutinefunction(dependant.call)
    is_body_form = body_field and isinstance(body_field.field_info, params.Form)
    if isinstance(response_class, fastapi.routing.DefaultPlaceholder):
        actual_response_class: Type[Response] = response_class.value
    else:
        actual_response_class = response_class

    async def app(request: fastapi.routing.Request) -> Response:
        try:
            body = None
            if body_field:
                if is_body_form:
                    body = await request.form()
                else:
                    body_bytes = await request.body()
                    if body_bytes:
                        body = await request.json()
        except fastapi.routing.json.JSONDecodeError as e:
            raise fastapi.routing.RequestValidationError([fastapi.routing.ErrorWrapper(e, ("body", e.pos))], body=e.doc)
        except Exception as e:
            raise fastapi.routing.HTTPException(
                status_code=400, detail="There was an error parsing the body"
            ) from e
        solved_result = await fastapi.routing.solve_dependencies(
            request=request,
            dependant=dependant,
            body=body,
            dependency_overrides_provider=dependency_overrides_provider,
        )
        values, errors, background_tasks, sub_response, _ = solved_result
        if errors:
            raise fastapi.routing.RequestValidationError(errors, body=body)
        else:
            raw_response = await fastapi.routing.run_endpoint_function(
                dependant=dependant, values=values, is_coroutine=is_coroutine
            )

            if isinstance(raw_response, Response):
                if raw_response.background is None:
                    raw_response.background = background_tasks
                return raw_response
            response_data = await serialize_response(
                field=response_field,
                response_content=raw_response,
                include=response_model_include,
                exclude=response_model_exclude,
                by_alias=response_model_by_alias,
                exclude_unset=response_model_exclude_unset,
                exclude_defaults=response_model_exclude_defaults,
                exclude_none=response_model_exclude_none,
                is_coroutine=is_coroutine,
            )
            response = actual_response_class(
                content=response_data,
                status_code=status_code,
                background=background_tasks,  # type: ignore # in Starlette
            )
            response.headers.raw.extend(sub_response.headers.raw)
            if sub_response.status_code:
                response.status_code = sub_response.status_code
            return response

    return app


class NoLogAPIRoute(fastapi.routing.APIRoute):
    def get_route_handler(self) -> Callable[[fastapi.routing.Request], fastapi.routing.Coroutine[Any, Any, Response]]:
        return get_request_handler(
            dependant=self.dependant,
            body_field=self.body_field,
            status_code=self.status_code,
            response_class=self.response_class,
            response_field=self.secure_cloned_response_field,
            response_model_include=self.response_model_include,
            response_model_exclude=self.response_model_exclude,
            response_model_by_alias=self.response_model_by_alias,
            response_model_exclude_unset=self.response_model_exclude_unset,
            response_model_exclude_defaults=self.response_model_exclude_defaults,
            response_model_exclude_none=self.response_model_exclude_none,
            dependency_overrides_provider=self.dependency_overrides_provider,
        )


class APIRoute(fastapi.routing.APIRoute):
    def get_route_handler(self) -> Callable[[fastapi.routing.Request], fastapi.routing.Coroutine[Any, Any, Response]]:
        original_route_handler = get_request_handler(
            dependant=self.dependant,
            body_field=self.body_field,
            status_code=self.status_code,
            response_class=self.response_class,
            response_field=self.secure_cloned_response_field,
            response_model_include=self.response_model_include,
            response_model_exclude=self.response_model_exclude,
            response_model_by_alias=self.response_model_by_alias,
            response_model_exclude_unset=self.response_model_exclude_unset,
            response_model_exclude_defaults=self.response_model_exclude_defaults,
            response_model_exclude_none=self.response_model_exclude_none,
            dependency_overrides_provider=self.dependency_overrides_provider,
        )

        async def custom_route_handler(request: fastapi.Request) -> fastapi.Response:
            """
            Replace request logs body
            """
            request_body = ''
            if 'json' in request.headers.get('Content-Type', ''):
                request_body = await request.body()
            query_string = ''
            if request_query_string := request.scope.get("query_string"):
                query_string = urllib.parse.unquote(request_query_string)

            log.info(f'>> {request.method}\t{request.url.path}'
                     f'\tAccount: {context.get_account()}'
                     f'\tQuery params: {query_string}' 
                     f'\tJSON Body: {request_body}')

            response = await original_route_handler(request)

            response_body = ''
            if isinstance(response, fastapi.responses.JSONResponse):
                response_body = response.body

            log.info(f'<< {request.method}\t{request.url.path}'
                     f'\tAccount: {context.get_account()}'
                     f'\tJSON Body: {response_body}')

            return response

        return custom_route_handler
