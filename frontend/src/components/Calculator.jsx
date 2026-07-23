import { useRef, useState } from 'react'
import { postCalculatorAction } from '../lib/api'
import './Calculator.css'

const INITIAL_STATE = {
  display: '0',
  accumulator: null,
  operator: null,
  fresh: true,
}

const UNARY_API = {
  sin: 'sin',
  cos: 'cos',
  tan: 'tan',
  ln: 'ln',
  log: 'log',
  '√': 'sqrt',
  'x²': 'square',
  '1/x': 'reciprocal',
  '|x|': 'abs',
}

/**
 * 可交互计算器：按键逻辑走后端 Calculator 类。
 */
export default function Calculator({ onLog }) {
  const [mode, setMode] = useState('simple')
  const [state, setState] = useState(INITIAL_STATE)
  const [expression, setExpression] = useState('')
  const [busy, setBusy] = useState(false)
  const stateRef = useRef(INITIAL_STATE)
  const isScientific = mode === 'scientific'

  const applyResponse = (data) => {
    stateRef.current = data.state
    setState(data.state)
    if (data.expression != null) setExpression(data.expression)
    if (data.log) onLog?.(data.log)
  }

  const send = async (action, value = null, extra = {}) => {
    if (busy) return
    setBusy(true)
    try {
      const data = await postCalculatorAction({
        action,
        value,
        state: stateRef.current,
      })
      applyResponse(data)
      if (extra.clearExpression) setExpression('')
      if (typeof extra.expression === 'string') setExpression(extra.expression)
    } catch (err) {
      onLog?.(`错误：${err?.message || String(err)}`)
    } finally {
      setBusy(false)
    }
  }

  const handleDigit = (digit) => {
    if (stateRef.current.fresh) setExpression('')
    send('digit', digit)
  }

  const handleDot = () => {
    if (stateRef.current.fresh) setExpression('')
    send('dot')
  }

  const handleOperator = (op) => send('operator', op)
  const handleEquals = () => send('equals')
  const handleClear = () => {
    setExpression('')
    send('clear')
  }
  const handleNegate = () => send('negate')
  const handleConst = (name) => send('const', name === 'π' ? 'pi' : 'e')
  const handleUnary = (label) => send('unary', UNARY_API[label])

  const toggleMode = () => {
    setMode((m) => (m === 'simple' ? 'scientific' : 'simple'))
    handleClear()
  }

  const screenHint = expression || '\u00a0'
  const { display } = state

  return (
    <div className={`calculator ${isScientific ? 'is-scientific' : ''}`}>
      <div className="calculator-toolbar">
        <button type="button" className="mode-toggle" onClick={toggleMode} disabled={busy}>
          {isScientific ? '切换为简单计算器' : '切换为科学计算器'}
        </button>
      </div>

      <div className="calculator-screen" aria-live="polite">
        <span className="calculator-expression" title={screenHint}>
          {screenHint}
        </span>
        <span className="calculator-value">{display}</span>
      </div>

      {isScientific ? (
        <div className="calculator-pad scientific-pad">
          <button type="button" className="calculator-key key-fn" onClick={() => handleUnary('sin')} disabled={busy}>sin</button>
          <button type="button" className="calculator-key key-fn" onClick={() => handleUnary('cos')} disabled={busy}>cos</button>
          <button type="button" className="calculator-key key-fn" onClick={() => handleUnary('tan')} disabled={busy}>tan</button>
          <button type="button" className="calculator-key key-fn" onClick={() => handleUnary('ln')} disabled={busy}>ln</button>
          <button type="button" className="calculator-key key-fn" onClick={() => handleUnary('log')} disabled={busy}>log</button>

          <button type="button" className="calculator-key key-fn" onClick={() => handleUnary('√')} disabled={busy}>√</button>
          <button type="button" className="calculator-key key-fn" onClick={() => handleUnary('x²')} disabled={busy}>x²</button>
          <button type="button" className="calculator-key key-op" onClick={() => handleOperator('^')} disabled={busy}>xʸ</button>
          <button type="button" className="calculator-key key-fn" onClick={() => handleConst('π')} disabled={busy}>π</button>
          <button type="button" className="calculator-key key-fn" onClick={() => handleConst('e')} disabled={busy}>e</button>

          <button type="button" className="calculator-key key-action" onClick={handleClear} disabled={busy}>C</button>
          <button type="button" className="calculator-key key-fn" onClick={handleNegate} disabled={busy}>±</button>
          <button type="button" className="calculator-key key-op" onClick={() => handleOperator('/')} disabled={busy}>÷</button>
          <button type="button" className="calculator-key key-op" onClick={() => handleOperator('*')} disabled={busy}>×</button>
          <button type="button" className="calculator-key key-op" onClick={() => handleOperator('-')} disabled={busy}>−</button>

          <button type="button" className="calculator-key" onClick={() => handleDigit('7')} disabled={busy}>7</button>
          <button type="button" className="calculator-key" onClick={() => handleDigit('8')} disabled={busy}>8</button>
          <button type="button" className="calculator-key" onClick={() => handleDigit('9')} disabled={busy}>9</button>
          <button type="button" className="calculator-key key-op" onClick={() => handleOperator('+')} disabled={busy}>+</button>
          <button type="button" className="calculator-key key-equals key-equals-cell" onClick={handleEquals} disabled={busy}>=</button>

          <button type="button" className="calculator-key" onClick={() => handleDigit('4')} disabled={busy}>4</button>
          <button type="button" className="calculator-key" onClick={() => handleDigit('5')} disabled={busy}>5</button>
          <button type="button" className="calculator-key" onClick={() => handleDigit('6')} disabled={busy}>6</button>
          <button type="button" className="calculator-key key-fn" onClick={() => handleUnary('1/x')} disabled={busy}>1/x</button>

          <button type="button" className="calculator-key" onClick={() => handleDigit('1')} disabled={busy}>1</button>
          <button type="button" className="calculator-key" onClick={() => handleDigit('2')} disabled={busy}>2</button>
          <button type="button" className="calculator-key" onClick={() => handleDigit('3')} disabled={busy}>3</button>
          <button type="button" className="calculator-key key-fn" onClick={() => handleUnary('|x|')} disabled={busy}>|x|</button>

          <button type="button" className="calculator-key key-zero-sci" onClick={() => handleDigit('0')} disabled={busy}>0</button>
          <button type="button" className="calculator-key" onClick={handleDot} disabled={busy}>.</button>
        </div>
      ) : (
        <div className="calculator-pad">
          <button type="button" className="calculator-key key-action" onClick={handleClear} disabled={busy}>C</button>
          <button type="button" className="calculator-key key-op" onClick={() => handleOperator('/')} disabled={busy}>÷</button>
          <button type="button" className="calculator-key key-op" onClick={() => handleOperator('*')} disabled={busy}>×</button>
          <button type="button" className="calculator-key key-op" onClick={() => handleOperator('-')} disabled={busy}>−</button>

          <button type="button" className="calculator-key" onClick={() => handleDigit('7')} disabled={busy}>7</button>
          <button type="button" className="calculator-key" onClick={() => handleDigit('8')} disabled={busy}>8</button>
          <button type="button" className="calculator-key" onClick={() => handleDigit('9')} disabled={busy}>9</button>
          <button type="button" className="calculator-key key-op" onClick={() => handleOperator('+')} disabled={busy}>+</button>

          <button type="button" className="calculator-key" onClick={() => handleDigit('4')} disabled={busy}>4</button>
          <button type="button" className="calculator-key" onClick={() => handleDigit('5')} disabled={busy}>5</button>
          <button type="button" className="calculator-key" onClick={() => handleDigit('6')} disabled={busy}>6</button>
          <button type="button" className="calculator-key key-equals" onClick={handleEquals} disabled={busy}>=</button>

          <button type="button" className="calculator-key" onClick={() => handleDigit('1')} disabled={busy}>1</button>
          <button type="button" className="calculator-key" onClick={() => handleDigit('2')} disabled={busy}>2</button>
          <button type="button" className="calculator-key" onClick={() => handleDigit('3')} disabled={busy}>3</button>

          <button type="button" className="calculator-key key-zero" onClick={() => handleDigit('0')} disabled={busy}>0</button>
          <button type="button" className="calculator-key" onClick={handleDot} disabled={busy}>.</button>
        </div>
      )}
    </div>
  )
}
