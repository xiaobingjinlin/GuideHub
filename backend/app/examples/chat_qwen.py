"""通义 Qwen3：ChatQwen 工厂与流式 content 解析（LangChain / LangGraph 共用）。"""

from __future__ import annotations

from langchain_qwq import ChatQwen

from app.llm_util import get_qwen_config


def build_chat_qwen(
    *,
    model: str | None = None,
    enable_thinking: bool = True,
    temperature: float | None = None,
) -> ChatQwen:
    """
    创建 ``ChatQwen``（Qwen3 用这个；``ChatQwQ`` 面向 qwq/qvq）。

    ``enable_thinking`` 会写入 extra_body；流式思考在
    ``chunk.additional_kwargs['reasoning_content']``。
    """
    cfg = get_qwen_config(model=model)
    if temperature is None:
        temperature = 0.6 if enable_thinking else 0.7
    return ChatQwen(
        model=cfg.model,
        api_key=cfg.api_key,
        base_url=cfg.base_url,
        temperature=temperature,
        enable_thinking=bool(enable_thinking),
    )


def chunk_text(content: object) -> str:
    """把 AIMessageChunk.content（str 或 content blocks）收成纯文本。"""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text") or ""))
        return "".join(parts)
    return str(content)
