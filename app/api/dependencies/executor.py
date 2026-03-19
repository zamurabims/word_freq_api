import os
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache

# Количество воркеров = CPU / 2, минимум 1, максимум 4.
# Оставляем ресурсы uvicorn и event loop'у.
_WORKER_COUNT = max(1, min(4, (os.cpu_count() or 2) // 2))

_executor: ProcessPoolExecutor | None = None


def get_executor() -> ProcessPoolExecutor:
    global _executor
    if _executor is None:
        _executor = ProcessPoolExecutor(max_workers=_WORKER_COUNT)
    return _executor


def shutdown_executor() -> None:
    global _executor
    if _executor:
        _executor.shutdown(wait=False)
        _executor = None
