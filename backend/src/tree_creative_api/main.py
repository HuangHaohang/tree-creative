import uvicorn
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from tree_creative_api import __version__
from tree_creative_api.api.router import api_router, integration_router
from tree_creative_api.api.schemas import ErrorDetail, ErrorResponse, ServiceInfo
from tree_creative_api.core.config import Settings, get_settings
from tree_creative_api.core.errors import ApiError
from tree_creative_api.core.lifespan import build_lifespan
from tree_creative_api.core.logging import configure_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings.log_level)

    application = FastAPI(
        title=resolved_settings.app_name,
        version=__version__,
        debug=resolved_settings.debug,
        docs_url="/docs" if resolved_settings.docs_enabled else None,
        redoc_url="/redoc" if resolved_settings.docs_enabled else None,
        lifespan=build_lifespan(resolved_settings),
    )
    application.state.settings = resolved_settings
    application.add_middleware(CorrelationIdMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-CSRF-Token", "X-Request-ID"],
    )
    application.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=resolved_settings.allowed_hosts,
    )
    application.include_router(api_router, prefix=resolved_settings.api_v1_prefix)
    application.include_router(integration_router)

    @application.get("/", response_model=ServiceInfo, tags=["system"])
    async def service_info() -> ServiceInfo:
        return ServiceInfo(
            name=resolved_settings.app_name,
            version=__version__,
            environment=resolved_settings.app_env,
        )

    @application.exception_handler(ApiError)
    async def handle_api_error(_request: Request, error: ApiError) -> JSONResponse:
        payload = ErrorResponse(
            error=ErrorDetail(code=error.code, message=error.message),
        )
        return JSONResponse(status_code=error.status_code, content=payload.model_dump())

    @application.exception_handler(RequestValidationError)
    async def handle_validation_error(
        _request: Request,
        error: RequestValidationError,
    ) -> JSONResponse:
        payload = ErrorResponse(
            error=ErrorDetail(
                code="validation_error",
                message="Request validation failed",
                details={"issues": error.errors()},
            ),
        )
        return JSONResponse(status_code=422, content=payload.model_dump(mode="json"))

    Instrumentator().instrument(application).expose(
        application,
        endpoint="/metrics",
        include_in_schema=False,
    )
    return application


app = create_app()


def run() -> None:
    settings = get_settings()
    uvicorn.run(
        "tree_creative_api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
