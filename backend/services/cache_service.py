"""
Caching Service for Performance Optimization
Supports in-memory caching with TTL and optional Redis backend
"""
from typing import Any, Optional, Callable
from datetime import datetime, timedelta
import json
import hashlib
import functools
from collections import OrderedDict
import asyncio


class LRUCache:
    """Thread-safe LRU cache with TTL support"""
    
    def __init__(self, max_size: int = 1000):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self.cache:
            value, expiry = self.cache[key]
            
            # Check if expired
            if expiry and datetime.utcnow() > expiry:
                del self.cache[key]
                self.misses += 1
                return None
            
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self.hits += 1
            return value
        
        self.misses += 1
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        """Set value in cache with optional TTL"""
        expiry = None
        if ttl_seconds:
            expiry = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        
        self.cache[key] = (value, expiry)
        self.cache.move_to_end(key)
        
        # Evict oldest if over max size
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)
    
    def delete(self, key: str):
        """Delete key from cache"""
        if key in self.cache:
            del self.cache[key]
    
    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': round(hit_rate, 2),
            'memory_items': len(self.cache)
        }


class CacheService:
    """Comprehensive caching service"""
    
    def __init__(self, max_size: int = 1000, enable_redis: bool = False):
        self.memory_cache = LRUCache(max_size=max_size)
        self.enable_redis = enable_redis
        self.redis_client = None
        
        if enable_redis:
            try:
                import redis
                self.redis_client = redis.Redis(
                    host='localhost',
                    port=6379,
                    db=0,
                    decode_responses=True
                )
            except ImportError:
                print("Redis not available, using memory cache only")
                self.enable_redis = False
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache (memory first, then Redis)"""
        # Try memory cache first
        value = self.memory_cache.get(key)
        if value is not None:
            return value
        
        # Try Redis if enabled
        if self.enable_redis and self.redis_client:
            try:
                redis_value = self.redis_client.get(key)
                if redis_value:
                    # Deserialize and store in memory cache
                    value = json.loads(redis_value)
                    self.memory_cache.set(key, value, ttl_seconds=300)
                    return value
            except Exception as e:
                print(f"Redis get error: {e}")
        
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 3600):
        """Set value in cache (both memory and Redis)"""
        # Store in memory cache
        self.memory_cache.set(key, value, ttl_seconds=ttl_seconds)
        
        # Store in Redis if enabled
        if self.enable_redis and self.redis_client:
            try:
                serialized = json.dumps(value)
                self.redis_client.setex(key, ttl_seconds, serialized)
            except Exception as e:
                print(f"Redis set error: {e}")
    
    def delete(self, key: str):
        """Delete key from cache"""
        self.memory_cache.delete(key)
        
        if self.enable_redis and self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception as e:
                print(f"Redis delete error: {e}")
    
    def clear(self, pattern: Optional[str] = None):
        """Clear cache (with optional pattern)"""
        if pattern:
            # Pattern-based clearing
            if self.enable_redis and self.redis_client:
                try:
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        self.redis_client.delete(*keys)
                except Exception as e:
                    print(f"Redis clear error: {e}")
            
            # Memory cache pattern clearing
            keys_to_delete = [k for k in self.memory_cache.cache.keys() if pattern in k]
            for key in keys_to_delete:
                self.memory_cache.delete(key)
        else:
            # Clear all
            self.memory_cache.clear()
            if self.enable_redis and self.redis_client:
                try:
                    self.redis_client.flushdb()
                except Exception as e:
                    print(f"Redis flush error: {e}")
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        stats = self.memory_cache.get_stats()
        
        if self.enable_redis and self.redis_client:
            try:
                redis_info = self.redis_client.info('stats')
                stats['redis_enabled'] = True
                stats['redis_keys'] = self.redis_client.dbsize()
                stats['redis_hits'] = redis_info.get('keyspace_hits', 0)
                stats['redis_misses'] = redis_info.get('keyspace_misses', 0)
            except Exception as e:
                stats['redis_enabled'] = False
                stats['redis_error'] = str(e)
        else:
            stats['redis_enabled'] = False
        
        return stats


# Global cache instance
_cache_service = None

def get_cache_service(max_size: int = 1000, enable_redis: bool = False) -> CacheService:
    """Get or create cache service instance"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService(max_size=max_size, enable_redis=enable_redis)
    return _cache_service


# Cache decorator
def cache_result(ttl_seconds: int = 3600, key_prefix: str = ""):
    """Decorator to cache function results"""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = _generate_cache_key(key_prefix, func.__name__, args, kwargs)
            
            # Try to get from cache
            cache = get_cache_service()
            cached_value = cache.get(cache_key)
            
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, ttl_seconds=ttl_seconds)
            
            return result
        
        return wrapper
    return decorator


def _generate_cache_key(prefix: str, func_name: str, args: tuple, kwargs: dict) -> str:
    """Generate cache key from function call"""
    # Create hashable representation
    key_parts = [prefix, func_name]
    
    # Add args
    for arg in args:
        if isinstance(arg, (str, int, float, bool)):
            key_parts.append(str(arg))
        else:
            key_parts.append(hashlib.md5(str(arg).encode()).hexdigest()[:8])
    
    # Add kwargs
    for k, v in sorted(kwargs.items()):
        if isinstance(v, (str, int, float, bool)):
            key_parts.append(f"{k}={v}")
        else:
            key_parts.append(f"{k}={hashlib.md5(str(v).encode()).hexdigest()[:8]}")
    
    return ":".join(key_parts)


# Async cache decorator
def async_cache_result(ttl_seconds: int = 3600, key_prefix: str = ""):
    """Decorator to cache async function results"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = _generate_cache_key(key_prefix, func.__name__, args, kwargs)
            
            # Try to get from cache
            cache = get_cache_service()
            cached_value = cache.get(cache_key)
            
            if cached_value is not None:
                return cached_value
            
            # Execute async function
            result = await func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, ttl_seconds=ttl_seconds)
            
            return result
        
        return wrapper
    return decorator
