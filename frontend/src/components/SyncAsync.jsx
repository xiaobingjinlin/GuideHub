import { useEffect, useMemo, useRef, useState } from 'react'
import { postSyncAsync } from '../lib/api'
import './Concurrency.css'

const BAR_MAX_MS = 3000

const MODE_META = {
  sync: {
    label: '同步',
    hint: 'time.sleep 一个接一个，耗时相加',
  },
  async: {
    label: '异步',
    hint: 'asyncio.sleep + gather，等待可重叠',
  },
}

const MODE_KEYS = ['sync', 'async']
const EMPTY_RESULTS = { sync: null, async: null }
const EMPTY_PROGRESS = { sync: 0, async: 0 }

function toBarPercent(elapsedMs) {
  return Math.min(100, (elapsedMs / BAR_MAX_MS) * 100)
}

/**
 * 同步 vs 异步：布局参考示例三。
 */
export default function SyncAsync({ onLog, title }) {
  const [running, setRunning] = useState(null)
  const [results, setResults] = useState(EMPTY_RESULTS)
  const [progress, setProgress] = useState(EMPTY_PROGRESS)
  const [error, setError] = useState('')
  const runIdRef = useRef(0)
  const busyRef = useRef(false)
  const rafRef = useRef(0)

  useEffect(
    () => () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
    },
    [],
  )

  const winner = useMemo(() => {
    const entries = MODE_KEYS.map((k) => [k, results[k]]).filter(([, v]) => v != null)
    if (entries.length < 2) return null
    return entries.reduce((best, cur) => (cur[1] < best[1] ? cur : best))[0]
  }, [results])

  const stopProgressTick = () => {
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current)
      rafRef.current = 0
    }
  }

  const startProgressTick = (modeKey, startedAt) => {
    stopProgressTick()
    const tick = () => {
      const elapsedMs = performance.now() - startedAt
      setProgress((prev) => ({ ...prev, [modeKey]: toBarPercent(elapsedMs) }))
      rafRef.current = requestAnimationFrame(tick)
    }
    rafRef.current = requestAnimationFrame(tick)
  }

  const runMode = async (modeKey) => {
    if (busyRef.current) return
    busyRef.current = true
    const meta = MODE_META[modeKey]
    const runId = ++runIdRef.current
    setError('')
    setRunning(modeKey)
    setProgress((prev) => ({ ...prev, [modeKey]: 0 }))

    onLog?.(`—— 开始：${meta.label} ——`)
    const t0 = performance.now()
    startProgressTick(modeKey, t0)

    try {
      const data = await postSyncAsync(modeKey)
      stopProgressTick()
      if (runId !== runIdRef.current) {
        busyRef.current = false
        return
      }
      for (const line of data.logs || []) onLog?.(line)
      const elapsedSec = Number(data.elapsed)
      setProgress((prev) => ({ ...prev, [modeKey]: toBarPercent(elapsedSec * 1000) }))
      setResults((prev) => ({ ...prev, [modeKey]: elapsedSec }))
      onLog?.(`${meta.label} 结束，耗时 ${elapsedSec.toFixed(2)}s（后端实测）`)
    } catch (err) {
      stopProgressTick()
      const message = err?.message || String(err)
      setError(message)
      onLog?.(`错误：${message}`)
      setProgress((prev) => ({ ...prev, [modeKey]: 0 }))
    } finally {
      if (runId === runIdRef.current) {
        setRunning(null)
        busyRef.current = false
      }
    }
  }

  const runAll = async () => {
    if (busyRef.current) return
    setResults({ ...EMPTY_RESULTS })
    setProgress({ ...EMPTY_PROGRESS })
    onLog?.('======== 开始对比：同步 vs 异步 ========')
    for (const key of MODE_KEYS) {
      await runMode(key)
    }
    onLog?.('======== 对比结束 ========')
  }

  const reset = () => {
    runIdRef.current += 1
    stopProgressTick()
    busyRef.current = false
    setRunning(null)
    setResults({ ...EMPTY_RESULTS })
    setProgress({ ...EMPTY_PROGRESS })
    setError('')
    onLog?.('已重置对比结果')
  }

  return (
    <div className="concurrency concurrency-io">
      <header className="concurrency-hero">
        <p className="concurrency-eyebrow">asyncio</p>
        <h1 className="concurrency-title">{title || '同步与异步'}</h1>
        <p className="concurrency-subtitle">
          同一批等待型任务：对比同步串行与异步并发的耗时差异
        </p>
      </header>

      <div className="concurrency-toolbar">
        <button type="button" className="concurrency-cta" disabled={!!running} onClick={runAll}>
          {running ? '对比进行中…' : '开始对比'}
        </button>
        <button type="button" className="concurrency-reset" disabled={!!running} onClick={reset}>
          重置
        </button>
      </div>

      {error && <p className="concurrency-error">{error}</p>}

      <div className="concurrency-lanes" aria-label="耗时对比">
        {MODE_KEYS.map((key, index) => {
          const meta = MODE_META[key]
          const value = results[key]
          const widthPct = progress[key] ?? 0
          const isRunning = running === key
          const isWinner = winner === key

          return (
            <article
              key={key}
              className={[
                'concurrency-lane',
                `mode-${key === 'sync' ? 'serial' : 'threads'}`,
                isRunning ? 'is-running' : '',
                isWinner ? 'is-winner' : '',
              ].join(' ')}
              style={{ animationDelay: `${index * 60}ms` }}
            >
              <div className="concurrency-lane-top">
                <div>
                  <h2>{meta.label}</h2>
                  <p>{meta.hint}</p>
                </div>
                <div className="concurrency-lane-meta">
                  {isWinner && <span className="concurrency-badge">更快</span>}
                  <span className="concurrency-time">
                    {isRunning ? '…' : value == null ? '—' : `${value.toFixed(2)}s`}
                  </span>
                </div>
              </div>

              <div className="concurrency-track">
                <div className="concurrency-fill" style={{ width: `${widthPct}%` }} />
              </div>

              <button
                type="button"
                className="concurrency-lane-run"
                disabled={!!running}
                onClick={() => runMode(key)}
              >
                单独运行
              </button>
            </article>
          )
        })}
      </div>

      <p className="concurrency-expect">
        预期：异步 ≪ 同步（3 次等待重叠 vs 相加；进度条满格 = 3 秒）
      </p>
    </div>
  )
}
