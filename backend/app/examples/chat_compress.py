"""
对话压缩 + 历史展示辅助（混合策略）。

设计目标：把对话窗口控制在约 10–20 轮，避免上下文无限膨胀。

规则（一轮 = HumanMessage + AIMessage）：
- 未满 MAX_PAIRS（20）轮：不压缩，原样返回；
- 达到 20 轮时：
  1. 最近 KEEP_RECENT_PAIRS（9）轮原样保留；
  2. 从尾部数第 10 轮：HumanMessage 不变，其 AIMessage 换成「更早内容」的摘要；
  3. 摘要由 SUMMARY_MODEL（qwen3.6-flash / ChatQwen）生成，长度不超过 SUMMARY_MAX_CHARS（1000）字。
"""

from __future__ import annotations

from langchain.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.messages import BaseMessage

from app.examples.chat_qwen import build_chat_qwen, chunk_text

MAX_PAIRS = 20
KEEP_RECENT_PAIRS = 9
SUMMARY_MAX_CHARS = 1000
SUMMARY_MODEL = "qwen3.6-flash"


def pair_count(messages: list[BaseMessage]) -> int:
    """统计对话轮数：以 HumanMessage 条数为准。"""
    return sum(1 for m in messages if isinstance(m, HumanMessage))


def as_pairs(messages: list[BaseMessage]) -> list[tuple[HumanMessage, AIMessage | None]]:
    """将扁平消息列表切成「(Human, AI?)」轮次列表。"""
    pairs: list[tuple[HumanMessage, AIMessage | None]] = []
    i = 0
    while i < len(messages):
        if isinstance(messages[i], HumanMessage):
            human = messages[i]
            ai = None
            if i + 1 < len(messages) and isinstance(messages[i + 1], AIMessage):
                ai = messages[i + 1]
                i += 2
            else:
                i += 1
            pairs.append((human, ai))
        else:
            i += 1
    return pairs


def flatten_pairs(pairs: list[tuple[HumanMessage, AIMessage | None]]) -> list[BaseMessage]:
    """把轮次列表还原为扁平的 Human / AI 消息序列。"""
    out: list[BaseMessage] = []
    for human, ai in pairs:
        out.append(human)
        if ai is not None:
            out.append(ai)
    return out


def format_history_text(
    messages: list[BaseMessage],
    *,
    footer_note: str = "— 共 {n} 轮（Human+AI）—",
) -> str:
    """
    把消息列表格式化为右侧「对话历史」纯文本。

    Args:
        messages: 会话消息。
        footer_note: 末尾行模板，可用 ``{n}`` 表示轮数。
    """
    if not messages:
        return "（对话历史为空）"
    lines: list[str] = []
    for idx, (human, ai) in enumerate(as_pairs(messages), start=1):
        lines.append(f"[{idx}] Human: {human.content}")
        if ai is not None:
            lines.append(f"[{idx}] AI: {ai.content}")
    lines.append("")
    lines.append(footer_note.format(n=pair_count(messages)))
    return "\n".join(lines)


def pairs_to_plain(pairs: list[tuple[HumanMessage, AIMessage | None]]) -> str:
    """把多轮对话转成纯文本，作为摘要模型的输入材料。"""
    chunks: list[str] = []
    for idx, (human, ai) in enumerate(pairs, start=1):
        chunks.append(f"第{idx}轮用户：{human.content}")
        if ai is not None:
            chunks.append(f"第{idx}轮助手：{ai.content}")
    return "\n".join(chunks)


def summarize_pairs(pairs: list[tuple[HumanMessage, AIMessage | None]]) -> str:
    """用 ChatQwen 调用摘要模型，把若干轮压成中文摘要（≤ SUMMARY_MAX_CHARS）。"""
    plain = pairs_to_plain(pairs)
    model = build_chat_qwen(
        model=SUMMARY_MODEL,
        enable_thinking=False,
        temperature=0.3,
    )
    result = model.invoke(
        [
            SystemMessage(content="你是对话摘要助手。"),
            HumanMessage(
                content=(
                    "请将下列多轮对话压缩成一段中文摘要，作为后续对话的上下文。"
                    f"要求：不超过{SUMMARY_MAX_CHARS}字；保留关键事实、结论与用户偏好；不要分点刷屏。\n\n"
                    f"{plain}"
                )
            ),
        ]
    )
    text = chunk_text(result.content).strip()
    if len(text) > SUMMARY_MAX_CHARS:
        text = text[:SUMMARY_MAX_CHARS]
    return text


def compress_if_needed(messages: list[BaseMessage]) -> tuple[list[BaseMessage], bool]:
    """
    若对话达到 MAX_PAIRS 轮则执行混合压缩，否则原样返回。

    Returns:
        (处理后的消息列表, 是否发生了压缩)。
    """
    pairs = as_pairs(messages)
    if len(pairs) < MAX_PAIRS:
        return messages, False

    recent = pairs[-KEEP_RECENT_PAIRS:]
    boundary_human, boundary_ai = pairs[-KEEP_RECENT_PAIRS - 1]
    older = pairs[: -KEEP_RECENT_PAIRS - 1]

    to_summarize = list(older)
    if boundary_ai is not None:
        to_summarize.append((boundary_human, boundary_ai))
    elif not older:
        to_summarize = [(boundary_human, boundary_ai)]

    summary = summarize_pairs(to_summarize) if to_summarize else "（无更早对话）"
    new_pairs: list[tuple[HumanMessage, AIMessage | None]] = [
        (boundary_human, AIMessage(content=summary)),
        *recent,
    ]
    return flatten_pairs(new_pairs), True
