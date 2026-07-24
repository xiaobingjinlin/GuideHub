"""GuideHub FastAPI 入口。"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import calculator, candy, concurrency, file_io, main_child_thread, sync_async

app = FastAPI(title="GuideHub API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(calculator.router, prefix="/api/calculator", tags=["calculator"])
app.include_router(candy.router, prefix="/api/candy", tags=["candy"])
app.include_router(concurrency.router, prefix="/api/concurrency", tags=["concurrency"])
app.include_router(
    main_child_thread.router,
    prefix="/api/main-child-thread",
    tags=["main-child-thread"],
)
app.include_router(sync_async.router, prefix="/api/sync-async", tags=["sync-async"])
app.include_router(file_io.router, prefix="/api/file-io", tags=["file-io"])


@app.get("/api/health")
def health():
    return {"ok": True}


# Gradio 6：css 传给 mount_gradio_app，不再放 Blocks()
try:
    import gradio as gr
    from app.examples.gradio_chat_css import TEXT_CHAT_CSS
    from app.examples.langchain_text_chat_ui import build_text_chat_blocks

    app = gr.mount_gradio_app(
        app,
        build_text_chat_blocks(),
        path="/gradio/text-chat",
        css=TEXT_CHAT_CSS,
    )
except Exception as exc:  # noqa: BLE001
    @app.get("/gradio/text-chat")
    def gradio_unavailable():
        return {
            "ok": False,
            "detail": f"Gradio 文本对话未就绪：{exc}",
        }


try:
    import gradio as gr
    from app.examples.gradio_chat_css import TEXT_CHAT_CSS
    from app.examples.langgraph_text_chat_ui import build_langgraph_text_chat_blocks

    app = gr.mount_gradio_app(
        app,
        build_langgraph_text_chat_blocks(),
        path="/gradio/langgraph-text-chat",
        css=TEXT_CHAT_CSS,
    )
except Exception as exc:  # noqa: BLE001

    @app.get("/gradio/langgraph-text-chat")
    def langgraph_gradio_unavailable():
        return {
            "ok": False,
            "detail": f"Gradio LangGraph 文本对话未就绪：{exc}",
        }
