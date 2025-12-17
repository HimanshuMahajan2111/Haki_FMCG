"""State Manager for distributed agent state."""
import asyncio
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, Optional
from enum import Enum
import structlog

logger = structlog.get_logger()


class StateType(Enum):
    """Types of state."""
    WORKFLOW = "workflow"
    AGENT = "agent"
    SESSION = "session"
    CACHE = "cache"


@dataclass
class StateEntry:
    """State entry with metadata."""
    key: str
    value: Any
    state_type: StateType
    created_at: float
    updated_at: float
    expires_at: Optional[float] = None
    version: int = 1
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def is_expired(self) -> bool:
        """Check if state has expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['state_type'] = self.state_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateEntry':
        """Create from dictionary."""
        if isinstance(data['state_type'], str):
            data['state_type'] = StateType(data['state_type'])
        return cls(**data)


class StateManager(ABC):
    """Abstract base class for state managers."""
    
    @abstractmethod
    async def set(self, key: str, value: Any, 
                  state_type: StateType = StateType.WORKFLOW,
                  ttl: Optional[int] = None) -> bool:
        """Set state value."""
        pass
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get state value."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete state."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass
    
    @abstractmethod
    async def get_all(self, pattern: str = "*") -> Dict[str, Any]:
        """Get all states matching pattern."""
        pass
    
    @abstractmethod
    async def increment(self, key: str, delta: int = 1) -> int:
        """Increment counter."""
        pass


class InMemoryStateManager(StateManager):
    """In-memory state manager for development."""
    
    def __init__(self):
        self.states: Dict[str, StateEntry] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task = None
        logger.info("Initialized InMemoryStateManager")
    
    async def start_cleanup_task(self):
        """Start background cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop_cleanup_task(self):
        """Stop background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
    
    async def _cleanup_loop(self):
        """Background loop to clean up expired states."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Cleanup loop error", error=str(e))
    
    async def _cleanup_expired(self):
        """Remove expired states."""
        async with self._lock:
            expired_keys = [
                key for key, entry in self.states.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del self.states[key]
            if expired_keys:
                logger.debug("Cleaned up expired states", count=len(expired_keys))
    
    async def set(self, key: str, value: Any,
                  state_type: StateType = StateType.WORKFLOW,
                  ttl: Optional[int] = None) -> bool:
        """Set state value."""
        try:
            async with self._lock:
                now = time.time()
                expires_at = now + ttl if ttl else None
                
                if key in self.states:
                    # Update existing
                    entry = self.states[key]
                    entry.value = value
                    entry.updated_at = now
                    entry.expires_at = expires_at
                    entry.version += 1
                else:
                    # Create new
                    entry = StateEntry(
                        key=key,
                        value=value,
                        state_type=state_type,
                        created_at=now,
                        updated_at=now,
                        expires_at=expires_at
                    )
                    self.states[key] = entry
                
                logger.debug("Set state", key=key, ttl=ttl)
                return True
        except Exception as e:
            logger.error("Failed to set state", error=str(e), key=key)
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get state value."""
        async with self._lock:
            entry = self.states.get(key)
            if entry is None:
                return None
            if entry.is_expired():
                del self.states[key]
                return None
            return entry.value
    
    async def delete(self, key: str) -> bool:
        """Delete state."""
        async with self._lock:
            if key in self.states:
                del self.states[key]
                logger.debug("Deleted state", key=key)
                return True
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        async with self._lock:
            if key not in self.states:
                return False
            entry = self.states[key]
            if entry.is_expired():
                del self.states[key]
                return False
            return True
    
    async def get_all(self, pattern: str = "*") -> Dict[str, Any]:
        """Get all states matching pattern."""
        async with self._lock:
            # Simple pattern matching
            import fnmatch
            result = {}
            for key, entry in self.states.items():
                if fnmatch.fnmatch(key, pattern):
                    if not entry.is_expired():
                        result[key] = entry.value
                    else:
                        del self.states[key]
            return result
    
    async def increment(self, key: str, delta: int = 1) -> int:
        """Increment counter."""
        async with self._lock:
            current = await self.get(key) or 0
            new_value = current + delta
            await self.set(key, new_value)
            return new_value


class RedisStateManager(StateManager):
    """Redis-based state manager for production."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0",
                 prefix: str = "state"):
        self.redis_url = redis_url
        self.prefix = prefix
        self.redis = None
        logger.info("Initialized RedisStateManager", redis_url=redis_url)
    
    async def connect(self):
        """Connect to Redis."""
        try:
            import redis.asyncio as aioredis
            self.redis = aioredis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
            logger.info("Connected to Redis for state management")
        except ImportError:
            logger.error("redis package not installed")
            raise
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
            logger.info("Disconnected from Redis")
    
    def _make_key(self, key: str) -> str:
        """Create prefixed key."""
        return f"{self.prefix}:{key}"
    
    async def set(self, key: str, value: Any,
                  state_type: StateType = StateType.WORKFLOW,
                  ttl: Optional[int] = None) -> bool:
        """Set state in Redis."""
        try:
            if not self.redis:
                await self.connect()
            
            redis_key = self._make_key(key)
            
            # Store as JSON
            value_json = json.dumps(value)
            
            if ttl:
                await self.redis.setex(redis_key, ttl, value_json)
            else:
                await self.redis.set(redis_key, value_json)
            
            # Store metadata
            metadata_key = f"{redis_key}:meta"
            metadata = {
                'state_type': state_type.value,
                'updated_at': time.time()
            }
            await self.redis.hset(metadata_key, mapping=metadata)
            if ttl:
                await self.redis.expire(metadata_key, ttl)
            
            logger.debug("Set state in Redis", key=key, ttl=ttl)
            return True
            
        except Exception as e:
            logger.error("Failed to set state in Redis", error=str(e), key=key)
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get state from Redis."""
        try:
            if not self.redis:
                await self.connect()
            
            redis_key = self._make_key(key)
            value_json = await self.redis.get(redis_key)
            
            if value_json is None:
                return None
            
            return json.loads(value_json)
            
        except Exception as e:
            logger.error("Failed to get state from Redis", error=str(e), key=key)
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete state from Redis."""
        try:
            if not self.redis:
                await self.connect()
            
            redis_key = self._make_key(key)
            deleted = await self.redis.delete(redis_key, f"{redis_key}:meta")
            
            logger.debug("Deleted state from Redis", key=key, deleted=deleted)
            return deleted > 0
            
        except Exception as e:
            logger.error("Failed to delete state from Redis", error=str(e))
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        try:
            if not self.redis:
                await self.connect()
            
            redis_key = self._make_key(key)
            return await self.redis.exists(redis_key) > 0
            
        except Exception as e:
            logger.error("Failed to check existence in Redis", error=str(e))
            return False
    
    async def get_all(self, pattern: str = "*") -> Dict[str, Any]:
        """Get all states matching pattern from Redis."""
        try:
            if not self.redis:
                await self.connect()
            
            redis_pattern = self._make_key(pattern)
            result = {}
            
            async for key in self.redis.scan_iter(match=redis_pattern):
                if key.endswith(':meta'):
                    continue
                value_json = await self.redis.get(key)
                if value_json:
                    # Remove prefix
                    original_key = key[len(self.prefix) + 1:]
                    result[original_key] = json.loads(value_json)
            
            return result
            
        except Exception as e:
            logger.error("Failed to get all states from Redis", error=str(e))
            return {}
    
    async def increment(self, key: str, delta: int = 1) -> int:
        """Increment counter in Redis."""
        try:
            if not self.redis:
                await self.connect()
            
            redis_key = self._make_key(key)
            return await self.redis.incrby(redis_key, delta)
            
        except Exception as e:
            logger.error("Failed to increment in Redis", error=str(e))
            return 0
