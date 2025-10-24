"""
Analytics and metrics API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timedelta
from typing import Optional, List

from app.auth import get_current_user
from app.database import database
from app.services.metrics_service import MetricsService
from app.models.metrics import DailyMetrics

router = APIRouter()


@router.get("/metrics")
async def get_current_metrics(
    current_user: dict = Depends(get_current_user)
):
    """
    Get current system metrics and KPIs.
    
    Returns:
        Current metrics summary
    """
    db = database.get_database()
    metrics_service = MetricsService(db)
    
    metrics = await metrics_service.get_current_metrics()
    return metrics


@router.get("/metrics/daily/{date}", response_model=DailyMetrics)
async def get_daily_metrics(
    date: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get aggregated metrics for a specific date.
    
    Args:
        date: Date in YYYY-MM-DD format
        current_user: Authenticated user
        
    Returns:
        Daily metrics
        
    Raises:
        HTTPException: If date format is invalid or metrics not found
    """
    # Validate date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    
    db = database.get_database()
    metrics_service = MetricsService(db)
    
    # Try to get existing metrics
    metrics = await metrics_service.get_daily_metrics(date)
    
    # If not found, aggregate them
    if not metrics:
        metrics = await metrics_service.aggregate_daily_metrics(date)
    
    return metrics


@router.get("/metrics/range", response_model=List[DailyMetrics])
async def get_metrics_range(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    days: Optional[int] = Query(7, description="Number of days (if dates not specified)"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get metrics for a date range.
    
    Args:
        start_date: Start date (optional)
        end_date: End date (optional)
        days: Number of days to fetch (default 7)
        current_user: Authenticated user
        
    Returns:
        List of daily metrics
    """
    # Calculate date range
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    if not start_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        start_dt = end_dt - timedelta(days=days - 1)
        start_date = start_dt.strftime("%Y-%m-%d")
    
    db = database.get_database()
    metrics_service = MetricsService(db)
    
    metrics = await metrics_service.get_metrics_range(start_date, end_date)
    return metrics


@router.get("/calls")
async def get_call_analytics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Get call analytics data for charts.
    
    Args:
        start_date: Start date filter
        end_date: End date filter
        current_user: Authenticated user
        
    Returns:
        Call analytics data
    """
    # Default to last 7 days
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if not start_date:
        start_dt = datetime.now() - timedelta(days=6)
        start_date = start_dt.strftime("%Y-%m-%d")
    
    db = database.get_database()
    metrics_service = MetricsService(db)
    
    metrics = await metrics_service.get_metrics_range(start_date, end_date)
    
    # Format for frontend charts
    daily_stats = []
    for m in metrics:
        daily_stats.append({
            "date": m.date,
            "total_calls": m.total_calls,
            "completed_calls": m.completed_calls,
            "failed_calls": m.failed_calls,
            "avg_duration": m.avg_call_duration_seconds
        })
    
    return {"daily_stats": daily_stats}


@router.post("/metrics/aggregate/{date}")
async def aggregate_metrics(
    date: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Manually trigger metrics aggregation for a specific date.
    
    Args:
        date: Date in YYYY-MM-DD format
        current_user: Authenticated user
        
    Returns:
        Aggregated metrics
    """
    # Validate date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    
    db = database.get_database()
    metrics_service = MetricsService(db)
    
    metrics = await metrics_service.aggregate_daily_metrics(date)
    return metrics


@router.get("/alerts")
async def get_alerts(
    current_user: dict = Depends(get_current_user)
):
    """
    Get current system alerts based on metric thresholds.
    
    Returns:
        List of active alerts
    """
    db = database.get_database()
    metrics_service = MetricsService(db)
    
    alerts = await metrics_service.check_alert_thresholds()
    return {"alerts": alerts}
