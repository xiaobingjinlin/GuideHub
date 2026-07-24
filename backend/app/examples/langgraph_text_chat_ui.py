"""
Gradio UI：LangGraph 文本对话机器人。

布局与交互由 ``text_chat_gradio`` 共用壳实现；本文件只注入 LangGraph 后端。
"""

from __future__ import annotations

import gradio as gr

from app.examples import langgraph_text_chat as core
from app.examples.text_chat_gradio import TextChatBackend, build_text_chat_blocks as _build


def build_langgraph_text_chat_blocks() -> gr.Blocks:
    """构建 Gradio Blocks，挂载到 /gradio/langgraph-text-chat。"""
    backend = TextChatBackend(
        default_session_id=core.DEFAULT_THREAD_ID,
        text_model=core.TEXT_MODEL,
        page_title="GuideHub · LangGraph 文本对话",
        subtitle=(
            f"**文本对话** · `{core.TEXT_MODEL}` · graph.stream + compress 节点 · "
            "右侧为 LangGraph SqliteSaver checkpoint 对话历史"
        ),
        history_label="对话历史（LangGraph checkpoint）",
        load_session=core.load_session,
        format_history_text=core.format_history_for_ui,
        arm_cancel=core.arm_cancel,
        clear_cancel=core.clear_cancel,
        is_cancel_requested=core.is_cancel_requested,
        request_cancel=core.request_cancel,
        rollback_cancelled_turn=core.rollback_cancelled_turn,
        iter_stream=core.iter_graph_stream,
        finalize_after_turn=core.finalize_after_turn,
        reset=core.reset,
    )
    return _build(backend)
