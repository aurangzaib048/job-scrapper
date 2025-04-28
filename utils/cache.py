from cacheout import Cache

cache = Cache(maxsize=1000)


def get_from_cache(key):
    """Get filters from cache"""
    return cache.get(key)


def set_to_cache(key, value):
    """Set filters in cache"""
    cache.set(key, value)
