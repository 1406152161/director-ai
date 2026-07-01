# @author zhangzhihao
"""Celery 任务内运行 async 协程。"""

import asyncio
import concurrent.futures
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def run_async(coro_factory: Callable[..., Awaitable[T]], *args, **kwargs) -> T:
    coro = coro_factory(*args, **kwargs)
    try:
        asyncio.get_running_loop()
        nested_loop = True
    except RuntimeError:
        nested_loop = False

    try:
        if not nested_loop:
            return asyncio.run(coro)
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(asyncio.run, coro).result()
    except Exception:
        logger.exception("Celery async task failed: %s", coro_factory.__name__)
        raise
