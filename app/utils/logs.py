import logging
import time
from functools import wraps
from logging import Logger
from typing import Callable, Any

logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def log_execution_time(logger: Logger) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter() - start_time
            logger.info('function execution time: %.3f', end_time - start_time)
            return result
        return wrapper
    return decorator




