import { useMemo, useState, useCallback, useEffect, useRef } from 'react'
import { loadCategories } from './data/loadTutorials'
import { buildUserPageUrl, parseUserPageParams } from './lib/runtimeChannel'
import UserPage from './components/UserPage'
import './App.css'

function timestamp() {
  return new Date().toLocaleTimeString('zh-CN', { hour12: false })
}

function BackendApp() {
  const categories = useMemo(() => loadCategories(), [])
  const [activeCategoryId, setActiveCategoryId] = useState(categories[0]?.id ?? null)
  const activeCategory = categories.find((c) => c.id === activeCategoryId) ?? null

  const [activeExampleId, setActiveExampleId] = useState(
    categories[0]?.examples[0]?.id ?? null,
  )
  const activeExample =
    activeCategory?.examples.find((ex) => ex.id === activeExampleId) ??
    activeCategory?.examples[0] ??
    null

  const [consoleLines, setConsoleLines] = useState([])
  const [userWindowOpen, setUserWindowOpen] = useState(false)
  const [bottomTab, setBottomTab] = useState('console') // console | notes
  const userWindowRef = useRef(null)

  const appendLog = useCallback((message) => {
    setConsoleLines((prev) => [...prev, `[${timestamp()}] ${message}`])
  }, [])

  useEffect(() => {
    const onMessage = (event) => {
      if (event.origin !== window.location.origin) return
      const data = event.data
      if (!data || data.source !== 'guidehub-user') return
      if (data.type === 'log' && data.message) appendLog(data.message)
      if (data.type === 'closed') setUserWindowOpen(false)
    }

    window.addEventListener('message', onMessage)

    const timer = window.setInterval(() => {
      if (userWindowRef.current && userWindowRef.current.closed) {
        userWindowRef.current = null
        setUserWindowOpen(false)
      }
    }, 500)

    return () => {
      window.clearInterval(timer)
      window.removeEventListener('message', onMessage)
    }
  }, [appendLog])

  const selectCategory = (id) => {
    setActiveCategoryId(id)
    const next = categories.find((c) => c.id === id)
    setActiveExampleId(next?.examples[0]?.id ?? null)
    setConsoleLines([])
  }

  const selectExample = (id) => {
    setActiveExampleId(id)
    setConsoleLines([])
  }

  const handleRun = () => {
    if (!activeExample || !activeCategory) return

    setConsoleLines([
      `[${timestamp()}] 运行「${activeExample.title}」—— 已打开新窗口`,
      `[${timestamp()}] 后台待命：可直接查看本页控制台，等待操作`,
    ])

    const url = buildUserPageUrl(activeCategory.id, activeExample.id)
    const width = activeExample.window?.width ?? 480
    const height = activeExample.window?.height ?? 720
    const features = [
      'popup=yes',
      `width=${width}`,
      `height=${height}`,
      'menubar=no',
      'toolbar=no',
      'location=yes',
      'resizable=yes',
      'scrollbars=yes',
    ].join(',')
    // 每个示例独立窗口名，便于套用各自默认宽高
    const popup = window.open(url, `guidehub-user-${activeExample.id}`, features)

    if (!popup) {
      appendLog('弹窗被浏览器拦截，请允许本站弹出窗口后重试')
      setUserWindowOpen(false)
      return
    }

    userWindowRef.current = popup
    setUserWindowOpen(true)
    popup.focus()
  }

  return (
    <div className={`app ${userWindowOpen ? 'app-as-backend' : ''}`}>
      <div className="app-atmosphere" aria-hidden="true" />

      <header className="topbar">
        <div className="brand">
          <div className="brand-text">
            <strong>GuideHub</strong>
            <span>我的教程</span>
          </div>
        </div>

        <nav className="category-nav" aria-label="教程分类">
          {categories.map((cat) => (
            <button
              key={cat.id}
              type="button"
              className={`category-tab ${cat.id === activeCategoryId ? 'is-active' : ''}`}
              onClick={() => selectCategory(cat.id)}
            >
              {cat.label}
            </button>
          ))}
        </nav>
      </header>

      <main className="workspace">
        <aside className="sidebar">
          <p className="sidebar-label">示例菜单</p>
          <ul className="example-list">
            {(activeCategory?.examples ?? []).map((ex) => (
              <li key={ex.id}>
                <button
                  type="button"
                  className={`example-item ${ex.id === activeExample?.id ? 'is-active' : ''}`}
                  onClick={() => selectExample(ex.id)}
                >
                  {ex.title}
                </button>
              </li>
            ))}
            {!activeCategory?.examples?.length && (
              <li className="example-empty">该分类暂无示例</li>
            )}
          </ul>
        </aside>

        <section className="editor-pane">
          <div className="panel code-panel">
            <div className="panel-head">
              <h1>{activeExample?.title ?? '选择示例'}</h1>
              <div className="panel-head-right">
                {userWindowOpen && <span className="backend-badge">后台页面</span>}
                <span className="panel-meta">代码</span>
              </div>
            </div>
            <div className="code-area-wrap">
              <textarea
                className="code-area"
                readOnly
                spellCheck={false}
                value={activeExample?.code ?? ''}
                placeholder="选择左侧示例后，这里会显示带注释的示例代码"
              />
              <button
                type="button"
                className="run-button"
                onClick={handleRun}
                disabled={!activeExample}
              >
                <span className="run-icon" aria-hidden="true">
                  ▶
                </span>
                运行
              </button>
            </div>
          </div>

          <div className={`panel bottom-panel is-${bottomTab}`}>
            <div className="panel-head bottom-tabs" role="tablist" aria-label="下方面板">
              <button
                type="button"
                role="tab"
                aria-selected={bottomTab === 'console'}
                className={`bottom-tab ${bottomTab === 'console' ? 'is-active' : ''}`}
                onClick={() => setBottomTab('console')}
              >
                控制台
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={bottomTab === 'notes'}
                className={`bottom-tab ${bottomTab === 'notes' ? 'is-active' : ''}`}
                onClick={() => setBottomTab('notes')}
              >
                知识便利贴
              </button>
              <span className="panel-meta">
                {bottomTab === 'console' ? '前后台交互' : '笔记'}
              </span>
            </div>
            {bottomTab === 'console' ? (
              <textarea
                className="console-area"
                readOnly
                spellCheck={false}
                value={consoleLines.join('\n')}
                placeholder="点击「运行」后，每次计算操作会显示在这里"
              />
            ) : (
              <textarea
                className="note-area"
                readOnly
                spellCheck={false}
                value={(activeExample?.notes ?? [])
                  .map((line, i) =>
                    line.startsWith('友情提示') ? line : `${i + 1}. ${line}`,
                  )
                  .join('\n')}
                placeholder="选择左侧示例后，这里会显示知识点摘要"
              />
            )}
          </div>
        </section>
      </main>
    </div>
  )
}

export default function App() {
  const userParams = parseUserPageParams()
  if (userParams?.categoryId && userParams?.exampleId) {
    return <UserPage categoryId={userParams.categoryId} exampleId={userParams.exampleId} />
  }
  return <BackendApp />
}
