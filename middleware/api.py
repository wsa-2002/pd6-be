from typing import Any, Dict, List, Optional, Sequence, Union

import fastapi
import fastapi.openapi.utils


def get_openapi_path(
    *, route: fastapi.openapi.utils.routing.APIRoute, model_name_map: Dict[type, str]
) -> fastapi.openapi.utils.Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    path = {}
    security_schemes: Dict[str, Any] = {}
    definitions: Dict[str, Any] = {}
    assert route.methods is not None, "Methods must be a list"
    if isinstance(route.response_class, fastapi.openapi.utils.DefaultPlaceholder):
        current_response_class: fastapi.openapi.utils.Type[fastapi.openapi.utils.Response] = route.response_class.value
    else:
        current_response_class = route.response_class
    assert current_response_class, "A response class is needed to generate OpenAPI"
    route_response_media_type: Optional[str] = current_response_class.media_type
    if route.include_in_schema:
        for method in route.methods:
            operation = fastapi.openapi.utils.get_openapi_operation_metadata(route=route, method=method)
            parameters: List[Dict[str, Any]] = []
            flat_dependant = fastapi.openapi.utils.get_flat_dependant(route.dependant, skip_repeats=True)
            security_definitions, operation_security = fastapi.openapi.utils.get_openapi_security_definitions(
                flat_dependant=flat_dependant
            )
            if operation_security:
                operation.setdefault("security", []).extend(operation_security)
            if security_definitions:
                security_schemes.update(security_definitions)
            all_route_params = fastapi.openapi.utils.get_flat_params(route.dependant)
            operation_parameters = fastapi.openapi.utils.get_openapi_operation_parameters(
                all_route_params=all_route_params, model_name_map=model_name_map
            )
            parameters.extend(operation_parameters)
            if parameters:
                operation["parameters"] = list(
                    {param["name"]: param for param in parameters}.values()
                )
            if method in fastapi.openapi.utils.METHODS_WITH_BODY:
                request_body_oai = fastapi.openapi.utils.get_openapi_operation_request_body(
                    body_field=route.body_field, model_name_map=model_name_map
                )
                if request_body_oai:
                    operation["requestBody"] = request_body_oai
            if route.callbacks:
                callbacks = {}
                for callback in route.callbacks:
                    if isinstance(callback, fastapi.openapi.utils.routing.APIRoute):
                        (
                            cb_path,
                            cb_security_schemes,
                            cb_definitions,
                        ) = get_openapi_path(
                            route=callback, model_name_map=model_name_map
                        )
                        callbacks[callback.name] = {callback.path: cb_path}
                operation["callbacks"] = callbacks
            status_code = str(route.status_code)
            operation.setdefault("responses", {}).setdefault(status_code, {})[
                "description"
            ] = route.response_description
            if (
                route_response_media_type
                and route.status_code not in fastapi.openapi.utils.STATUS_CODES_WITH_NO_BODY
            ):
                response_schema = {"type": "string"}
                if fastapi.openapi.utils.lenient_issubclass(current_response_class, fastapi.openapi.utils.JSONResponse):
                    if route.response_field:
                        response_schema, _, _ = fastapi.openapi.utils.field_schema(
                            route.response_field,
                            model_name_map=model_name_map,
                            ref_prefix=fastapi.openapi.utils.REF_PREFIX,
                        )
                    else:
                        response_schema = {}
                operation.setdefault("responses", {}).setdefault(
                    status_code, {}
                ).setdefault("content", {}).setdefault(route_response_media_type, {})[
                    "schema"
                ] = response_schema
            if route.responses:
                operation_responses = operation.setdefault("responses", {})
                for (
                    additional_status_code,
                    additional_response,
                ) in route.responses.items():
                    process_response = additional_response.copy()
                    process_response.pop("model", None)
                    status_code_key = str(additional_status_code).upper()
                    if status_code_key == "DEFAULT":
                        status_code_key = "default"
                    openapi_response = operation_responses.setdefault(
                        status_code_key, {}
                    )
                    assert isinstance(
                        process_response, dict
                    ), "An additional response must be a dict"
                    field = route.response_fields.get(additional_status_code)
                    additional_field_schema: Optional[Dict[str, Any]] = None
                    if field:
                        additional_field_schema, _, _ = fastapi.openapi.utils.field_schema(
                            field, model_name_map=model_name_map, ref_prefix=fastapi.openapi.utils.REF_PREFIX
                        )
                        media_type = route_response_media_type or "application/json"
                        additional_schema = (
                            process_response.setdefault("content", {})
                            .setdefault(media_type, {})
                            .setdefault("schema", {})
                        )
                        fastapi.openapi.utils.deep_dict_update(additional_schema, additional_field_schema)
                    status_text: Optional[str] = fastapi.openapi.utils.status_code_ranges.get(
                        str(additional_status_code).upper()
                    ) or fastapi.openapi.utils.http.client.responses.get(int(additional_status_code))
                    description = (
                        process_response.get("description")
                        or openapi_response.get("description")
                        or status_text
                        or "Additional Response"
                    )
                    fastapi.openapi.utils.deep_dict_update(openapi_response, process_response)
                    openapi_response["description"] = description

            # HTTP 422 ValidationError is removed
            # because they will be handled in envelope's error handler
            # and NOT raised with HTTP code 422

            # http422 = str(fastapi.openapi.utils.HTTP_422_UNPROCESSABLE_ENTITY)
            # if (all_route_params or route.body_field) and not any(
            #     [
            #         status in operation["responses"]
            #         for status in [http422, "4XX", "default"]
            #     ]
            # ):
            #     operation["responses"][http422] = {
            #         "description": "Validation Error",
            #         "content": {
            #             "application/json": {
            #                 "schema": {"$ref": fastapi.openapi.utils.REF_PREFIX + "HTTPValidationError"}
            #             }
            #         },
            #     }
            #     if "ValidationError" not in definitions:
            #         definitions.update(
            #             {
            #                 "ValidationError": fastapi.openapi.utils.validation_error_definition,
            #                 "HTTPValidationError": fastapi.openapi.utils.validation_error_response_definition,
            #             }
            #         )
            path[method.lower()] = operation
    return path, security_schemes, definitions


