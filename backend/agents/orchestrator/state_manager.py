"""
Distributed State Manager for Multi-Agent Systems
Handles state persistence, synchronization, and recovery.
"""
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import asyncio
import structlog

logger = structlog.get_logger()


class StateScope(Enum):
    """State visibility scope."""
    AGENT = "agent"  # Agent-local state
    WORKFLOW = "workflow"  # Workflow-level state
    GLOBAL = "global"  # System-wide state


class StateVersion(Enum):
    """State versioning strategy."""
    NONE = "none"  # No versioning
    TIMESTAMP = "timestamp"  # Timestamp-based
    SEQUENTIAL = "sequential"  # Sequential version numbers


@dataclass
class StateEntry:
    """State entry with metadata."""
    key: str
    value: Any
    scope: StateScope
    owner: str  # Agent or workflow ID
    version: int = 1
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'key': self.key,
            'value': self.value,
            'scope': self.scope.value,
            'owner': self.owner,
            'version': self.version,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateEntry':
        """Create from dictionary."""
        entry = cls(
            key=data['key'],
            value=data['value'],
            scope=StateScope(data['scope']),
            owner=data['owner'],
            version=data.get('version', 1),
            metadata=data.get('metadata', {})
        )
        
        if data.get('created_at'):
            entry.created_at = datetime.fromisoformat(data['created_at'])
        if data.get('updated_at'):
            entry.updated_at = datetime.fromisoformat(data['updated_at'])
        if data.get('expires_at'):
            entry.expires_at = datetime.fromisoformat(data['expires_at'])
        
        return entry


class StateBackend:
    """Abstract state backend."""
    
    async def get(self, key: str) -> Optional[StateEntry]:
        """Get state entry."""
        raise NotImplementedError
    
    async def set(self, entry: StateEntry) -> bool:
        """Set state entry."""
        raise NotImplementedError
    
    async def delete(self, key: str) -> bool:
        """Delete state entry."""
        raise NotImplementedError
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        raise NotImplementedError
    
    async def keys(self, pattern: Optional[str] = None) -> List[str]:
        """Get all keys matching pattern."""
        raise NotImplementedError


class InMemoryStateBackend(StateBackend):
    """In-memory state backend."""
    
    def __init__(self):
        self.store: Dict[str, StateEntry] = {}
        self.lock = asyncio.Lock()
        logger.info("Initialized in-memory state backend")
    
    async def get(self, key: str) -> Optional[StateEntry]:
        """Get state entry."""
        async with self.lock:
            entry = self.store.get(key)
            
            # Check expiration
            if entry and entry.expires_at and datetime.now() > entry.expires_at:
                del self.store[key]
                return None
            
            return entry
    
    async def set(self, entry: StateEntry) -> bool:
        """Set state entry."""
        async with self.lock:
            entry.updated_at = datetime.now()
            self.store[entry.key] = entry
            return True
    
    async def delete(self, key: str) -> bool:
        """Delete state entry."""
        async with self.lock:
            if key in self.store:
                del self.store[key]
                return True
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        return await self.get(key) is not None
    
    async def keys(self, pattern: Optional[str] = None) -> List[str]:
        """Get all keys matching pattern."""
        async with self.lock:
            all_keys = list(self.store.keys())
            
            if pattern:
                # Simple glob pattern matching
                import fnmatch
                return [k for k in all_keys if fnmatch.fnmatch(k, pattern)]
            
            return all_keys


