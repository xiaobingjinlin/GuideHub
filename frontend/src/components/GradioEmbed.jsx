import { useEffect } from 'react'
import './GradioEmbed.css'

/**
 * 将后端 Gradio 应用嵌进 GuideHub 用户窗。
 */
export default function GradioEmbed({ onLog, title, gradioPath, eyebrow = 'LangChain · Gradio' }) {
  useEffect(() => {
    onLog?.(`已打开 Gradio：${gradioPath}`)
    return () => onLog?.('Gradio 页面关闭')
  }, [gradioPath, onLog])

  return (
    <div className="gradio-embed">
      <header className="gradio-embed-hero">
        <p className="gradio-embed-eyebrow">{eyebrow}</p>
        <h1 className="gradio-embed-title">{title || '文本对话机器人'}</h1>
      </header>
      <iframe
        className="gradio-embed-frame"
        title={title || 'Gradio'}
        src={gradioPath}
        allow="microphone; clipboard-read; clipboard-write"
      />
    </div>
  )
}
