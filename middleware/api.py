from typing import Any, Dict, List, Optional, Sequence, Union

import fastapi
import fastapi.openapi.utils


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
            result = fastapi.openapi.utils.get_openapi_path(route=route, model_name_map=model_name_map)
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
