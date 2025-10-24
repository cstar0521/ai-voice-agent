"""
API routes for the AI Voice Loan Agent.
"""
from fastapi import APIRouter

from app.api import auth, calls, leads, config, analytics

# Create main API router with v1 prefix
api_router = APIRouter(prefix="/api/v1")

# Include sub-routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(calls.router, prefix="/calls", tags=["calls"])
api_router.include_router(leads.router, prefix="/leads", tags=["leads"])
api_router.include_router(config.router, prefix="/config", tags=["configuration"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])

__all__ = ["api_router"]
