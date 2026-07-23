"""
主线程与子线程 —— 单线程 vs 主子线程。

对比同一份工作：
1. with 阻塞逻辑（线程池 + sleep）
2. 主线程后续业务（模拟 UI / 业务继续跑）

单线程：先 with 再业务 → 主线程全程串行，总时长相加，with 期间完全阻塞。
主子线程：daemon 子线程跑 with，主线程并行做业务 → 总墙钟 ≈ max，主线程几乎不被 with 卡住。
"""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor

WORKERS = 4
IO_SLEEP = 0.4
MAIN_WORK_SLEEP = 0.5


def with_blocking_work() -> None:
    """
    with 会阻塞「当前线程」：
    只有线程池任务全部结束，才会离开 with 代码块。
    """
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda _i: time.sleep(IO_SLEEP), range(WORKERS)))


def main_business_work() -> None:
    """模拟主线程上的后续业务（例如刷新界面、继续处理请求）。"""
    time.sleep(MAIN_WORK_SLEEP)


def run_single() -> dict:
    """单线程：with 与业务串行，主线程被 with 整段堵住。"""
    logs = [
        "场景：单线程顺序执行",
        "步骤：先跑 with 阻塞逻辑，再跑主线程业务",
    ]
    t0 = time.perf_counter()

    logs.append("主线程：进入 with …")
    t_with = time.perf_counter()
    with_blocking_work()
    with_elapsed = time.perf_counter() - t_with
    logs.append(f"主线程：离开 with（阻塞约 {with_elapsed:.2f}s，期间干不了别的）")

    logs.append("主线程：开始后续业务 …")
    t_biz = time.perf_counter()
    main_business_work()
    biz_elapsed = time.perf_counter() - t_biz
    logs.append(f"主线程：业务结束（约 {biz_elapsed:.2f}s）")

    elapsed = time.perf_counter() - t0
    logs.append(
        f"结论：总耗时 ≈ with + 业务 = {with_elapsed:.2f}+{biz_elapsed:.2f} ≈ {elapsed:.2f}s；"
        f"主线程被 with 阻塞 {with_elapsed:.2f}s"
    )
    return {
        "mode": "single",
        "elapsed": round(elapsed, 4),
        "blocked": round(with_elapsed, 4),
        "with_elapsed": round(with_elapsed, 4),
        "business_elapsed": round(biz_elapsed, 4),
        "logs": logs,
    }


def run_main_child() -> dict:
    """
    主子线程：daemon 子线程执行 with，主线程并行做业务。
    daemon=True：主程序退出时子线程会被粗暴回收。
    """
    logs: list[str] = [
        "场景：主子线程并行",
        "说明：子线程 daemon=True，主程序退出时子线程会被直接回收",
    ]
    child_elapsed_box: list[float] = []

    def target() -> None:
        t_child = time.perf_counter()
        logs.append("子线程：进入 with …")
        with_blocking_work()
        child_elapsed_box.append(time.perf_counter() - t_child)
        logs.append(f"子线程：离开 with（约 {child_elapsed_box[-1]:.2f}s）")

    t0 = time.perf_counter()
    thread = threading.Thread(target=target, name="with-worker", daemon=True)
    thread.start()
    spawn_cost = time.perf_counter() - t0
    logs.append(f"主线程：已启动子线程（约 {spawn_cost:.4f}s，几乎不阻塞）")

    logs.append("主线程：同步开始后续业务 …")
    t_biz = time.perf_counter()
    main_business_work()
    biz_elapsed = time.perf_counter() - t_biz
    logs.append(f"主线程：业务结束（约 {biz_elapsed:.2f}s，与子线程 with 重叠）")

    # 演示需等任务做完再比总效率；真实退出场景通常不 join daemon
    thread.join()
    with_elapsed = child_elapsed_box[0] if child_elapsed_box else 0.0
    elapsed = time.perf_counter() - t0
    # 主线程被 with「卡住」的时间：仅启动开销（业务与 with 并行）
    blocked = spawn_cost

    logs.append(
        "提示：若主程序此时直接退出且未 join，daemon 子线程可能被粗暴打断、来不及收尾"
    )
    logs.append(
        f"结论：总耗时 ≈ max(with, 业务) ≈ {elapsed:.2f}s；"
        f"主线程几乎不被 with 阻塞（约 {blocked:.4f}s）"
    )
    return {
        "mode": "main_child",
        "elapsed": round(elapsed, 4),
        "blocked": round(blocked, 4),
        "with_elapsed": round(with_elapsed, 4),
        "business_elapsed": round(biz_elapsed, 4),
        "logs": logs,
    }


def run(mode: str) -> dict:
    if mode == "single":
        return run_single()
    if mode == "main_child":
        return run_main_child()
    raise ValueError(f"unknown mode: {mode}")
