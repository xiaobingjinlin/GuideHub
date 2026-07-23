import { useEffect, useMemo, useRef, useState } from 'react'
import { postMainChildThread } from '../lib/api'
import './Concurrency.css'

const BAR_MAX_MS = 3000

const MODE_META = {
  single: {
    label: '单线程',
    hint: 'with 与业务串行，主线程整段被阻塞',
  },
  main_child: {
    label: '主子线程',
    hint: 'daemon 子线程跑 with，主线程并行做业务',
  },
}

const MODE_KEYS = ['single', 'main_child']
const EMPTY_RESULTS = { single: null, main_child: null }
const EMPTY_PROGRESS = { single: 0, main_child: 0 }
const EMPTY_EXTRA = { single: null, main_child: null }

function toBarPercent(elapsedMs) {
  return Math.min(100, (elapsedMs / BAR_MAX_MS) * 100)
}

/**
 * 单线程 vs 主子线程：对比阻塞与总执行效率（布局参考示例三）。
 */
export default function MainChildThread({ onLog, title }) {
  const [running, setRunning] = useState(null)
  const [results, setResults] = useState(EMPTY_RESULTS)
  const [progress, setProgress] = useState(EMPTY_PROGRESS)
  const [extra, setExtra] = useState(EMPTY_EXTRA)
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
      const data = await postMainChildThread(modeKey)
      stopProgressTick()
      if (runId !== runIdRef.current) {
        busyRef.current = false
        return
      }
      for (const line of data.logs || []) onLog?.(line)
      const elapsedSec = Number(data.elapsed)
      const blockedSec = Number(data.blocked)
      setProgress((prev) => ({ ...prev, [modeKey]: toBarPercent(elapsedSec * 1000) }))
      setResults((prev) => ({ ...prev, [modeKey]: elapsedSec }))
      setExtra((prev) => ({
        ...prev,
        [modeKey]: {
          blocked: blockedSec,
          withElapsed: Number(data.with_elapsed),
          businessElapsed: Number(data.business_elapsed),
        },
      }))
      onLog?.(
        `${meta.label}：总耗时 ${elapsedSec.toFixed(2)}s；主线程阻塞约 ${blockedSec.toFixed(modeKey === 'main_child' ? 4 : 2)}s`,
      )
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
    setExtra({ ...EMPTY_EXTRA })
    onLog?.('======== 开始对比：单线程 vs 主子线程 ========')
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
    setExtra({ ...EMPTY_EXTRA })
    setError('')
    onLog?.('已重置对比结果')
  }

  return (
    <div className="concurrency concurrency-io">
      <header className="concurrency-hero">
        <p className="concurrency-eyebrow">主线程与子线程</p>
        <h1 className="concurrency-title">{title || '主线程与子线程'}</h1>
        <p className="concurrency-subtitle">
          同一份工作：对比单线程串行阻塞，与主子线程并行的效率差异
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
          const detail = extra[key]
          const widthPct = progress[key] ?? 0
          const isRunning = running === key
          const isWinner = winner === key

          return (
            <article
              key={key}
              className={[
                'concurrency-lane',
                `mode-${key === 'single' ? 'serial' : 'threads'}`,
                isRunning ? 'is-running' : '',
                isWinner ? 'is-winner' : '',
              ].join(' ')}
              style={{ animationDelay: `${index * 60}ms` }}
            >
              <div className="concurrency-lane-top">
                <div>
                  <h2>{meta.label}</h2>
                  <p>
                    {meta.hint}
                    {detail
                      ? ` · 阻塞 ${detail.blocked.toFixed(key === 'main_child' ? 4 : 2)}s`
                      : ''}
                  </p>
                </div>
                <div className="concurrency-lane-meta">
                  {isWinner && <span className="concurrency-badge">总耗时更短</span>}
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
        预期：单线程总耗时 ≈ with + 业务；主子线程 ≈ max(with, 业务)，且主线程几乎不被阻塞（进度条满格 = 3
        秒）
      </p>
    </div>
  )
}