def get_openapi(
    *,
    title: str,
    version: str,
    openapi_version: str = "3.0.2",
    description: Optional[str] = None,
    routes: Sequence[fastapi.openapi.utils.BaseRoute],
    tags: Optional[List[Dict[str, Any]]] = None,
    servers: Optional[List[Dict[str, Union[str, Any]]]] = None,
) -> Dict[str, Any]:
    info = {"title": title, "version": version}
    if description:
        info["description"] = description
    output: Dict[str, Any] = {"openapi": openapi_version, "info": info}
    if servers:
        output["servers"] = servers
    components: Dict[str, Dict[str, Any]] = {}
    paths: Dict[str, Dict[str, Any]] = {}
    flat_models = fastapi.openapi.utils.get_flat_models_from_routes(routes)
    model_name_map = fastapi.openapi.utils.get_model_name_map(flat_models)

    # FOR THIS #
    for flat_model in flat_models:
        if flat_model not in model_name_map:
            # find key
            same_flat_model = [model for model, mapped in model_name_map.items()
                               if model.__name__ == flat_model.__name__][0]
            model_name_map[flat_model] = model_name_map[same_flat_model]

    definitions = fastapi.openapi.utils.get_model_definitions(
        flat_models=flat_models, model_name_map=model_name_map
    )
    for route in routes:
        if isinstance(route, fastapi.openapi.utils.routing.APIRoute):
            result = get_openapi_path(route=route, model_name_map=model_name_map)
            if result:
                path, security_schemes, path_definitions = result
                if path:
                    paths.setdefault(route.path_format, {}).update(path)
                if security_schemes:
                    components.setdefault("securitySchemes", {}).update(
                        security_schemes
                    )
                if path_definitions:
                    definitions.update(path_definitions)
    if definitions:
        components["schemas"] = {k: definitions[k] for k in sorted(definitions)}
    if components:
        output["components"] = components
    output["paths"] = paths
    if tags:
        output["tags"] = tags
    return fastapi.openapi.utils.jsonable_encoder(fastapi.openapi.utils.OpenAPI(**output),
                                                  by_alias=True, exclude_none=True)  # type: ignore


class FastAPI(fastapi.FastAPI):
    def openapi(self) -> Dict[str, Any]:
        if not self.openapi_schema:
            self.openapi_schema = get_openapi(
                title=self.title,
                version=self.version,
                openapi_version=self.openapi_version,
                description=self.description,
                routes=self.routes,
                tags=self.openapi_tags,
                servers=self.servers,
            )
        return self.openapi_schema
