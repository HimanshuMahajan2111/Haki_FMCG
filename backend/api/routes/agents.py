"""Agent-related API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from db.database import get_db
from db.models import AgentLog, AgentType

router = APIRouter()


@router.get("/logs")
async def get_agent_logs(
    agent_name: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """Get agent execution logs.
    
    Args:
        agent_name: Filter by agent name
        limit: Maximum number of logs
        db: Database session
        
    Returns:
        Agent logs
    """
    query = select(AgentLog).order_by(desc(AgentLog.created_at)).limit(limit)
    
    if agent_name:
        query = query.where(AgentLog.agent_name == agent_name)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return {
        "data": [
            {
                "id": log.id,
                "rfp_id": log.rfp_id,
                "agent_type": log.agent_type.value,
                "agent_name": log.agent_name,
                "started_at": log.started_at.isoformat(),
                "completed_at": log.completed_at.isoformat() if log.completed_at else None,
                "duration_seconds": log.duration_seconds,
                "status": log.status,
                "tokens_used": log.tokens_used,
                "cost_usd": log.cost_usd,
            }
            for log in logs
        ]
    }


@router.get("/statistics")
async def get_agent_statistics(
    db: AsyncSession = Depends(get_db)
):
    """Get aggregate agent statistics.
    
    Args:
        db: Database session
        
    Returns:
        Agent statistics
    """
    from sqlalchemy import func
    
    # Get statistics per agent type
    stats_query = (
        select(
            AgentLog.agent_type,
            func.count(AgentLog.id).label("execution_count"),
            func.avg(AgentLog.duration_seconds).label("avg_duration"),
            func.sum(AgentLog.tokens_used).label("total_tokens"),
            func.sum(AgentLog.cost_usd).label("total_cost"),
        )
        .group_by(AgentLog.agent_type)
    )
    
    result = await db.execute(stats_query)
    stats = result.all()
    
    return {
        "data": [
            {
                "agent_type": stat.agent_type.value,
                "execution_count": stat.execution_count,
                "avg_duration_seconds": round(stat.avg_duration or 0, 2),
                "total_tokens": stat.total_tokens or 0,
                "total_cost_usd": round(stat.total_cost or 0, 4),
            }
            for stat in stats
        ]
    }
