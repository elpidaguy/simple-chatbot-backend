import asyncio

# Simple concurrency limiter for model calls
_semaphore = asyncio.Semaphore(10)


def get_semaphore():
    return _semaphore
