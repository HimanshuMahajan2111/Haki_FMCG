"""
Agent Scheduler - Schedules and runs agent tasks.
"""
from typing import Callable, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import Thread, Event
import time
import structlog

logger = structlog.get_logger()


@dataclass
class ScheduleConfig:
    """Configuration for a scheduled task."""
    task_id: str
    task_name: str
    interval_minutes: int
    enabled: bool = True
    max_runs: Optional[int] = None  # None = unlimited
    run_count: int = 0
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None


class AgentScheduler:
    """Schedule and run agent tasks."""
    
    def __init__(self):
        """Initialize scheduler."""
        self.logger = logger.bind(component="AgentScheduler")
        self.schedules: Dict[str, ScheduleConfig] = {}
        self.tasks: Dict[str, Callable] = {}
        self.running = False
        self.stop_event = Event()
        self.scheduler_thread: Optional[Thread] = None
        
        self.logger.info("Agent scheduler initialized")
    
    def add_schedule(self, config: ScheduleConfig, task: Callable):
        """Add a scheduled task.
        
        Args:
            config: Schedule configuration
            task: Callable to execute
        """
        self.schedules[config.task_id] = config
        self.tasks[config.task_id] = task
        
        # Set next run time
        config.next_run = datetime.now() + timedelta(minutes=config.interval_minutes)
        
        self.logger.info(
            "Schedule added",
            task_id=config.task_id,
            interval_minutes=config.interval_minutes,
            next_run=config.next_run.isoformat()
        )
    
    def remove_schedule(self, task_id: str):
        """Remove a scheduled task.
        
        Args:
            task_id: Task ID to remove
        """
        if task_id in self.schedules:
            del self.schedules[task_id]
            del self.tasks[task_id]
            self.logger.info("Schedule removed", task_id=task_id)
    
    def start(self):
        """Start the scheduler."""
        if self.running:
            self.logger.warning("Scheduler already running")
            return
        
        self.running = True
        self.stop_event.clear()
        
        self.scheduler_thread = Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("Scheduler started", schedules=len(self.schedules))
    
    def stop(self):
        """Stop the scheduler."""
        if not self.running:
            return
        
        self.logger.info("Stopping scheduler")
        self.running = False
        self.stop_event.set()
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        self.logger.info("Scheduler stopped")
    
    def _run_scheduler(self):
        """Main scheduler loop."""
        self.logger.info("Scheduler loop started")
        
        while self.running:
            try:
                now = datetime.now()
                
                # Check each schedule
                for task_id, config in list(self.schedules.items()):
                    if not config.enabled:
                        continue
                    
                    # Check if task should run
                    if config.next_run and now >= config.next_run:
                        self._execute_task(task_id, config)
                
                # Sleep for 10 seconds before next check
                if self.stop_event.wait(timeout=10):
                    break
                
            except Exception as e:
                self.logger.error("Scheduler loop error", error=str(e))
                time.sleep(10)
        
        self.logger.info("Scheduler loop ended")
    
    def _execute_task(self, task_id: str, config: ScheduleConfig):
        """Execute a scheduled task.
        
        Args:
            task_id: Task ID
            config: Schedule configuration
        """
        self.logger.info("Executing scheduled task", task_id=task_id)
        
        try:
            # Update config
            config.last_run = datetime.now()
            config.run_count += 1
            
            # Execute task
            task = self.tasks[task_id]
            task()
            
            # Schedule next run
            if config.max_runs and config.run_count >= config.max_runs:
                self.logger.info(
                    "Task reached max runs, disabling",
                    task_id=task_id,
                    run_count=config.run_count
                )
                config.enabled = False
            else:
                config.next_run = datetime.now() + timedelta(minutes=config.interval_minutes)
                self.logger.debug(
                    "Task executed successfully",
                    task_id=task_id,
                    next_run=config.next_run.isoformat()
                )
            
        except Exception as e:
            self.logger.error(
                "Task execution failed",
                task_id=task_id,
                error=str(e)
            )
            # Retry after interval
            config.next_run = datetime.now() + timedelta(minutes=config.interval_minutes)
    
    def get_schedules(self) -> Dict[str, Dict[str, Any]]:
        """Get all schedules.
        
        Returns:
            Dictionary of schedule information
        """
        result = {}
        for task_id, config in self.schedules.items():
            result[task_id] = {
                'task_name': config.task_name,
                'interval_minutes': config.interval_minutes,
                'enabled': config.enabled,
                'run_count': config.run_count,
                'last_run': config.last_run.isoformat() if config.last_run else None,
                'next_run': config.next_run.isoformat() if config.next_run else None,
                'max_runs': config.max_runs
            }
        return result
