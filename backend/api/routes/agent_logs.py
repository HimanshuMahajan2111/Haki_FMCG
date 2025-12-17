"""
Agent Logs API - Real-time agent execution logs

Endpoints:
- GET /api/logs/agents          - Get recent agent logs
- GET /api/logs/workflow/{id}   - Get logs for specific workflow
- WS  /api/logs/stream           - WebSocket for real-time log streaming
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict
import json
import structlog
import asyncio

from db.database import get_db

router = APIRouter(prefix="/api/logs", tags=["logs"])
logger = structlog.get_logger()

# In-memory log storage for real-time streaming
# In production, use Redis or database
agent_logs_store = defaultdict(list)
active_websockets: List[WebSocket] = []


class AgentLogManager:
    """Manage agent logs for real-time streaming."""
    
    @staticmethod
    async def add_log(workflow_id: str, log_entry: Dict[str, Any]):
        """Add log entry and broadcast to connected clients."""
        log_entry['timestamp'] = datetime.now().isoformat()
        log_entry['workflow_id'] = workflow_id
        
        # Store in memory
        agent_logs_store[workflow_id].append(log_entry)
        
        # Keep only last 1000 logs per workflow
        if len(agent_logs_store[workflow_id]) > 1000:
            agent_logs_store[workflow_id] = agent_logs_store[workflow_id][-1000:]
        
        # Broadcast to all connected WebSocket clients
        await AgentLogManager.broadcast_log(log_entry)
        
        logger.info("Agent log added", workflow_id=workflow_id, agent=log_entry.get('agent'))
    
    @staticmethod
    async def broadcast_log(log_entry: Dict[str, Any]):
        """Broadcast log to all connected WebSocket clients."""
        disconnected = []
        message = json.dumps(log_entry)
        
        for websocket in active_websockets:
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error("Error broadcasting to WebSocket", error=str(e))
                disconnected.append(websocket)
        
        # Remove disconnected clients
        for ws in disconnected:
            if ws in active_websockets:
                active_websockets.remove(ws)
    
    @staticmethod
    def get_logs(workflow_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get logs for a specific workflow."""
        logs = agent_logs_store.get(workflow_id, [])
        return logs[-limit:] if logs else []
    
    @staticmethod
    def get_all_recent_logs(limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent logs across all workflows."""
        all_logs = []
        for logs in agent_logs_store.values():
            all_logs.extend(logs)
        
        # Sort by timestamp descending
        all_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return all_logs[:limit]


# Singleton instance
log_manager = AgentLogManager()


@router.get("/agents")
async def get_agent_logs(
    limit: int = 100,
    agent: str = None,
    level: str = None
) -> Dict[str, Any]:
    """
    Get recent agent logs.
    
    Args:
        limit: Maximum number of logs to return
        agent: Filter by agent name (sales/technical/pricing/master)
        level: Filter by log level (info/warning/error)
        
    Returns:
        Recent agent logs
    """
    logs = log_manager.get_all_recent_logs(limit)
    
    # Apply filters
    if agent:
        logs = [log for log in logs if log.get('agent') == agent]
    
    if level:
        logs = [log for log in logs if log.get('level') == level]
    
    return {
        "success": True,
        "data": {
            "logs": logs,
            "count": len(logs),
            "filters": {
                "agent": agent,
                "level": level
            }
        }
    }


@router.get("/workflow/{workflow_id}")
async def get_workflow_logs(
    workflow_id: str,
    limit: int = 1000
) -> Dict[str, Any]:
    """
    Get logs for a specific workflow.
    
    Args:
        workflow_id: Workflow ID
        limit: Maximum number of logs
        
    Returns:
        Workflow logs
    """
    logs = log_manager.get_logs(workflow_id, limit)
    
    if not logs:
        return {
            "success": True,
            "data": {
                "logs": [],
                "count": 0,
                "workflow_id": workflow_id,
                "message": "No logs found for this workflow"
            }
        }
    
    # Calculate statistics
    agent_counts = defaultdict(int)
    level_counts = defaultdict(int)
    
    for log in logs:
        agent_counts[log.get('agent', 'unknown')] += 1
        level_counts[log.get('level', 'info')] += 1
    
    return {
        "success": True,
        "data": {
            "logs": logs,
            "count": len(logs),
            "workflow_id": workflow_id,
            "statistics": {
                "by_agent": dict(agent_counts),
                "by_level": dict(level_counts),
                "start_time": logs[0].get('timestamp') if logs else None,
                "end_time": logs[-1].get('timestamp') if logs else None
            }
        }
    }


@router.websocket("/stream")
async def websocket_log_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time log streaming.
    
    Usage:
        const ws = new WebSocket('ws://localhost:8000/api/logs/stream');
        ws.onmessage = (event) => {
            const log = JSON.parse(event.data);
            console.log(log);
        };
    """
    await websocket.accept()
    active_websockets.append(websocket)
    
    logger.info("WebSocket connection established", total_connections=len(active_websockets))
    
    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connection",
            "message": "Connected to agent log stream",
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep connection alive and listen for messages
        while True:
            data = await websocket.receive_text()
            
            # Handle ping/pong for keep-alive
            if data == "ping":
                await websocket.send_text("pong")
            
            # Allow client to request specific workflow logs
            elif data.startswith("workflow:"):
                workflow_id = data.split(":")[1]
                logs = log_manager.get_logs(workflow_id)
                await websocket.send_json({
                    "type": "workflow_logs",
                    "workflow_id": workflow_id,
                    "logs": logs
                })
    
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
        if websocket in active_websockets:
            active_websockets.remove(websocket)
    
    except Exception as e:
        logger.error("WebSocket error", error=str(e))
        if websocket in active_websockets:
            active_websockets.remove(websocket)
        await websocket.close()


@router.post("/emit")
async def emit_log(log_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Emit a log entry (used internally by agents).
    
    Args:
        log_data: Log entry data
        
    Returns:
        Success confirmation
    """
    required_fields = ['workflow_id', 'agent', 'message']
    
    for field in required_fields:
        if field not in log_data:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required field: {field}"
            )
    
    # Add default level if not provided
    if 'level' not in log_data:
        log_data['level'] = 'info'
    
    await log_manager.add_log(log_data['workflow_id'], log_data)
    
    return {
        "success": True,
        "message": "Log emitted successfully"
    }


@router.delete("/workflow/{workflow_id}")
async def clear_workflow_logs(workflow_id: str) -> Dict[str, Any]:
    """
    Clear logs for a specific workflow.
    
    Args:
        workflow_id: Workflow ID
        
    Returns:
        Deletion confirmation
    """
    if workflow_id in agent_logs_store:
        count = len(agent_logs_store[workflow_id])
        del agent_logs_store[workflow_id]
        
        return {
            "success": True,
            "message": f"Cleared {count} logs for workflow {workflow_id}"
        }
    else:
        raise HTTPException(
            status_code=404,
            detail=f"No logs found for workflow {workflow_id}"
        )


@router.get("/statistics")
async def get_log_statistics() -> Dict[str, Any]:
    """
    Get overall log statistics.
    
    Returns:
        Log statistics across all workflows
    """
    total_logs = sum(len(logs) for logs in agent_logs_store.values())
    total_workflows = len(agent_logs_store)
    
    agent_totals = defaultdict(int)
    level_totals = defaultdict(int)
    
    for logs in agent_logs_store.values():
        for log in logs:
            agent_totals[log.get('agent', 'unknown')] += 1
            level_totals[log.get('level', 'info')] += 1
    
    return {
        "success": True,
        "data": {
            "total_logs": total_logs,
            "total_workflows": total_workflows,
            "active_websockets": len(active_websockets),
            "by_agent": dict(agent_totals),
            "by_level": dict(level_totals),
            "recent_workflows": list(agent_logs_store.keys())[-10:]
        }
    }


# Helper function to emit logs from agents
async def emit_agent_log(
    workflow_id: str,
    agent: str,
    message: str,
    level: str = "info",
    data: Dict[str, Any] = None
):
    """
    Helper function for agents to emit logs.
    
    Usage in agents:
        from api.routes.agent_logs import emit_agent_log
        
        await emit_agent_log(
            workflow_id="wf_123",
            agent="technical_agent",
            message="Found 15 matching products",
            level="info",
            data={"match_count": 15}
        )
    
    Args:
        workflow_id: Workflow ID
        agent: Agent name (sales_agent, technical_agent, pricing_agent, master_agent)
        message: Log message
        level: Log level (info, warning, error, success)
        data: Additional data
    """
    log_entry = {
        "agent": agent,
        "message": message,
        "level": level,
        "data": data or {}
    }
    
    await log_manager.add_log(workflow_id, log_entry)


# Export for use in other modules
__all__ = ['router', 'emit_agent_log', 'log_manager']
