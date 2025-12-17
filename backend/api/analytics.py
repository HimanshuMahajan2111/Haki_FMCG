"""
Analytics and Monitoring API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from db.database import get_db
from services.analytics_service import get_analytics_service
from services.cache_service import get_cache_service, cache_result
from services.monitoring_service import get_performance_monitor, get_bottleneck_detector
from services.error_tracking import get_error_tracker

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


@router.get("/dashboard")
@cache_result(ttl_seconds=300, key_prefix="dashboard")
def get_dashboard_data(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive dashboard analytics
    
    - Cached for 5 minutes
    - Includes RFP processing, match accuracy, win rates, agent performance, system health
    """
    try:
        analytics = get_analytics_service(db)
        dashboard_data = analytics.generate_dashboard_data(days=days)
        return {
            "success": True,
            "data": dashboard_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate dashboard: {str(e)}")


@router.get("/rfp-processing")
def get_rfp_processing_analytics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get RFP processing statistics"""
    try:
        analytics = get_analytics_service(db)
        stats = analytics.get_rfp_processing_stats(days=days)
        return {"success": True, "data": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/match-accuracy")
def get_match_accuracy_analytics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get product matching accuracy metrics"""
    try:
        analytics = get_analytics_service(db)
        stats = analytics.get_match_accuracy_stats(days=days)
        return {"success": True, "data": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/win-rates")
def get_win_rate_analytics(
    days: int = Query(90, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get RFP win rate statistics"""
    try:
        analytics = get_analytics_service(db)
        stats = analytics.get_win_rate_stats(days=days)
        return {"success": True, "data": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent-performance")
def get_agent_performance_analytics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get agent performance metrics"""
    try:
        analytics = get_analytics_service(db)
        stats = analytics.get_agent_performance_stats(days=days)
        return {"success": True, "data": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system-health")
def get_system_health_analytics(
    db: Session = Depends(get_db)
):
    """Get system health metrics (not cached - real-time)"""
    try:
        analytics = get_analytics_service(db)
        stats = analytics.get_system_health_stats()
        return {"success": True, "data": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/realtime")
def get_realtime_metrics(
    db: Session = Depends(get_db)
):
    """Get real-time monitoring metrics"""
    try:
        analytics = get_analytics_service(db)
        metrics = analytics.get_realtime_metrics()
        return {"success": True, "data": metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance")
def get_performance_metrics():
    """Get performance monitoring metrics"""
    try:
        monitor = get_performance_monitor()
        metrics = monitor.get_all_metrics()
        system_metrics = monitor.get_system_metrics()
        
        return {
            "success": True,
            "data": {
                "metrics": metrics,
                "system": system_metrics
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bottlenecks")
def get_bottlenecks(
    minutes: int = Query(60, ge=1, le=1440)
):
    """Get detected performance bottlenecks"""
    try:
        detector = get_bottleneck_detector()
        bottlenecks = detector.get_bottlenecks(minutes=minutes)
        summary = detector.get_bottleneck_summary()
        
        return {
            "success": True,
            "data": {
                "bottlenecks": bottlenecks,
                "summary": summary
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache-stats")
def get_cache_statistics():
    """Get cache performance statistics"""
    try:
        cache = get_cache_service()
        stats = cache.get_stats()
        return {"success": True, "data": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear")
def clear_cache(pattern: Optional[str] = None):
    """Clear cache (optionally by pattern)"""
    try:
        cache = get_cache_service()
        cache.clear(pattern=pattern)
        return {
            "success": True,
            "message": f"Cache cleared{f' for pattern: {pattern}' if pattern else ''}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/errors")
def get_error_analytics(
    hours: int = Query(24, ge=1, le=168)
):
    """Get error analytics and summary"""
    try:
        tracker = get_error_tracker()
        summary = tracker.get_error_summary(hours=hours)
        recent_errors = tracker.get_recent_errors(minutes=hours*60)
        
        return {
            "success": True,
            "data": {
                "summary": summary,
                "recent_errors": recent_errors[:20]  # Last 20 errors
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/errors/{error_id}")
def get_error_details(error_id: str):
    """Get detailed information about a specific error"""
    try:
        tracker = get_error_tracker()
        error = tracker.get_error(error_id)
        
        if not error:
            raise HTTPException(status_code=404, detail="Error not found")
        
        return {"success": True, "data": error}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/errors/patterns/{error_type}")
def get_error_patterns(error_type: Optional[str] = None):
    """Get error pattern analysis"""
    try:
        tracker = get_error_tracker()
        patterns = tracker.get_error_patterns(error_type=error_type)
        
        return {"success": True, "data": patterns}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export")
def export_analytics_data(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Export all analytics data for reporting"""
    try:
        analytics = get_analytics_service(db)
        
        export_data = {
            "generated_at": datetime.utcnow().isoformat(),
            "period_days": days,
            "rfp_processing": analytics.get_rfp_processing_stats(days),
            "match_accuracy": analytics.get_match_accuracy_stats(days),
            "win_rates": analytics.get_win_rate_stats(days),
            "agent_performance": analytics.get_agent_performance_stats(days),
            "system_health": analytics.get_system_health_stats()
        }
        
        return {
            "success": True,
            "data": export_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