class RedisStateBackend(StateBackend):
    """Redis-based state backend."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """Initialize Redis backend."""
        try:
            import redis.asyncio as aioredis
            self.redis = aioredis.from_url(redis_url, decode_responses=False)
            logger.info("Initialized Redis state backend", url=redis_url)
        except ImportError:
            logger.error("redis package not installed")
            raise
    
    def _state_key(self, key: str) -> str:
        """Get Redis key for state."""
        return f"state:{key}"
    
    async def get(self, key: str) -> Optional[StateEntry]:
        """Get state entry."""
        try:
            redis_key = self._state_key(key)
            data = await self.redis.get(redis_key)
            
            if data:
                entry = StateEntry.from_dict(json.loads(data))
                
                # Check expiration
                if entry.expires_at and datetime.now() > entry.expires_at:
                    await self.delete(key)
                    return None
                
                return entry
            
            return None
        except Exception as e:
            logger.error("Failed to get state from Redis", key=key, error=str(e))
            return None
    
    async def set(self, entry: StateEntry) -> bool:
        """Set state entry."""
        try:
            entry.updated_at = datetime.now()
            redis_key = self._state_key(entry.key)
            data = json.dumps(entry.to_dict())
            
            await self.redis.set(redis_key, data)
            
            # Set TTL if expires_at is set
            if entry.expires_at:
                ttl = int((entry.expires_at - datetime.now()).total_seconds())
                if ttl > 0:
                    await self.redis.expire(redis_key, ttl)
            
            return True
        except Exception as e:
            logger.error("Failed to set state in Redis", key=entry.key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete state entry."""
        try:
            redis_key = self._state_key(key)
            result = await self.redis.delete(redis_key)
            return result > 0
        except Exception as e:
            logger.error("Failed to delete state from Redis", key=key, error=str(e))
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        try:
            redis_key = self._state_key(key)
            return await self.redis.exists(redis_key) > 0
        except Exception as e:
            logger.error("Failed to check existence in Redis", key=key, error=str(e))
            return False
    
    async def keys(self, pattern: Optional[str] = None) -> List[str]:
        """Get all keys matching pattern."""
        try:
            redis_pattern = f"state:{pattern if pattern else '*'}"
            keys = await self.redis.keys(redis_pattern)
            
            # Strip state: prefix
            return [k.decode('utf-8').replace('state:', '') for k in keys]
        except Exception as e:
            logger.error("Failed to get keys from Redis", error=str(e))
            return []
    
    async def close(self):
        """Close Redis connection."""
        await self.redis.close()


