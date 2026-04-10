from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
import logging
import time
import uuid
import os
import asyncio

from app.database import database
from app.logging_config import setup_logging, get_logger, log_api_request
from app.middleware.rate_limit import RateLimitMiddleware, add_security_headers, cleanup_rate_limiter
from config import settings

# Configure structured logging
log_level = os.getenv("LOG_LEVEL", "INFO")
log_file = os.getenv("LOG_FILE", None)
setup_logging(log_level=log_level, log_file=log_file)

logger = get_logger('api')

app = FastAPI(
    title="AI Voice Loan Agent API",
    version="1.0.0",
    description="AI-powered voice agent for education loan qualification"
)

# Rate limiting middleware (add before CORS)
rate_limit_middleware = RateLimitMiddleware(
    default_limit=100,  # 100 requests per minute per IP
    default_window=60,
    webhook_limit=1000,  # 1000 requests per minute for webhooks
    webhook_window=60
)
app.middleware("http")(rate_limit_middleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security headers middleware
@app.middleware("http")
async def add_security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response = add_security_headers(response)
    return response


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests and responses with structured logging."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.time()
    
    # Process request
    try:
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000
        
        # Log API request
        log_api_request(
            logger,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            user_id=getattr(request.state, 'user_id', None)
        )
        
        # Add request ID to response
        response.headers["X-Request-ID"] = request_id
        
        return response
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(
            f"Request failed: {str(e)}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "duration_ms": duration_ms,
                "error": str(e)
            },
            exc_info=True
        )
        raise
    
    logger.info(
        f"Request completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "process_time": f"{process_time:.3f}s"
        }
    )
    
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.3f}"
    
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.error(
        f"Unhandled exception",
        extra={
            "request_id": request_id,
            "error": str(exc),
            "type": type(exc).__name__
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "request_id": request_id,
            "message": "An unexpected error occurred"
        }
    )


# Validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.warning(
        f"Validation error",
        extra={
            "request_id": request_id,
            "errors": exc.errors()
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "request_id": request_id,
            "details": exc.errors()
        }
    )


@app.on_event("startup")
async def startup_event():
    """Initialize database connection and background tasks on startup."""
    logger.info("Starting AI Voice Loan Agent API")
    try:
        await database.connect()
        logger.info("Database connected successfully")
        
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}", exc_info=True)
        logger.warning("Starting server without database connection. Some features may not work.")
    
    try:
        # Start rate limiter cleanup task
        asyncio.create_task(cleanup_rate_limiter())
        logger.info("Rate limiter cleanup task started")
        
    except Exception as e:
        logger.error(f"Failed to start background tasks: {e}", exc_info=True)
    
    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown."""
    await database.disconnect()
    logger.info("Database disconnected")


# Include API routes
from app.api import api_router
app.include_router(api_router)

# Test endpoints removed - using production endpoints

# Mount static files for serving Sarvam AI audio
import os
os.makedirs("static/audio", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "AI Voice Loan Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health():
    """Health check endpoint with database status."""
    db_status = await database.ping()
    return {
        "status": "healthy" if db_status else "degraded",
        "database": "connected" if db_status else "disconnected",
        "version": "1.0.0"
    }
