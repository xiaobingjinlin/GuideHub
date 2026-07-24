"""
文本对话示例共用常量与护栏（LangChain / LangGraph 非图逻辑）。

含：默认模型名、字数护栏、TurnResult。
"""

from __future__ import annotations

from dataclasses import dataclass

from langchain.messages import trim_messages
from langchain_core.messages import BaseMessage

# 对话主模型（摘要模型见 chat_compress.SUMMARY_MODEL）
TEXT_MODEL = "qwen3.7-plus"

# 送入模型前的上下文护栏（按字符粗估；中文约 1～2 字/token，取偏保守预算）
CONTEXT_MAX_CHARS = 24_000


@dataclass
class TurnResult:
    """
    单轮对话结束后的聚合结果，供 Gradio UI 刷新气泡与右侧历史。

    Attributes:
        reply: 本轮助手最终回复文本（不含思考过程；思考由 UI 流式展示）。
        history_text: 格式化后的对话历史纯文本。
        compressed: 本轮结束后是否触发了混合压缩。
        pair_count: 当前会话轮数（一轮 = HumanMessage + AIMessage）。
    """

    reply: str
    history_text: str
    compressed: bool
    pair_count: int


def _char_budget_counter(messages: list[BaseMessage]) -> int:
    """粗估上下文占用：按消息 content 字符数求和（作 trim_messages 的 token_counter）。"""
    total = 0
    for m in messages:
        content = getattr(m, "content", "") or ""
        total += len(str(content))
    return total


def guard_prompt_messages(messages: list[BaseMessage]) -> list[BaseMessage]:
    """
    token/字数护栏：超长时从尾部保留，尽量保持 Human 对齐边界，并始终保留 system。

    混合压缩（chat_compress）负责「轮数」窗口；本函数负责「单次请求体积」兜底。
    只返回送模型的副本，不写回会话存储。
    """
    return trim_messages(
        messages,
        max_tokens=CONTEXT_MAX_CHARS,
        strategy="last",
        token_counter=_char_budget_counter,
        start_on="human",
        include_system=True,
        allow_partial=False,
    )
