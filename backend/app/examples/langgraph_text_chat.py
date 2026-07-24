"""
LangGraph 文本对话核心逻辑。

教学对照 LangChain 示例，会话 / 流式 / 压缩尽量走 LangGraph：
- 状态：自定义 ``ChatState``（messages + did_compress；system 进 checkpoint）
- 记忆：``SqliteSaver``（WAL）
- 热路径：``graph.stream(..., stream_mode="messages")``
  ``START → ensure_system → assistant → compress → END``
- 护栏：assistant 内 ``trim_messages``（只裁送模型副本）
- 终止：UI 置 Event 打断消费；回滚用 **checkpoint_id 时间旅行**（非手写消息快照）

数据流：
  Human 入图 → ensure_system → assistant（trim + ChatQwen）
            → compress（满 20 轮混合压缩）→ checkpointer
            → finalize_after_turn（读 did_compress，刷新右侧）
"""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Annotated, Any, NotRequired, TypedDict

from langchain.messages import (
    AIMessage,
    AIMessageChunk,
    HumanMessage,
    RemoveMessage,
    SystemMessage,
)
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import REMOVE_ALL_MESSAGES, add_messages

from app.examples.chat_common import TEXT_MODEL, TurnResult, guard_prompt_messages
from app.examples.chat_compress import compress_if_needed, format_history_text, pair_count
from app.examples.chat_qwen import build_chat_qwen, chunk_text

DB_PATH = Path(__file__).resolve().parent / "langgraph_text_chat.db"
DEFAULT_THREAD_ID = "guidehub-langgraph-text-chat"
_HISTORY_FOOTER = "— 共 {n} 轮（Human+AI）· LangGraph checkpoint —"

SYSTEM_PROMPT = (
    "你是 GuideHub LangGraph 文本对话助手，回答简洁、准确。"
    "若开启思考模式，请先推理再给出最终回答。"
)

# UI「终止」信号（消费侧）；真正丢弃本轮靠 checkpoint 时间旅行回滚
_cancel_events: dict[str, threading.Event] = {}
# 发送前的 StateSnapshot.config（含 checkpoint_id / checkpoint_ns）
_checkpoint_configs: dict[str, dict[str, Any] | None] = {}

_conn: sqlite3.Connection | None = None
_checkpointer: SqliteSaver | None = None
_graph = None


class ChatState(TypedDict):
    """图状态：消息列表 + 本轮是否触发了压缩。"""

    messages: Annotated[list[BaseMessage], add_messages]
    did_compress: NotRequired[bool]


def _thread_config(
    thread_id: str,
    *,
    enable_thinking: bool | None = None,
    checkpoint_id: str | None = None,
) -> dict[str, Any]:
    """LangGraph config：thread_id / enable_thinking / 可选 checkpoint_id。"""
    configurable: dict[str, Any] = {
        "thread_id": thread_id or DEFAULT_THREAD_ID,
    }
    if enable_thinking is not None:
        configurable["enable_thinking"] = bool(enable_thinking)
    if checkpoint_id is not None:
        configurable["checkpoint_id"] = checkpoint_id
    return {"configurable": configurable}


def _format_history(messages: list[BaseMessage]) -> str:
    """右侧历史文案（带 LangGraph checkpoint 脚注）。"""
    return format_history_text(messages, footer_note=_HISTORY_FOOTER)


def _split_system(
    messages: list[BaseMessage],
) -> tuple[list[SystemMessage], list[BaseMessage]]:
    systems = [m for m in messages if isinstance(m, SystemMessage)]
    rest = [m for m in messages if not isinstance(m, SystemMessage)]
    return systems, rest


def ensure_system(state: ChatState) -> dict:
    """若尚无 SystemMessage，整表重写为 [system, ...]。"""
    messages = list(state.get("messages") or [])
    if any(isinstance(m, SystemMessage) for m in messages):
        return {}
    return {
        "messages": [
            RemoveMessage(id=REMOVE_ALL_MESSAGES),
            SystemMessage(content=SYSTEM_PROMPT),
            *messages,
        ]
    }


