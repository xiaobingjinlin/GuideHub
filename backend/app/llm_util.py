"""
从环境变量读取大模型（通义千问 / OpenAI 兼容）配置。

本地需已配置：
  QWEN_API_KEY   API Key
  QWEN_BASE_URL  兼容 OpenAI 的接口根地址

可选：
  QWEN_MODEL           默认文本模型（兼容旧用法）
  QWEN_MODEL_TEXT      文本对话模型，默认 qwen3.7-plus
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class LlmConfig:
    api_key: str
    base_url: str
    model: str = "qwen3.7-plus"


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(
            f"缺少环境变量 {name}。请在本地配置后重启后端进程。"
        )
    return value


def get_qwen_config(*, model: str | None = None) -> LlmConfig:
    """读取 Qwen 相关环境变量；可传入 model 覆盖默认。"""
    default_model = (
        os.getenv("QWEN_MODEL_TEXT")
        or os.getenv("QWEN_MODEL")
        or "qwen3.7-plus"
    ).strip() or "qwen3.7-plus"
    return LlmConfig(
        api_key=_require_env("QWEN_API_KEY"),
        base_url=_require_env("QWEN_BASE_URL").rstrip("/"),
        model=(model or default_model).strip() or default_model,
    )


def get_llm_config(*, model: str | None = None) -> LlmConfig:
    """通用入口：当前即 Qwen 配置。"""
    return get_qwen_config(model=model)
