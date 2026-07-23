"""
文件读写 —— 用 with + open() 读写持久化文本文件。

路径与教程代码一致：与本模块同目录的 memo.txt；页面刷新后内容仍在。
"""

from __future__ import annotations

from pathlib import Path

# 与教程代码相同：文件放在本模块同目录
FILE_PATH = Path(__file__).resolve().parent / "memo.txt"
DEFAULT_LINE = "GuideHub：用 with 和 open() 读写文件。"


def ensure_file() -> None:
    """文件不存在则先创建空文件。"""
    if not FILE_PATH.exists():
        with open(FILE_PATH, "w", encoding="utf-8") as f:
            f.write("")


def read_content() -> str:
    """用 with + open 读出全部文本。"""
    ensure_file()
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        return f.read()


def append_line(line: str | None = None) -> dict:
    """
    追加一句话：
    - 文件为空（第一段）：直接写入
    - 已有内容：与上一段空一行再写
    """
    text = (line if line is not None else DEFAULT_LINE).rstrip("\n")
    current = read_content()

    if current.strip() == "":
        new_content = text
        logs = ["文件为空：作为第一段直接写入"]
    else:
        new_content = current.rstrip("\n") + "\n\n" + text
        logs = ["文件已有内容：与上一段空一行后追加"]

    with open(FILE_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)

    logs.append(f"已写入：{text}")
    logs.append(f"路径：{FILE_PATH}")
    return {
        "content": new_content,
        "line": text,
        "path": str(FILE_PATH),
        "logs": logs,
    }


def reset_content() -> dict:
    """清空文件并保存（写空字符串）。"""
    ensure_file()
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        f.write("")
    return {
        "content": "",
        "path": str(FILE_PATH),
        "logs": ["已清空文件并保存", f"路径：{FILE_PATH}"],
    }


def get_content() -> dict:
    content = read_content()
    return {
        "content": content,
        "line": DEFAULT_LINE,
        "path": str(FILE_PATH),
        "logs": [f"已读取文件（{len(content)} 字符）", f"路径：{FILE_PATH}"],
    }
