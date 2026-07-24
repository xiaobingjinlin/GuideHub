"""
LangChain / LangGraph 共用的文本对话 Gradio 壳。

差异通过 ``TextChatBackend`` 注入：默认会话 ID、流式入口、落库方式、文案等。
流式过程中冻结右侧历史文案，避免每个 chunk 重复读库。
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any

import gradio as gr
from gradio import ChatMessage
from langchain.messages import AIMessage, HumanMessage
from langchain_core.messages import BaseMessage


@dataclass(frozen=True)
class TextChatBackend:
    """两套示例共用的后端适配面。"""

    default_session_id: str
    text_model: str
    page_title: str
    subtitle: str
    history_label: str
    load_session: Callable[[str], list[BaseMessage]]
    format_history_text: Callable[[list[BaseMessage]], str]
    arm_cancel: Callable[[str], Any]
    clear_cancel: Callable[[str], None]
    is_cancel_requested: Callable[[str], bool]
    request_cancel: Callable[[str], None]
    rollback_cancelled_turn: Callable[[str], list[BaseMessage]]
    iter_stream: Callable[..., Iterator[tuple[str, str]]]
    finalize_after_turn: Callable[..., Any]
    reset: Callable[[str], str]


def _messages_to_chatbot(messages: list[BaseMessage]) -> list[ChatMessage]:
    """HumanMessage → user、AIMessage → assistant。"""
    history: list[ChatMessage] = []
    for m in messages:
        if isinstance(m, HumanMessage):
            history.append(ChatMessage(role="user", content=str(m.content)))
        elif isinstance(m, AIMessage):
            history.append(ChatMessage(role="assistant", content=str(m.content)))
    return history


def _format_assistant(reply: str, compressed: bool, pair_count: int) -> str:
    parts = [reply]
    if compressed:
        parts.append(f"\n\n（已触发混合压缩：当前对话历史 {pair_count} 轮）")
    return "".join(parts)


def build_text_chat_blocks(backend: TextChatBackend) -> gr.Blocks:
    """按 backend 构建左右分栏对话界面。"""

    def _on_load() -> tuple[str, list, str]:
        sid = backend.default_session_id
        messages = backend.load_session(sid)
        return sid, _messages_to_chatbot(messages), backend.format_history_text(messages)

    def _show_stop_btn(user_msg: str):
        if not (user_msg or "").strip():
            return gr.update(visible=True), gr.update(visible=False)
        return gr.update(visible=False), gr.update(visible=True)

    def _show_send_btn():
        return gr.update(visible=True), gr.update(visible=False)

    def _on_stop(session_id: str):
        sid = session_id or backend.default_session_id
        backend.request_cancel(sid)
        messages = backend.rollback_cancelled_turn(sid)
        return (
            gr.update(),
            backend.format_history_text(messages),
            sid,
            *_show_send_btn(),
        )

    def _on_send(
        user_msg: str,
        history: list,
        session_id: str,
        enable_thinking: bool,
    ) -> Iterator[tuple[list, str, str, str]]:
        history = list(history or [])
        sid = session_id or backend.default_session_id
        enable_thinking = bool(enable_thinking)
        text = (user_msg or "").strip()
        if not text:
            mem = backend.format_history_text(backend.load_session(sid))
            yield history, mem, sid, ""
            return

        # 流式期间冻结右侧历史，结束/终止/出错再刷新，避免每 chunk 读库
        frozen_history = backend.format_history_text(backend.load_session(sid))
        backend.arm_cancel(sid)
        try:
            history.append(ChatMessage(role="user", content=text))
            yield history, frozen_history, sid, ""

            reasoning = ""
            reply = ""
            answer_started = False

            if enable_thinking:
                history.append(
                    ChatMessage(
                        role="assistant",
                        content="",
                        metadata={"title": "思考中…", "status": "pending"},
                    )
                )
                yield history, frozen_history, sid, ""
            else:
                history.append(ChatMessage(role="assistant", content=""))
                answer_started = True
                yield history, frozen_history, sid, ""

            try:
                for kind, piece in backend.iter_stream(
                    sid,
                    text,
                    enable_thinking=enable_thinking,
                ):
                    if backend.is_cancel_requested(sid):
                        break
                    if kind == "reasoning":
                        reasoning += piece
                        history[-1] = ChatMessage(
                            role="assistant",
                            content=reasoning,
                            metadata={"title": "思考中…", "status": "pending"},
                        )
                        yield history, frozen_history, sid, ""
                    else:
                        if enable_thinking and not answer_started:
                            history[-1] = ChatMessage(
                                role="assistant",
                                content=reasoning or "（无思考内容）",
                                metadata={"title": "思考过程", "status": "done"},
                            )
                            history.append(ChatMessage(role="assistant", content=""))
                            answer_started = True
                        reply += piece
                        history[-1] = ChatMessage(role="assistant", content=reply)
                        yield history, frozen_history, sid, ""
            except Exception as exc:  # noqa: BLE001
                if backend.is_cancel_requested(sid):
                    messages = backend.rollback_cancelled_turn(sid)
                    yield history, backend.format_history_text(messages), sid, ""
                    return
                if enable_thinking and not answer_started:
                    history[-1] = ChatMessage(
                        role="assistant",
                        content=reasoning or str(exc),
                        metadata={"title": "思考中断", "status": "done"},
                    )
                    history.append(ChatMessage(role="assistant", content=f"错误：{exc}"))
                else:
                    history[-1] = ChatMessage(
                        role="assistant",
                        content=(reply + f"\n\n错误：{exc}").strip(),
                    )
                yield history, backend.format_history_text(backend.load_session(sid)), sid, ""
                return

            if backend.is_cancel_requested(sid):
                messages = backend.rollback_cancelled_turn(sid)
                yield history, backend.format_history_text(messages), sid, ""
                return

            if enable_thinking and not answer_started:
                history[-1] = ChatMessage(
                    role="assistant",
                    content=reasoning or "（无思考内容）",
                    metadata={"title": "思考过程", "status": "done"},
                )
                history.append(ChatMessage(role="assistant", content=""))
                answer_started = True

            try:
                result = backend.finalize_after_turn(sid, reply)
            except Exception as exc:  # noqa: BLE001
                history[-1] = ChatMessage(
                    role="assistant",
                    content=(reply or "") + f"\n\n保存对话历史失败：{exc}",
                )
                yield history, backend.format_history_text(backend.load_session(sid)), sid, ""
                return

            final_text = _format_assistant(
                result.reply, result.compressed, result.pair_count
            )
            history[-1] = ChatMessage(role="assistant", content=final_text)
            if (
                enable_thinking
                and len(history) >= 2
                and isinstance(history[-2], ChatMessage)
                and (history[-2].metadata or {}).get("title") in {"思考过程", "思考中…"}
                and not reasoning
            ):
                history.pop(-2)

            yield history, result.history_text, sid, ""
        finally:
            # 若已被 cancels 打断且尚未显式回滚，快照仍在 → 这里补一次；
            # 已 rollback 过的路径会 pop 掉快照，此处为 no-op。
            if backend.is_cancel_requested(sid):
                backend.rollback_cancelled_turn(sid)
            backend.clear_cancel(sid)

    def _on_reset(session_id: str) -> tuple[list, str, str]:
        sid = session_id or backend.default_session_id
        backend.request_cancel(sid)
        # 丢弃快照、不回滚，避免把刚清空的会话写回发送前状态
        backend.clear_cancel(sid)
        mem = backend.reset(sid)
        return [], mem, sid

    with gr.Blocks(title=backend.page_title) as demo:
        gr.Markdown(backend.subtitle)
        session_state = gr.State(backend.default_session_id)

        with gr.Row(equal_height=True):
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(label="对话", height=280)
                user_in = gr.Textbox(
                    label="输入",
                    placeholder="输入消息后回车或点击发送",
                    lines=1,
                    max_lines=2,
                )
                with gr.Row(elem_id="action-row", equal_height=True):
                    thinking_box = gr.Checkbox(
                        label="开启思考模式",
                        value=True,
                        container=False,
                        elem_id="thinking-mode",
                    )
                    send_btn = gr.Button("发送", variant="primary", size="sm")
                    stop_btn = gr.Button(
                        "终止",
                        variant="stop",
                        size="sm",
                        visible=False,
                    )
                    reset_btn = gr.Button("清空会话", size="sm")
            with gr.Column(scale=2):
                memory_box = gr.Textbox(
                    label=backend.history_label,
                    lines=18,
                    max_lines=18,
                    interactive=False,
                    elem_id="memory-box",
                )

        demo.load(
            _on_load,
            inputs=None,
            outputs=[session_state, chatbot, memory_box],
        )

        send_outputs = [chatbot, memory_box, session_state, user_in]
        send_inputs = [user_in, chatbot, session_state, thinking_box]

        send_event = send_btn.click(
            _show_stop_btn,
            inputs=[user_in],
            outputs=[send_btn, stop_btn],
        ).then(
            _on_send,
            inputs=send_inputs,
            outputs=send_outputs,
        ).then(
            _show_send_btn,
            inputs=None,
            outputs=[send_btn, stop_btn],
        )

        submit_event = user_in.submit(
            _show_stop_btn,
            inputs=[user_in],
            outputs=[send_btn, stop_btn],
        ).then(
            _on_send,
            inputs=send_inputs,
            outputs=send_outputs,
        ).then(
            _show_send_btn,
            inputs=None,
            outputs=[send_btn, stop_btn],
        )

        stop_btn.click(
            _on_stop,
            inputs=[session_state],
            outputs=[chatbot, memory_box, session_state, send_btn, stop_btn],
            cancels=[send_event, submit_event],
        )

        reset_btn.click(
            _on_reset,
            inputs=[session_state],
            outputs=[chatbot, memory_box, session_state],
            cancels=[send_event, submit_event],
        ).then(
            _show_send_btn,
            inputs=None,
            outputs=[send_btn, stop_btn],
        )
    return demo
