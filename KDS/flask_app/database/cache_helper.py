import time
from functools import wraps
import threading

def ttl_cache(maxsize=128, ttl=300):
    """
    A simple thread-safe time-to-live cache decorator.
    Caches the results of a function for `ttl` seconds.
    `maxsize` limits the number of cached entries.
    """
    cache = {}
    lock = threading.Lock()

    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            # Create a hashable key from args and kwargs
            # Dictionaries and lists in kwargs must be handled, but for our simple SQL 
            # queries, args are mostly strings/ints.
            # Handle list arguments by converting them to tuples for hashing.
            hashable_args = tuple(tuple(x) if isinstance(x, list) else x for x in args)
            hashable_kwargs = frozenset((k, tuple(v) if isinstance(v, list) else v) for k, v in kwargs.items())
            key = (hashable_args, hashable_kwargs)

            with lock:
                if key in cache:
                    result, timestamp = cache[key]
                    if time.time() - timestamp < ttl:
                        # Return a copy if it's a pandas DataFrame to prevent mutation
                        if hasattr(result, 'copy'):
                            return result.copy()
                        return result
                    else:
                        del cache[key]

            # Cache miss or expired
            result = fn(*args, **kwargs)

            with lock:
                # Evict oldest if cache is full
                if len(cache) >= maxsize:
                    oldest_key = min(cache.keys(), key=lambda k: cache[k][1])
                    del cache[oldest_key]
                cache[key] = (result, time.time())

            if hasattr(result, 'copy'):
                return result.copy()
            return result
        
        # Expose cache clearing method
        wrapped.cache_clear = lambda: cache.clear()
        return wrapped
    return decorator
