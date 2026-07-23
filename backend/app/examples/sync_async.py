"""
同步与异步 —— 用 asyncio 对比同一批「等待型」任务。

同步：time.sleep 一个接一个，总耗时相加。
异步：asyncio.sleep + gather 并发等待，总耗时 ≈ 单次等待。
"""

from __future__ import annotations

import asyncio
import time

TASK_COUNT = 3
IO_SLEEP = 0.5


def fetch_sync(task_id: int) -> str:
    """同步模拟一次网络/IO 等待：阻塞当前线程。"""
    time.sleep(IO_SLEEP)
    return f"sync-task-{task_id}-done"


async def fetch_async(task_id: int) -> str:
    """异步模拟一次网络/IO 等待：挂起协程，事件循环可去跑别的任务。"""
    await asyncio.sleep(IO_SLEEP)
    return f"async-task-{task_id}-done"


def run_sync() -> dict:
    logs = [
        f"场景：同步顺序执行 {TASK_COUNT} 个等待任务",
        f"说明：每次 time.sleep({IO_SLEEP}) 都会堵住当前线程",
    ]
    t0 = time.perf_counter()
    results = []
    for i in range(TASK_COUNT):
        logs.append(f"同步任务-{i + 1}：开始")
        results.append(fetch_sync(i))
        logs.append(f"同步任务-{i + 1}：完成")
    elapsed = time.perf_counter() - t0
    logs.append(f"同步全部结束，耗时 {elapsed:.2f}s（≈ {TASK_COUNT} × {IO_SLEEP}）")
    return {
        "mode": "sync",
        "elapsed": round(elapsed, 4),
        "results": results,
        "logs": logs,
    }


async def _run_async_body() -> tuple[float, list[str], list[str]]:
    logs = [
        f"场景：异步并发执行 {TASK_COUNT} 个等待任务",
        "说明：asyncio.sleep 挂起协程；gather 让多个等待重叠",
    ]
    t0 = time.perf_counter()
    for i in range(TASK_COUNT):
        logs.append(f"异步任务-{i + 1}：已调度")
    results = await asyncio.gather(
        *(fetch_async(i) for i in range(TASK_COUNT)),
        return_exceptions=True,
    )
    elapsed = time.perf_counter() - t0
    for i, _ in enumerate(results):
        logs.append(f"异步任务-{i + 1}：完成")
    logs.append(f"异步全部结束，耗时 {elapsed:.2f}s（≈ 一次 {IO_SLEEP}，等待可重叠）")
    return elapsed, logs, list(results)


def run_async_mode() -> dict:
    elapsed, logs, results = asyncio.run(_run_async_body())
    return {
        "mode": "async",
        "elapsed": round(elapsed, 4),
        "results": results,
        "logs": logs,
    }


def run(mode: str) -> dict:
    if mode == "sync":
        return run_sync()
    if mode == "async":
        return run_async_mode()
    raise ValueError(f"unknown mode: {mode}")
