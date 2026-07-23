"""
多线程与多进程 —— IO / CPU 密集对比。
函数名与教程示例对齐：io_bound_task / cpu_bound_task / run_serial / run_threads / run_processes
"""

from __future__ import annotations

import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

WORKERS = 4
IO_SLEEP = 0.4
CPU_LOOPS = 3_000_000


def io_bound_task(task_id: int) -> str:
    """模拟一次阻塞 IO：真正干活少，大部分时间在等。"""
    time.sleep(IO_SLEEP)
    return f"io-task-{task_id}-done"


def cpu_bound_task(task_id: int) -> int:
    """模拟纯 CPU 计算：几乎不 IO，一直在算。"""
    total = 0
    for i in range(CPU_LOOPS):
        total += i * i
    return total + task_id


def _run_serial(task, label_prefix: str) -> tuple[float, list[str]]:
    logs = [f"顺序执行：{WORKERS} 个任务依次进行"]
    t0 = time.perf_counter()
    for i in range(WORKERS):
        logs.append(f"serial worker-{i + 1}：开始")
        task(i)
        logs.append(f"serial worker-{i + 1}：完成")
    elapsed = time.perf_counter() - t0
    logs.append(f"顺序执行结束，耗时 {elapsed:.2f}s")
    return elapsed, logs


def _run_threads(task, kind: str) -> tuple[float, list[str]]:
    logs = [f"多线程：ThreadPoolExecutor，workers={WORKERS}（{kind}）"]
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for i in range(WORKERS):
            logs.append(f"thread-{i + 1}：已提交")
        # pool.map 返回惰性迭代器；list(...) 消费全部结果，确保计时覆盖「任务全部完成」
        list(pool.map(task, range(WORKERS)))
    elapsed = time.perf_counter() - t0
    logs.append(f"多线程结束，耗时 {elapsed:.2f}s")
    return elapsed, logs


def _run_processes(task, kind: str) -> tuple[float, list[str]]:
    logs = [f"多进程：ProcessPoolExecutor，workers={WORKERS}（{kind}）"]
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        for i in range(WORKERS):
            logs.append(f"process-{i + 1}：已提交")
        # 同上：list 强制等全部进程任务结束，再关闭进程池
        list(pool.map(task, range(WORKERS)))
    elapsed = time.perf_counter() - t0
    logs.append(f"多进程结束，耗时 {elapsed:.2f}s")
    return elapsed, logs


def run_io(mode: str) -> dict:
    if mode == "serial":
        elapsed, logs = _run_serial(io_bound_task, "io")
    elif mode == "threads":
        elapsed, logs = _run_threads(io_bound_task, "IO")
    elif mode == "processes":
        elapsed, logs = _run_processes(io_bound_task, "IO")
    else:
        raise ValueError(f"unknown mode: {mode}")
    return {"kind": "io", "mode": mode, "elapsed": round(elapsed, 4), "logs": logs}


def run_cpu(mode: str) -> dict:
    if mode == "serial":
        elapsed, logs = _run_serial(cpu_bound_task, "cpu")
    elif mode == "threads":
        elapsed, logs = _run_threads(cpu_bound_task, "CPU")
    elif mode == "processes":
        elapsed, logs = _run_processes(cpu_bound_task, "CPU")
    else:
        raise ValueError(f"unknown mode: {mode}")
    return {"kind": "cpu", "mode": mode, "elapsed": round(elapsed, 4), "logs": logs}
