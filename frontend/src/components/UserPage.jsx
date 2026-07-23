import { useEffect, useMemo } from 'react'
import { loadCategories } from '../data/loadTutorials'
import { postSessionEvent, postUserLog } from '../lib/runtimeChannel'
import Calculator from './Calculator'
import Candy from './Candy'
import Concurrency from './Concurrency'
import FileIO from './FileIO'
import MainChildThread from './MainChildThread'
import SyncAsync from './SyncAsync'
import './UserPage.css'

const RACE_UIS = new Set(['concurrency', 'main-child-thread', 'sync-async'])
const CUSTOM_HERO_UIS = new Set([...RACE_UIS, 'file-io'])

const UI_MAP = {
  calculator: Calculator,
  candy: Candy,
  concurrency: Concurrency,
  'main-child-thread': MainChildThread,
  'sync-async': SyncAsync,
  'file-io': FileIO,
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
    <div className={`user-page ${RACE_UIS.has(example.ui) ? 'is-concurrency' : ''}`}>
      <div className="user-page-atmosphere" aria-hidden="true" />
      {!CUSTOM_HERO_UIS.has(example.ui) && (
        <header className="user-page-header">
          <h1>{example.title}</h1>
        </header>
      )}
      <main className="user-page-body">
        {UserUI ? (
          <UserUI
            onLog={(message) => postUserLog(message)}
            problem={example.problem}
            kind={example.kind}
            title={example.title}
          />
        ) : (
          <p className="user-page-empty">该示例暂未绑定可交互界面。</p>
        )}
      </main>
    </div>
  )
}
