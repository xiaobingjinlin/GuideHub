"""
LangChain 文本对话核心逻辑（LangChain 1.3，不依赖 LangGraph）。

热路径：
  SqliteChatMessageHistory 读历史
  → ChatPromptTemplate 组消息
  → trim_messages token/字数护栏
  → ChatQwen.stream（保留 reasoning_content → additional_kwargs）
  → store.add_messages([Human, AI])
  → finalize_after_turn（混合压缩）

说明：通用 ``ChatOpenAI.stream`` 会丢弃通义的 ``reasoning_content``；
本示例用 ``langchain-qwq.ChatQwen`` 做流式，思考走 ``additional_kwargs``。
也不再使用已弃用的 RunnableWithMessageHistory 驱动热路径。
"""

from __future__ import annotations

import threading
from pathlib import Path

from langchain.messages import AIMessage, HumanMessage
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.examples.chat_common import TEXT_MODEL, TurnResult, guard_prompt_messages
from app.examples.chat_compress import compress_if_needed, format_history_text, pair_count
from app.examples.chat_qwen import build_chat_qwen, chunk_text
from app.examples.sqlite_chat_history import SqliteChatMessageHistory

# 按 session_id 登记的终止信号：UI 点「终止」时 set，流式循环每 chunk 检查一次
_cancel_events: dict[str, threading.Event] = {}
# 发送前的历史快照：终止时回滚 SQLite，确保本轮不落库
_history_snapshots: dict[str, list[BaseMessage]] = {}

DB_PATH = Path(__file__).resolve().parent / "langchain_text_chat.db"
DEFAULT_SESSION_ID = "guidehub-text-chat"

SYSTEM_PROMPT = (
    "你是 GuideHub 文本对话助手，回答简洁、准确。"
    "若开启思考模式，请先推理再给出最终回答。"
)

_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ]
)


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """
    按 session_id 打开 SQLite 对话历史。

    Args:
        session_id: 会话标识；本示例固定为 DEFAULT_SESSION_ID。

    Returns:
        SqliteChatMessageHistory 实例（连接按 db 路径复用）。
    """
    return SqliteChatMessageHistory(session_id=session_id, db_path=DB_PATH)


def build_prompt_messages(history: list[BaseMessage], user_text: str) -> list[BaseMessage]:
    """用 ChatPromptTemplate 组装 system + 历史 + 本轮 human。"""
    return _PROMPT.format_messages(history=history, input=user_text.strip())


def load_session(session_id: str) -> list[BaseMessage]:
    """从 SQLite 读取指定会话的全部消息。"""
    return list(get_session_history(session_id).messages)


def clear_session(session_id: str) -> None:
    """清空指定会话在 SQLite 中的全部消息。"""
    get_session_history(session_id).clear()


def rewrite_session(session_id: str, messages: list[BaseMessage]) -> None:
    """
    用新的消息列表整体覆盖当前会话（clear + 批量 add_messages）。

    用于压缩完成后把缩短后的历史写回 SQLite。
    """
    store = get_session_history(session_id)
    store.clear()
    cleaned = [m for m in messages if isinstance(m, (HumanMessage, AIMessage))]
    store.add_messages(cleaned)


def maybe_compress_session(session_id: str) -> tuple[list[BaseMessage], bool]:
    """读取会话；若达到压缩阈值则压缩并写回，否则原样返回。"""
    messages = load_session(session_id)
    compressed_msgs, did = compress_if_needed(messages)
    if did:
        rewrite_session(session_id, compressed_msgs)
        return compressed_msgs, True
    return messages, False


def arm_cancel(session_id: str) -> threading.Event:
    """为本轮生成登记终止 Event，并保存发送前的对话历史快照。"""
    _history_snapshots[session_id] = list(load_session(session_id))
    event = threading.Event()
    _cancel_events[session_id] = event
    return event


