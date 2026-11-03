"""FastAPI application entry point."""

from contextlib import asynccontextmanager
import logging
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1 import api_router

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


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.\d+\.\d+\.\d+)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