def assistant(state: ChatState, config: RunnableConfig) -> dict:
    """
    trim 后调用 ChatQwen；落库仅保留最终 content。

    ``graph.stream(..., stream_mode="messages")`` 会转发本节点的
    token / ``reasoning_content``。
    """
    enable_thinking = bool(
        (config.get("configurable") or {}).get("enable_thinking", True)
    )
    model = build_chat_qwen(model=TEXT_MODEL, enable_thinking=enable_thinking)
    prompt = guard_prompt_messages(list(state.get("messages") or []))
    result = model.invoke(prompt)
    text = chunk_text(result.content).strip() or (
        "（模型未返回文本，请检查模型权限与网络）"
    )
    return {"messages": [AIMessage(content=text)], "did_compress": False}


def compress(state: ChatState) -> dict:
    """图节点：满 20 轮则混合压缩并写回；保留头部 SystemMessage。"""
    messages = list(state.get("messages") or [])
    systems, rest = _split_system(messages)
    compressed_msgs, did = compress_if_needed(rest)
    if not did:
        return {"did_compress": False}
    head: list[BaseMessage] = (
        list(systems[:1]) if systems else [SystemMessage(content=SYSTEM_PROMPT)]
    )
    return {
        "messages": [
            RemoveMessage(id=REMOVE_ALL_MESSAGES),
            *head,
            *compressed_msgs,
        ],
        "did_compress": True,
    }


def _ensure_graph():
    """懒加载：SQLite（WAL）+ SqliteSaver + 编译图。"""
    global _conn, _checkpointer, _graph
    if _graph is not None:
        return _graph

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    _conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    _conn.execute("PRAGMA journal_mode=WAL")
    _checkpointer = SqliteSaver(_conn)
    _checkpointer.setup()

    builder = StateGraph(ChatState)
    builder.add_node("ensure_system", ensure_system)
    builder.add_node("assistant", assistant)
    builder.add_node("compress", compress)
    builder.add_edge(START, "ensure_system")
    builder.add_edge("ensure_system", "assistant")
    builder.add_edge("assistant", "compress")
    builder.add_edge("compress", END)
    _graph = builder.compile(checkpointer=_checkpointer)
    return _graph


def get_graph():
    """返回已编译、挂了 SqliteSaver 的 StateGraph。"""
    return _ensure_graph()


