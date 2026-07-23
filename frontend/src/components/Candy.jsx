import { useState } from 'react'
import { postCandySolve } from '../lib/api'
import './Candy.css'

const PRESETS = [
  { label: '[1,0,2]', ratings: [1, 0, 2], expect: 5 },
  { label: '[1,2,2]', ratings: [1, 2, 2], expect: 4 },
  { label: '[1,3,2,2,1]', ratings: [1, 3, 2, 2, 1], expect: 7 },
]

/**
 * 分发糖果：题干 + 演示 + 底部官方示例。
 * 求解走后端 Solution.candy。
 */
export default function Candy({ onLog, problem }) {
  const [presetIndex, setPresetIndex] = useState(0)
  const [phase, setPhase] = useState('idle') // idle | left | done | error
  const [leftPass, setLeftPass] = useState(null)
  const [candies, setCandies] = useState(null)
  const [total, setTotal] = useState(null)
  const [busy, setBusy] = useState(false)
  const preset = PRESETS[presetIndex]

  const shownCandies =
    phase === 'idle' || !leftPass
      ? preset.ratings.map(() => 1)
      : phase === 'left'
        ? leftPass
        : candies || leftPass

  const run = async () => {
    if (busy) return
    setBusy(true)
    setPhase('idle')
    try {
      const data = await postCandySolve(preset.ratings)
      for (const line of data.logs || []) onLog?.(line)
      onLog?.(`期望 ${preset.expect}，实际 ${data.total}`)
      setLeftPass(data.left_pass)
      setCandies(data.candies)
      setTotal(data.total)
      setPhase('left')
      window.setTimeout(() => setPhase('done'), 450)
    } catch (err) {
      const message = err?.message || String(err)
      onLog?.(`错误：${message}`)
      setPhase('error')
    } finally {
      setBusy(false)
    }
  }

  const reset = () => {
    setPhase('idle')
    setLeftPass(null)
    setCandies(null)
    setTotal(null)
  }

  return (
    <div className="candy">
      {problem?.statement && (
        <section className="candy-problem">
          <div className="candy-problem-head">
            <h2>题目描述</h2>
            {problem.link && (
              <a href={problem.link} target="_blank" rel="noreferrer">
                力扣原题
              </a>
            )}
          </div>
          <div className="candy-statement">
            {problem.statement.split('\n').map((line, i) =>
              line.trim() === '' ? (
                <br key={`br-${i}`} />
              ) : line.trim().startsWith('- ') ? (
                <p key={`li-${i}`} className="candy-bullet">
                  {line.trim()}
                </p>
              ) : (
                <p key={`p-${i}`}>{line}</p>
              ),
            )}
          </div>

          {problem.hints?.length > 0 && (
            <div className="candy-hints">
              <h3>提示</h3>
              <ul>
                {problem.hints.map((hint) => (
                  <li key={hint}>
                    <code>{hint}</code>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}

      <section className="candy-demo">
        <h2>交互演示</h2>
        <div className="candy-presets" role="group" aria-label="演示样例">
          {PRESETS.map((p, i) => (
            <button
              key={p.label}
              type="button"
              className={`candy-preset ${i === presetIndex ? 'is-active' : ''}`}
              onClick={() => {
                setPresetIndex(i)
                reset()
              }}
            >
              {p.label}
            </button>
          ))}
        </div>

        <div className="candy-row" aria-label="评分与糖数">
          {preset.ratings.map((rating, i) => (
            <div key={`${preset.label}-${i}`} className="candy-child">
              <div className="candy-rating">评分 {rating}</div>
              <div className="candy-bar-wrap">
                <div
                  className="candy-bar"
                  style={{ height: `${Math.max(shownCandies[i], 1) * 18}px` }}
                />
              </div>
              <div className="candy-count">{shownCandies[i]} 颗</div>
              <div className="candy-index">#{i}</div>
            </div>
          ))}
        </div>

        <div className="candy-actions">
          <button type="button" className="candy-run" onClick={run} disabled={busy}>
            {busy ? '求解中…' : '求解并演示'}
          </button>
          <button type="button" className="candy-reset" onClick={reset} disabled={busy}>
            重置
          </button>
        </div>

        <p className="candy-status">
          {phase === 'idle' && '状态：初始（全 1）—— 点「求解并演示」调用后端 Solution.candy'}
          {phase === 'left' && leftPass && `状态：左扫完成 [${leftPass.join(', ')}]`}
          {phase === 'done' && `状态：完成，最少 ${total} 颗（期望 ${preset.expect}）`}
          {phase === 'error' && '状态：后端调用失败，请确认 FastAPI 已启动'}
        </p>
      </section>

      {problem?.examples?.length > 0 && (
        <section className="candy-examples">
          <h2>示例</h2>
          {problem.examples.map((ex) => (
            <article key={ex.title} className="candy-example-card">
              <h3>{ex.title}</h3>
              <p>{ex.input}</p>
              <p>{ex.output}</p>
              {ex.explanation && <p className="candy-example-explain">{ex.explanation}</p>}
            </article>
          ))}
        </section>
      )}
    </div>
  )
}
