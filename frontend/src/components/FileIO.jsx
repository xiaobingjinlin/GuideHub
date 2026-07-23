import { useEffect, useState } from 'react'
import { getFileIoContent, postFileIoAppend, postFileIoReset } from '../lib/api'
import './FileIO.css'

/**
 * 文件读写：with + open 持久化到后端文件；刷新页面内容仍在。
 */
export default function FileIO({ onLog, title }) {
  const [line, setLine] = useState('GuideHub：用 with 和 open() 读写文件。')
  const [content, setContent] = useState('')
  const [path, setPath] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const apply = (data, { silentLog = false } = {}) => {
    if (data.line) setLine(data.line)
    setContent(data.content ?? '')
    if (data.path) setPath(data.path)
    if (!silentLog) {
      for (const msg of data.logs || []) onLog?.(msg)
    }
  }

  const load = async () => {
    setBusy(true)
    setError('')
    try {
      const data = await getFileIoContent()
      apply(data)
      onLog?.('—— 进入页面：已重新读取文件 ——')
    } catch (err) {
      const message = err?.message || String(err)
      setError(message)
      onLog?.(`错误：${message}`)
    } finally {
      setBusy(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleWrite = async () => {
    if (busy) return
    setBusy(true)
    setError('')
    onLog?.('—— 点击写入 ——')
    try {
      const data = await postFileIoAppend(line)
      apply(data)
      onLog?.('—— 写入后已重新读取 ——')
    } catch (err) {
      const message = err?.message || String(err)
      setError(message)
      onLog?.(`错误：${message}`)
    } finally {
      setBusy(false)
    }
  }

  const handleReset = async () => {
    if (busy) return
    setBusy(true)
    setError('')
    onLog?.('—— 点击重置 ——')
    try {
      const data = await postFileIoReset()
      apply(data)
    } catch (err) {
      const message = err?.message || String(err)
      setError(message)
      onLog?.(`错误：${message}`)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="file-io">
      <header className="file-io-hero">
        <p className="file-io-eyebrow">with + open()</p>
        <h1 className="file-io-title">{title || '文件读写'}</h1>
        <p className="file-io-subtitle">写入落盘保存；刷新页面后文件内容仍在</p>
      </header>

      <section className="file-io-sentence">
        <p className="file-io-label">待写入的一句话</p>
        <p className="file-io-quote">{line}</p>
        <div className="file-io-actions">
          <button type="button" className="file-io-cta" disabled={busy} onClick={handleWrite}>
            {busy ? '处理中…' : '写入'}
          </button>
          <button type="button" className="file-io-reset" disabled={busy} onClick={handleReset}>
            重置
          </button>
        </div>
      </section>

      {error && <p className="file-io-error">{error}</p>}

      <section className="file-io-preview">
        <div className="file-io-preview-head">
          <p className="file-io-label">文件内容</p>
          {path && <p className="file-io-path" title={path}>{path}</p>}
        </div>
        <textarea
          className="file-io-textarea"
          readOnly
          value={content}
          placeholder="（文件为空）"
          spellCheck={false}
        />
      </section>
    </div>
  )
}