class StateManager:
    """
    Distributed state manager for multi-agent systems.
    
    Features:
    - Multiple scope levels (agent, workflow, global)
    - State versioning and conflict resolution
    - Automatic expiration
    - State snapshots and rollback
    - Change notifications
    """
    
    def __init__(
        self,
        backend: Optional[StateBackend] = None,
        enable_versioning: bool = True,
        default_ttl: Optional[int] = None
    ):
        """Initialize state manager.
        
        Args:
            backend: State backend (in-memory or Redis)
            enable_versioning: Enable state versioning
            default_ttl: Default TTL for state entries (seconds)
        """
        self.backend = backend or InMemoryStateBackend()
        self.enable_versioning = enable_versioning
        self.default_ttl = default_ttl
        
        # Change listeners
        self.listeners: Dict[str, List[callable]] = {}
        
        # Statistics
        self.stats = {
            'get_count': 0,
            'set_count': 0,
            'delete_count': 0,
            'version_conflicts': 0
        }
        
        logger.info(
            "State manager initialized",
            backend=type(self.backend).__name__,
            versioning=enable_versioning
        )
    
    def _make_key(self, scope: StateScope, owner: str, key: str) -> str:
        """Create full key from scope, owner, and key.
        
        Args:
            scope: State scope
            owner: Owner (agent/workflow ID)
            key: Key name
            
        Returns:
            Full key
        """
        return f"{scope.value}:{owner}:{key}"
    
    async def get(
        self,
        key: str,
        scope: StateScope = StateScope.AGENT,
        owner: str = ""
    ) -> Optional[Any]:
        """Get state value.
        
        Args:
            key: State key
            scope: State scope
            owner: Owner ID
            
        Returns:
            State value or None
        """
        full_key = self._make_key(scope, owner, key)
        entry = await self.backend.get(full_key)
        
        self.stats['get_count'] += 1
        
        if entry:
            logger.debug(
                "State retrieved",
                key=key,
                scope=scope.value,
                owner=owner,
                version=entry.version
            )
            return entry.value
        
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        scope: StateScope = StateScope.AGENT,
        owner: str = "",
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Set state value.
        
        Args:
            key: State key
            value: State value
            scope: State scope
            owner: Owner ID
            ttl: Time to live (seconds)
            metadata: Additional metadata
            
        Returns:
            Success status
        """
        full_key = self._make_key(scope, owner, key)
        
        # Get existing entry for versioning
        existing = await self.backend.get(full_key)
        version = 1
        
        if existing and self.enable_versioning:
            version = existing.version + 1
        
        # Create entry
        entry = StateEntry(
            key=full_key,
            value=value,
            scope=scope,
            owner=owner,
            version=version,
            metadata=metadata or {}
        )
        
        # Set expiration
        if ttl or self.default_ttl:
            entry.expires_at = datetime.now() + timedelta(seconds=ttl or self.default_ttl)
        
        # Save to backend
        success = await self.backend.set(entry)
        
        if success:
            self.stats['set_count'] += 1
            
            logger.debug(
                "State updated",
                key=key,
                scope=scope.value,
                owner=owner,
                version=version
            )
            
            # Notify listeners
            await self._notify_listeners(full_key, value, 'set')
        
        return success
    
    async def delete(
        self,
        key: str,
        scope: StateScope = StateScope.AGENT,
        owner: str = ""
    ) -> bool:
        """Delete state value.
        
        Args:
            key: State key
            scope: State scope
            owner: Owner ID
            
        Returns:
            Success status
        """
        full_key = self._make_key(scope, owner, key)
        success = await self.backend.delete(full_key)
        
        if success:
            self.stats['delete_count'] += 1
            
            logger.debug(
                "State deleted",
                key=key,
                scope=scope.value,
                owner=owner
            )
            
            # Notify listeners
            await self._notify_listeners(full_key, None, 'delete')
        
        return success
    
    async def exists(
        self,
        key: str,
        scope: StateScope = StateScope.AGENT,
        owner: str = ""
    ) -> bool:
        """Check if state exists.
        
        Args:
            key: State key
            scope: State scope
            owner: Owner ID
            
        Returns:
            True if exists
        """
        full_key = self._make_key(scope, owner, key)
        return await self.backend.exists(full_key)
    
    async def get_all(
        self,
        scope: Optional[StateScope] = None,
        owner: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get all state values matching criteria.
        
        Args:
            scope: Filter by scope
            owner: Filter by owner
            
        Returns:
            Dictionary of key -> value
        """
        # Build pattern
        pattern_parts = []
        if scope:
            pattern_parts.append(scope.value)
        else:
            pattern_parts.append('*')
        
        if owner:
            pattern_parts.append(owner)
        else:
            pattern_parts.append('*')
        
        pattern_parts.append('*')
        pattern = ':'.join(pattern_parts)
        
        # Get matching keys
        keys = await self.backend.keys(pattern)
        
        # Get all values
        result = {}
        for full_key in keys:
            entry = await self.backend.get(full_key)
            if entry:
                # Extract original key (remove scope and owner prefix)
                parts = full_key.split(':', 2)
                if len(parts) == 3:
                    result[parts[2]] = entry.value
        
        return result
    
    async def get_entry(
        self,
        key: str,
        scope: StateScope = StateScope.AGENT,
        owner: str = ""
    ) -> Optional[StateEntry]:
        """Get full state entry with metadata.
        
        Args:
            key: State key
            scope: State scope
            owner: Owner ID
            
        Returns:
            State entry or None
        """
        full_key = self._make_key(scope, owner, key)
        return await self.backend.get(full_key)
    
    async def compare_and_set(
        self,
        key: str,
        expected_version: int,
        new_value: Any,
        scope: StateScope = StateScope.AGENT,
        owner: str = ""
    ) -> bool:
        """Atomic compare-and-set operation.
        
        Args:
            key: State key
            expected_version: Expected current version
            new_value: New value to set
            scope: State scope
            owner: Owner ID
            
        Returns:
            True if set successful, False if version mismatch
        """
        full_key = self._make_key(scope, owner, key)
        entry = await self.backend.get(full_key)
        
        if entry and entry.version != expected_version:
            self.stats['version_conflicts'] += 1
            logger.warning(
                "Version conflict",
                key=key,
                expected=expected_version,
                actual=entry.version
            )
            return False
        
        return await self.set(key, new_value, scope, owner)
    
    def subscribe(self, key: str, callback: callable):
        """Subscribe to state changes.
        
        Args:
            key: State key pattern to watch
            callback: Callback function(key, value, operation)
        """
        if key not in self.listeners:
            self.listeners[key] = []
        
        self.listeners[key].append(callback)
        
        logger.debug("Subscribed to state changes", key=key)
    
    def unsubscribe(self, key: str, callback: callable):
        """Unsubscribe from state changes.
        
        Args:
            key: State key pattern
            callback: Callback function to remove
        """
        if key in self.listeners and callback in self.listeners[key]:
            self.listeners[key].remove(callback)
            logger.debug("Unsubscribed from state changes", key=key)
    
    async def _notify_listeners(self, key: str, value: Any, operation: str):
        """Notify listeners of state change.
        
        Args:
            key: State key
            value: New value
            operation: Operation (set/delete)
        """
        for pattern, callbacks in self.listeners.items():
            # Simple pattern matching
            import fnmatch
            if fnmatch.fnmatch(key, pattern):
                for callback in callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(key, value, operation)
                        else:
                            callback(key, value, operation)
                    except Exception as e:
                        logger.error(
                            "Error in state change listener",
                            key=key,
                            error=str(e)
                        )
    
    async def create_snapshot(self, scope: StateScope, owner: str) -> Dict[str, Any]:
        """Create snapshot of all state for scope and owner.
        
        Args:
            scope: State scope
            owner: Owner ID
            
        Returns:
            Dictionary of state
        """
        return await self.get_all(scope=scope, owner=owner)
    
    async def restore_snapshot(
        self,
        snapshot: Dict[str, Any],
        scope: StateScope,
        owner: str
    ) -> bool:
        """Restore state from snapshot.
        
        Args:
            snapshot: State snapshot
            scope: State scope
            owner: Owner ID
            
        Returns:
            Success status
        """
        try:
            for key, value in snapshot.items():
                await self.set(key, value, scope, owner)
            
            logger.info(
                "State snapshot restored",
                scope=scope.value,
                owner=owner,
                count=len(snapshot)
            )
            return True
        except Exception as e:
            logger.error("Failed to restore snapshot", error=str(e))
            return False
    
    def get_stats(self) -> Dict[str, int]:
        """Get state manager statistics.
        
        Returns:
            Statistics dictionary
        """
        return self.stats.copy()


# Helper functions

def create_state_manager(
    use_redis: bool = False,
    redis_url: str = "redis://localhost:6379/0",
    **kwargs
) -> StateManager:
    """Create state manager with appropriate backend.
    
    Args:
        use_redis: Use Redis backend
        redis_url: Redis connection URL
        **kwargs: Additional arguments for StateManager
        
    Returns:
        State manager instance
    """
    if use_redis:
        backend = RedisStateBackend(redis_url)
    else:
        backend = InMemoryStateBackend()
    
    return StateManager(backend=backend, **kwargs)


# Global instance
_global_state_manager: Optional[StateManager] = None


def get_global_state_manager() -> StateManager:
    """Get global state manager instance."""
    global _global_state_manager
    if _global_state_manager is None:
        _global_state_manager = create_state_manager()
    return _global_state_manager


def set_global_state_manager(manager: StateManager):
    """Set global state manager instance."""
    global _global_state_manager
    _global_state_manager = manager
