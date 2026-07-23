import { useEffect, useMemo, useRef, useState } from 'react'
import { postConcurrency } from '../lib/api'
import './Concurrency.css'

const BAR_MAX_MS = 3000

const CONFIG = {
  io: {
    eyebrow: 'IO 密集型',
    subtitle: '等待可以重叠时，并发往往更快（后端真实计时）',
    expect: '预期：多线程 ≈ 多进程 ≪ 顺序执行',
  },
  cpu: {
    eyebrow: 'CPU 密集型',
    subtitle: '纯计算时，多进程更能吃到多核（后端真实计时）',
    expect: '预期：多进程 ≪ 多线程 ≈ 顺序执行',
  },
}

const MODE_META = {
  serial: { label: '顺序执行', hint: '一个接一个' },
  threads: { label: '多线程', hint: 'ThreadPoolExecutor' },
  processes: { label: '多进程', hint: 'ProcessPoolExecutor' },
}

const MODE_KEYS = ['serial', 'threads', 'processes']
const EMPTY_RESULTS = { serial: null, threads: null, processes: null }
const EMPTY_PROGRESS = { serial: 0, threads: 0, processes: 0 }

function toBarPercent(elapsedMs) {
  return Math.min(100, (elapsedMs / BAR_MAX_MS) * 100)
}

export default function Concurrency({ onLog, kind = 'io', title }) {
  const scenario = CONFIG[kind] || CONFIG.io
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
    if (entries.length < 3) return null
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

    onLog?.(`—— 开始：${meta.label}（${scenario.eyebrow}）——`)
    const t0 = performance.now()
    startProgressTick(modeKey, t0)

    try {
      const data = await postConcurrency(kind, modeKey)
      stopProgressTick()
      if (runId !== runIdRef.current) {
        busyRef.current = false
        return
      }
      for (const line of data.logs || []) onLog?.(line)
      const elapsedSec = Number(data.elapsed)
      const finalPct = toBarPercent(elapsedSec * 1000)
      setProgress((prev) => ({ ...prev, [modeKey]: finalPct }))
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
    onLog?.(`======== 开始完整对比：${scenario.eyebrow} ========`)
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
    <div className={`concurrency concurrency-${kind}`}>
      <header className="concurrency-hero">
        <p className="concurrency-eyebrow">{scenario.eyebrow}</p>
        <h1 className="concurrency-title">{title || '耗时对比'}</h1>
        <p className="concurrency-subtitle">{scenario.subtitle}</p>
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
                `mode-${key}`,
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
                  {isWinner && <span className="concurrency-badge">最快</span>}
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

      <p className="concurrency-expect">{scenario.expect}（进度条满格 = 3 秒）</p>
    </div>
  )
}
