"""FastAPI application entry point."""

from contextlib import asynccontextmanager
import logging
import uuid
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
# from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1 import api_router
from app.core.rate_limiter import limiter
from app.core.security import SecurityHeadersMiddleware
from app.core.monitoring import initialize_sentry

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Modern lifespan event handler for application startup and shutdown.
    Replaces deprecated @app.on_event handlers.
    """
    # Startup sequence
    logger.info(f"Starting {settings.APP_NAME} v2.5.0")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"API Documentation: http://{settings.BACKEND_HOST}:{settings.BACKEND_PORT}/docs")
    
    # Initialize Sentry
    if initialize_sentry():
        logger.info("Sentry error tracking initialized")
    
    try:
        from app.core.database import init_db
        init_db()
        logger.info("Database schemas and pgvector initialized successfully.")
    except Exception as e:
        logger.error(f"Database schema initialization warning: {e}")
    yield
    # Shutdown sequence
    logger.info("Gracefully shutting down AI Sales & CRM OS")


# Create FastAPI app with modern lifespan handler
app = FastAPI(
    title=settings.APP_NAME,
    version="2.5.0",
    description="Enterprise AI Sales, Lead Discovery, Outreach & CRM Operating System",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add rate limiter state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Exception handlers for resilient API contracts
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "message": "Input validation error"},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred", "path": str(request.url.path)},
    )


# Configure CORS - conditional based on environment
if settings.APP_ENV == "production":
    # Production: exact origins only, no regex patterns
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Development/Staging: allow local development IPs via regex
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.\d+\.\d+\.\d+)(:\d+)?$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# Prometheus metrics (temporarily disabled due to dependency conflict)
# Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
