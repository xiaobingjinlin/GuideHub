import { useEffect, useMemo } from 'react'
import { loadCategories } from '../data/loadTutorials'
import { postSessionEvent, postUserLog } from '../lib/runtimeChannel'
import Calculator from './Calculator'
import './UserPage.css'

const UI_MAP = {
  calculator: Calculator,
}

export default function UserPage({ categoryId, exampleId }) {
  const example = useMemo(() => {
    const categories = loadCategories()
    const category = categories.find((c) => c.id === categoryId)
    return category?.examples.find((ex) => ex.id === exampleId) ?? null
  }, [categoryId, exampleId])

  useEffect(() => {
    document.title = example ? example.title : 'GuideHub'
    const onUnload = () => postSessionEvent('closed')
    window.addEventListener('beforeunload', onUnload)
    return () => {
      window.removeEventListener('beforeunload', onUnload)
      postSessionEvent('closed')
    }
  }, [example])

  if (!example) {
    return (
      <div className="user-page">
        <div className="user-page-empty">未找到对应示例，请从后台重新点击「运行」。</div>
      </div>
    )
  }

  const UserUI = UI_MAP[example.ui] || null

  return (
    <div className="user-page">
      <div className="user-page-atmosphere" aria-hidden="true" />
      <header className="user-page-header">
        <h1>{example.title}</h1>
      </header>
      <main className="user-page-body">
        {UserUI ? (
          <UserUI onLog={(message) => postUserLog(message)} />
        ) : (
          <p className="user-page-empty">该示例暂未绑定可交互界面。</p>
        )}
      </main>
    </div>
  )
}
