"""RemediSync FastAPI application entrypoint, middleware, and lifecycle manager."""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
import uuid
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.api.config import settings
from src.api.routes import api_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager handling startup and shutdown events."""
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

# ------------------------------------------------------------------------------
# CORS Middleware
# ------------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------------------
# Correlation ID Middleware
# ------------------------------------------------------------------------------

@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    """Ensure every HTTP request and response carries a unique correlation ID."""
    correlation_id = request.headers.get("X-Correlation-ID") or f"req-{uuid.uuid4().hex[:8]}"
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


# ------------------------------------------------------------------------------
# Uniform Error Handling
# ------------------------------------------------------------------------------

def _build_error_payload(code: str, message: str, correlation_id: str) -> dict:
    """Helper formatting uniform error JSON response according to API specifications."""
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "correlation_id": correlation_id,
        },
    }


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Intercept Pydantic validation errors and return uniform 422 error envelope."""
    cid = getattr(request.state, "correlation_id", f"req-{uuid.uuid4().hex[:8]}")
    error_msgs = [f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in exc.errors()]
    msg = "; ".join(error_msgs)
    return JSONResponse(
        status_code=422,
        content=_build_error_payload(code="VALIDATION_ERROR", message=msg, correlation_id=cid),
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Intercept HTTP exceptions and return uniform envelope."""
    cid = getattr(request.state, "correlation_id", f"req-{uuid.uuid4().hex[:8]}")
    if isinstance(exc.detail, dict):
        code = exc.detail.get("code", "HTTP_ERROR")
        message = exc.detail.get("message", "An HTTP error occurred.")
    else:
        code = "HTTP_ERROR" if exc.status_code != 404 else "RESOURCE_NOT_FOUND"
        message = str(exc.detail)

    return JSONResponse(
        status_code=exc.status_code,
        content=_build_error_payload(code=code, message=message, correlation_id=cid),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all unhandled server error handler returning uniform 500 envelope."""
    cid = getattr(request.state, "correlation_id", f"req-{uuid.uuid4().hex[:8]}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_build_error_payload(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected server error occurred.",
            correlation_id=cid,
        ),
    )


# ------------------------------------------------------------------------------
# Route Registration
# ------------------------------------------------------------------------------

app.include_router(api_router)
