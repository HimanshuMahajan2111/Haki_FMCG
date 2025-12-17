"""
Progress Tracker for RFP Processing
Tracks agent execution progress in real-time
"""
from typing import Dict, Any
from datetime import datetime
import structlog

logger = structlog.get_logger()


class ProgressTracker:
    """Track processing progress for RFPs."""
    
    # In-memory storage (use Redis in production)
    _progress_store: Dict[int, Dict[str, Any]] = {}
    
    @classmethod
    def start_processing(cls, rfp_id: int):
        """Initialize processing progress."""
        cls._progress_store[rfp_id] = {
            "status": "processing",
            "progress": 0,
            "current_stage": "Initializing",
            "agents_status": {},
            "estimated_time_remaining": "2-5 minutes",
            "started_at": datetime.utcnow().isoformat()
        }
        logger.info("Processing started", rfp_id=rfp_id)
    
    @classmethod
    def update_stage(cls, rfp_id: int, stage: str, progress: int):
        """Update current processing stage."""
        if rfp_id in cls._progress_store:
            cls._progress_store[rfp_id].update({
                "current_stage": stage,
                "progress": progress,
                "updated_at": datetime.utcnow().isoformat()
            })
            logger.info("Stage updated", rfp_id=rfp_id, stage=stage, progress=progress)
    
    @classmethod
    def update_agent_status(cls, rfp_id: int, agent_name: str, status: str, details: str = ""):
        """Update individual agent status."""
        if rfp_id in cls._progress_store:
            if "agents_status" not in cls._progress_store[rfp_id]:
                cls._progress_store[rfp_id]["agents_status"] = {}
            
            cls._progress_store[rfp_id]["agents_status"][agent_name] = {
                "status": status,  # running, completed, failed
                "details": details,
                "updated_at": datetime.utcnow().isoformat()
            }
            logger.info("Agent status updated", rfp_id=rfp_id, agent=agent_name, status=status)
    
    @classmethod
    def complete_processing(cls, rfp_id: int, success: bool = True):
        """Mark processing as complete."""
        if rfp_id in cls._progress_store:
            cls._progress_store[rfp_id].update({
                "status": "completed" if success else "failed",
                "progress": 100 if success else cls._progress_store[rfp_id].get("progress", 0),
                "current_stage": "Completed" if success else "Failed",
                "completed_at": datetime.utcnow().isoformat()
            })
            logger.info("Processing completed", rfp_id=rfp_id, success=success)
    
    @classmethod
    def get_progress(cls, rfp_id: int) -> Dict[str, Any]:
        """Get current progress status."""
        return cls._progress_store.get(rfp_id, {
            "status": "not_started",
            "progress": 0,
            "current_stage": "Not Started",
            "agents_status": {}
        })
    
    @classmethod
    def clear_progress(cls, rfp_id: int):
        """Clear progress data for an RFP."""
        if rfp_id in cls._progress_store:
            del cls._progress_store[rfp_id]
