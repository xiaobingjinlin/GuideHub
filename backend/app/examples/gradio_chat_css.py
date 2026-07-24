"""Gradio 6 公共样式：css 需传给 mount_gradio_app / launch，不再放 Blocks()。"""

TEXT_CHAT_CSS = """
.gradio-container { max-width: 100% !important; padding: 8px 12px !important; }
footer { display: none !important; }
#memory-box textarea {
  min-height: 408px !important;
}
#action-row {
  align-items: center !important;
  gap: 0.75rem;
  min-height: 32px;
  overflow: hidden !important;
}
/* 不对子项写 display:!important，否则会盖掉 Gradio visible=False 的隐藏 */
#action-row > * {
  align-items: center !important;
  overflow: hidden !important;
}
#action-row label {
  margin: 0 !important;
  white-space: nowrap;
  line-height: 32px !important;
  height: 32px !important;
  min-height: 32px !important;
  align-items: center;
  font-size: 0.875rem !important;
  font-weight: 500 !important;
  overflow: hidden !important;
}
/* 「开启思考模式」复选框：与发送按钮同高 32px */
#thinking-mode,
#thinking-mode label,
#action-row .wrap,
#action-row .form {
  min-height: 32px !important;
  height: 32px !important;
  max-height: 32px !important;
  margin: 0 !important;
  padding-top: 0 !important;
  padding-bottom: 0 !important;
  align-items: center !important;
  overflow: hidden !important;
}
#thinking-mode input[type="checkbox"],
#action-row input[type="checkbox"] {
  width: 14px !important;
  height: 14px !important;
  margin: 0 0.35rem 0 0 !important;
  flex-shrink: 0;
}
#action-row button {
  height: 32px !important;
  min-height: 32px !important;
  max-height: 32px !important;
  padding-top: 0 !important;
  padding-bottom: 0 !important;
  padding-left: 0.9rem !important;
  padding-right: 0.9rem !important;
  align-items: center !important;
  justify-content: center !important;
  font-size: 0.875rem !important;
  font-weight: 500 !important;
  line-height: 1 !important;
  overflow: hidden !important;
  scrollbar-width: none !important;
}
#action-row button::-webkit-scrollbar,
#action-row *::-webkit-scrollbar {
  display: none !important;
  width: 0 !important;
  height: 0 !important;
}
#action-row * {
  scrollbar-width: none !important;
}
"""