def request_cancel(session_id: str) -> None:
    """请求终止指定会话当前正在进行的流式生成。"""
    event = _cancel_events.get(session_id)
    if event is not None:
        event.set()


def rollback_cancelled_turn(session_id: str) -> list[BaseMessage]:
    """
    终止后丢弃本轮：把 SQLite 恢复为发送前快照。

    快照用 pop 取出，重复调用不会再次写库（避免 stop + finally 双重回滚）。
    """
    snapshot = _history_snapshots.pop(session_id, None)
    if snapshot is not None:
        rewrite_session(session_id, snapshot)
        return list(snapshot)
    return load_session(session_id)


def clear_cancel(session_id: str) -> None:
    """
    结束本轮取消登记（只清 Event / 快照，不写库）。

    回滚由 ``rollback_cancelled_turn`` 显式完成；若任务被 Gradio cancels
    打断且尚未回滚，调用方应先 ``rollback_cancelled_turn`` 再清登记。
    """
    _cancel_events.pop(session_id, None)
    _history_snapshots.pop(session_id, None)


def is_cancel_requested(session_id: str) -> bool:
    """查询该会话是否已请求终止。"""
    event = _cancel_events.get(session_id)
    return bool(event and event.is_set())


def iter_chain_stream(session_id: str, user_text: str, *, enable_thinking: bool = True):
    """
    流式调用大模型，并向 UI 产出增量片段；成功结束后批量写入历史。

    流程：
      1. 读 SqliteChatMessageHistory
      2. ChatPromptTemplate 组 prompt
      3. trim_messages 护栏
      4. ChatQwen.stream（思考在 additional_kwargs）
      5. 未终止则 add_messages([HumanMessage, AIMessage])

    Yields:
        tuple[str, str]: ``("reasoning"|"content", 文本片段)``。
    """
    text = user_text.strip()
    store = get_session_history(session_id)
    prompt_messages = guard_prompt_messages(
        build_prompt_messages(list(store.messages), text)
    )
    model = build_chat_qwen(model=TEXT_MODEL, enable_thinking=enable_thinking)

    reply_parts: list[str] = []
    for chunk in model.stream(prompt_messages):
        if is_cancel_requested(session_id):
            break
        if enable_thinking:
            rc = (chunk.additional_kwargs or {}).get("reasoning_content")
            if rc:
                yield "reasoning", str(rc)
        piece = chunk_text(chunk.content)
        if piece:
            reply_parts.append(piece)
            yield "content", piece

    # 仅在未终止时落库，保证「终止 = 本轮不入库」
    if is_cancel_requested(session_id):
        return
    reply = "".join(reply_parts).strip() or "（模型未返回文本，请检查模型权限与网络）"
    store.add_messages(
        [
            HumanMessage(content=text),
            AIMessage(content=reply),
        ]
    )


def finalize_after_turn(session_id: str, reply: str) -> TurnResult:
    """
    一轮流式调用结束后的收尾：兜底空回复、触发压缩、组装 TurnResult。

    正常情况下本轮已由 iter_chain_stream 写入；此处处理空回复等极端情况，
    再按需混合压缩并刷新右侧历史文案。
    """
    if not (reply or "").strip():
        store = get_session_history(session_id)
        msgs = list(store.messages)
        if msgs and isinstance(msgs[-1], HumanMessage):
            store.add_messages(
                [AIMessage(content="（模型未返回文本，请检查模型权限与网络）")]
            )
        reply = "（模型未返回文本，请检查模型权限与网络）"

    messages, compressed = maybe_compress_session(session_id)
    return TurnResult(
        reply=reply,
        history_text=format_history_text(messages),
        compressed=compressed,
        pair_count=pair_count(messages),
    )


def reset(session_id: str) -> str:
    """清空会话并返回空历史的展示文本（供「清空会话」按钮）。"""
    clear_session(session_id or DEFAULT_SESSION_ID)
    return format_history_text([])