def export_graph_png(path: str | Path | None = None) -> Path:
    """导出图 PNG 到 frontend/public/guidehub/。"""
    target = Path(path) if path else (
        Path(__file__).resolve().parents[3]
        / "frontend"
        / "public"
        / "guidehub"
        / "langgraph-text-chat-graph.png"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    png = get_graph().get_graph().draw_mermaid_png()
    target.write_bytes(png)
    mmd = target.with_suffix(".mmd")
    mmd.write_text(get_graph().get_graph().draw_mermaid(), encoding="utf-8")
    return target


def load_session(thread_id: str) -> list[BaseMessage]:
    """从 checkpoint 读取当前 thread 的 messages。"""
    graph = get_graph()
    state = graph.get_state(_thread_config(thread_id))
    if not state or not state.values:
        return []
    return list(state.values.get("messages") or [])


def clear_session(thread_id: str) -> None:
    """删除整个 thread 的 checkpoint（清空会话）。"""
    graph = get_graph()
    assert _checkpointer is not None
    tid = thread_id or DEFAULT_THREAD_ID
    _checkpointer.delete_thread(tid)
    graph.get_state(_thread_config(tid))


def rewrite_session(thread_id: str, messages: list[BaseMessage]) -> None:
    """整表覆盖当前 tip（保留 SystemMessage）；一般用于兼容路径。"""
    graph = get_graph()
    config = _thread_config(thread_id)
    cleaned = [
        m
        for m in messages
        if isinstance(m, (SystemMessage, HumanMessage, AIMessage))
    ]
    graph.update_state(
        config,
        {
            "messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), *cleaned],
            "did_compress": False,
        },
    )


def arm_cancel(thread_id: str) -> threading.Event:
    """登记终止 Event，并保存发送前的 checkpoint config（时间旅行锚点）。"""
    graph = get_graph()
    state = graph.get_state(_thread_config(thread_id))
    cfg = None
    if state and state.config and (state.config.get("configurable") or {}).get(
        "checkpoint_id"
    ):
        # 深拷贝 configurable，保留 checkpoint_id / checkpoint_ns
        cfg = {
            "configurable": dict(state.config.get("configurable") or {}),
        }
    _checkpoint_configs[thread_id] = cfg
    event = threading.Event()
    _cancel_events[thread_id] = event
    return event


def request_cancel(thread_id: str) -> None:
    """请求终止：置位 Event，打断 stream 消费循环。"""
    event = _cancel_events.get(thread_id)
    if event is not None:
        event.set()


def rollback_cancelled_turn(thread_id: str) -> list[BaseMessage]:
    """
    终止后丢弃本轮：按发送前 checkpoint 做时间旅行回滚。

    - 无锚点：清空 thread（首轮即终止）
    - 有锚点：读出该检查点的 messages，再写回当前 tip（覆盖本轮脏状态）
    """
    past_config = _checkpoint_configs.pop(thread_id, None)
    graph = get_graph()
    tid = thread_id or DEFAULT_THREAD_ID

    if not past_config:
        clear_session(tid)
        return []

    past = graph.get_state(past_config)
    messages = list((past.values or {}).get("messages") or [])
    did_compress = bool((past.values or {}).get("did_compress"))
    # 写到当前 tip（不带旧 checkpoint_id），把线程头拨回发送前内容
    graph.update_state(
        _thread_config(tid),
        {
            "messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), *messages],
            "did_compress": did_compress,
        },
    )
    return load_session(tid)


def clear_cancel(thread_id: str) -> None:
    """结束本轮取消登记（只清 Event / 锚点，不写库）。"""
    _cancel_events.pop(thread_id, None)
    _checkpoint_configs.pop(thread_id, None)


def is_cancel_requested(thread_id: str) -> bool:
    """是否已点「终止」。"""
    event = _cancel_events.get(thread_id)
    return bool(event and event.is_set())


def iter_graph_stream(thread_id: str, user_text: str, *, enable_thinking: bool = True):
    """
    热路径：Human 入图，``stream_mode="messages"`` 流出思考与回答。

    落库与压缩均由节点 + checkpointer 完成。

    Yields:
        ("reasoning"|"content", 片段)
    """
    text = user_text.strip()
    graph = get_graph()
    config = _thread_config(thread_id, enable_thinking=enable_thinking)

    stream = graph.stream(
        {"messages": [HumanMessage(content=text)]},
        config,
        stream_mode="messages",
    )
    try:
        for chunk, metadata in stream:
            if is_cancel_requested(thread_id):
                break
            if (metadata or {}).get("langgraph_node") != "assistant":
                continue
            if not isinstance(chunk, (AIMessageChunk, AIMessage)):
                continue
            if enable_thinking:
                rc = (chunk.additional_kwargs or {}).get("reasoning_content")
                if rc:
                    yield "reasoning", str(rc)
            piece = chunk_text(chunk.content)
            if piece:
                yield "content", piece
    finally:
        close = getattr(stream, "close", None)
        if callable(close):
            try:
                close()
            except Exception:  # noqa: BLE001
                pass


def finalize_after_turn(thread_id: str, reply: str) -> TurnResult:
    """读 checkpoint（含 compress 节点结果），组装 TurnResult。"""
    graph = get_graph()
    state = graph.get_state(_thread_config(thread_id))
    values = (state.values if state else None) or {}
    messages = list(values.get("messages") or [])
    compressed = bool(values.get("did_compress"))

    if not (reply or "").strip():
        for m in reversed(messages):
            if isinstance(m, AIMessage) and str(m.content).strip():
                reply = str(m.content)
                break
        if not (reply or "").strip():
            reply = "（模型未返回文本，请检查模型权限与网络）"
            if messages and isinstance(messages[-1], HumanMessage):
                graph.update_state(
                    _thread_config(thread_id),
                    {"messages": [AIMessage(content=reply)], "did_compress": False},
                )
                messages = load_session(thread_id)

    return TurnResult(
        reply=reply,
        history_text=_format_history(messages),
        compressed=compressed,
        pair_count=pair_count(messages),
    )


def reset(thread_id: str) -> str:
    """清空 thread checkpoint，返回空历史文案。"""
    clear_session(thread_id or DEFAULT_THREAD_ID)
    return _format_history([])


def format_history_for_ui(messages: list[BaseMessage]) -> str:
    """UI 右侧历史：带 checkpoint 脚注。"""
    return _format_history(messages)
