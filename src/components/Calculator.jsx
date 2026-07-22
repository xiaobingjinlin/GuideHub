import { useState } from 'react'
import './Calculator.css'

function formatResult(n) {
  if (Number.isNaN(n) || !Number.isFinite(n)) return 'Error'
  return Number.isInteger(n) ? String(n) : String(Number(n.toPrecision(12)))
}

function toRadians(deg) {
  return (deg * Math.PI) / 180
}

function formatOp(op) {
  if (op === '*') return '×'
  if (op === '/') return '÷'
  if (op === '-') return '−'
  if (op === '^') return '^'
  return op
}

/** 科学函数表达式展示，如 sin(30)、√10、5² */
function formatUnaryExpression(label, arg) {
  if (label === '√') return `√${arg}`
  if (label === 'x²') return `${arg}²`
  if (label === '1/x') return `1/(${arg})`
  if (label === '|x|') return `|${arg}|`
  return `${label}(${arg})`
}

/**
 * 可交互计算器：简单模式 / 科学模式可切换。
 * 仅在真正发生运算时通过 onLog 回写后台控制台。
 */
export default function Calculator({ onLog }) {
  const [mode, setMode] = useState('simple') // simple | scientific
  const [display, setDisplay] = useState('0')
  const [accumulator, setAccumulator] = useState(null)
  const [operator, setOperator] = useState(null)
  const [fresh, setFresh] = useState(true)
  const [expression, setExpression] = useState('')

  const log = (message) => onLog?.(message)
  const isScientific = mode === 'scientific'

  const commit = (currentDisplay, acc, op) => {
    const value = parseFloat(currentDisplay)
    if (acc === null || op === null) return value
    if (op === '+') return acc + value
    if (op === '-') return acc - value
    if (op === '*') return acc * value
    if (op === '/') return value === 0 ? NaN : acc / value
    if (op === '^') return acc ** value
    return value
  }

  const applyResult = (result, expr) => {
    const shown = formatResult(result)
    setDisplay(shown)
    setExpression(expr)
    setAccumulator(result)
    setOperator(null)
    setFresh(true)
    log(`${expr} = ${shown}`)
  }

  const handleDigit = (digit) => {
    if (fresh) setExpression('')
    const next = fresh || display === '0' ? digit : display + digit
    setDisplay(next)
    setFresh(false)
  }

  const handleDot = () => {
    if (fresh) setExpression('')
    if (fresh) {
      setDisplay('0.')
      setFresh(false)
      return
    }
    if (display.includes('.')) return
    setDisplay(display + '.')
  }

  const handleOperator = (op) => {
    const willCalculate = accumulator !== null && operator !== null
    const left = accumulator
    const prevOp = operator
    const right = display
    const result = commit(display, accumulator, operator)
    const shown = formatResult(result)
    setAccumulator(result)
    setOperator(op)
    setDisplay(shown)
    setFresh(true)
    setExpression(`${shown} ${formatOp(op)}`)
    if (willCalculate) {
      const expr = `${formatResult(left)} ${formatOp(prevOp)} ${right}`
      log(`${expr} = ${shown}`)
    }
  }

  const handleEquals = () => {
    const willCalculate = accumulator !== null && operator !== null
    const left = accumulator
    const prevOp = operator
    const right = display
    const result = commit(display, accumulator, operator)
    const shown = formatResult(result)
    setAccumulator(result)
    setOperator(null)
    setDisplay(shown)
    setFresh(true)
    if (willCalculate) {
      const expr = `${formatResult(left)} ${formatOp(prevOp)} ${right}`
      setExpression(expr)
      log(`${expr} = ${shown}`)
    }
  }

  const handleClear = () => {
    setDisplay('0')
    setAccumulator(null)
    setOperator(null)
    setFresh(true)
    setExpression('')
  }

  const handleNegate = () => {
    if (display === '0' || display === 'Error') return
    const next = display.startsWith('-') ? display.slice(1) : `-${display}`
    setDisplay(next)
    setFresh(false)
  }

  const handleConst = (name, value) => {
    const shown = formatResult(value)
    setDisplay(shown)
    setExpression(name)
    setFresh(true)
    log(`${name} = ${shown}`)
  }

  const handleUnary = (label, fn) => {
    const arg = display
    const value = parseFloat(arg)
    const result = fn(value)
    applyResult(result, formatUnaryExpression(label, arg))
  }

  const toggleMode = () => {
    setMode((m) => (m === 'simple' ? 'scientific' : 'simple'))
    handleClear()
  }

  const screenHint = expression || '\u00a0'

  return (
    <div className={`calculator ${isScientific ? 'is-scientific' : ''}`}>
      <div className="calculator-toolbar">
        <button type="button" className="mode-toggle" onClick={toggleMode}>
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
          <button type="button" className="calculator-key key-fn" onClick={() => handleUnary('sin', (x) => Math.sin(toRadians(x)))}>
            sin
          </button>
          <button type="button" className="calculator-key key-fn" onClick={() => handleUnary('cos', (x) => Math.cos(toRadians(x)))}>
            cos
          </button>
          <button type="button" className="calculator-key key-fn" onClick={() => handleUnary('tan', (x) => Math.tan(toRadians(x)))}>
            tan
          </button>
          <button type="button" className="calculator-key key-fn" onClick={() => handleUnary('ln', (x) => Math.log(x))}>
            ln
          </button>
          <button type="button" className="calculator-key key-fn" onClick={() => handleUnary('log', (x) => Math.log10(x))}>
            log
          </button>

          <button type="button" className="calculator-key key-fn" onClick={() => handleUnary('√', (x) => Math.sqrt(x))}>
            √
          </button>
          <button type="button" className="calculator-key key-fn" onClick={() => handleUnary('x²', (x) => x * x)}>
            x²
          </button>
          <button type="button" className="calculator-key key-op" onClick={() => handleOperator('^')}>
            xʸ
          </button>
          <button type="button" className="calculator-key key-fn" onClick={() => handleConst('π', Math.PI)}>
            π
          </button>
          <button type="button" className="calculator-key key-fn" onClick={() => handleConst('e', Math.E)}>
            e
          </button>

          <button type="button" className="calculator-key key-action" onClick={handleClear}>
            C
          </button>
          <button type="button" className="calculator-key key-fn" onClick={handleNegate}>
            ±
          </button>
          <button type="button" className="calculator-key key-op" onClick={() => handleOperator('/')}>
            ÷
          </button>
          <button type="button" className="calculator-key key-op" onClick={() => handleOperator('*')}>
            ×
          </button>
          <button type="button" className="calculator-key key-op" onClick={() => handleOperator('-')}>
            −
          </button>

          <button type="button" className="calculator-key" onClick={() => handleDigit('7')}>
            7
          </button>
          <button type="button" className="calculator-key" onClick={() => handleDigit('8')}>
            8
          </button>
          <button type="button" className="calculator-key" onClick={() => handleDigit('9')}>
            9
          </button>
          <button type="button" className="calculator-key key-op" onClick={() => handleOperator('+')}>
            +
          </button>
          <button type="button" className="calculator-key key-equals key-equals-cell" onClick={handleEquals}>
            =
          </button>

          <button type="button" className="calculator-key" onClick={() => handleDigit('4')}>
            4
          </button>
          <button type="button" className="calculator-key" onClick={() => handleDigit('5')}>
            5
          </button>
          <button type="button" className="calculator-key" onClick={() => handleDigit('6')}>
            6
          </button>
          <button type="button" className="calculator-key key-fn" onClick={() => handleUnary('1/x', (x) => (x === 0 ? NaN : 1 / x))}>
            1/x
          </button>

          <button type="button" className="calculator-key" onClick={() => handleDigit('1')}>
            1
          </button>
          <button type="button" className="calculator-key" onClick={() => handleDigit('2')}>
            2
          </button>
          <button type="button" className="calculator-key" onClick={() => handleDigit('3')}>
            3
          </button>
          <button type="button" className="calculator-key key-fn" onClick={() => handleUnary('|x|', (x) => Math.abs(x))}>
            |x|
          </button>

          <button type="button" className="calculator-key key-zero-sci" onClick={() => handleDigit('0')}>
            0
          </button>
          <button type="button" className="calculator-key" onClick={handleDot}>
            .
          </button>
        </div>
      ) : (
        <div className="calculator-pad">
          <button type="button" className="calculator-key key-action" onClick={handleClear}>
            C
          </button>
          <button type="button" className="calculator-key key-op" onClick={() => handleOperator('/')}>
            ÷
          </button>
          <button type="button" className="calculator-key key-op" onClick={() => handleOperator('*')}>
            ×
          </button>
          <button type="button" className="calculator-key key-op" onClick={() => handleOperator('-')}>
            −
          </button>

          <button type="button" className="calculator-key" onClick={() => handleDigit('7')}>
            7
          </button>
          <button type="button" className="calculator-key" onClick={() => handleDigit('8')}>
            8
          </button>
          <button type="button" className="calculator-key" onClick={() => handleDigit('9')}>
            9
          </button>
          <button type="button" className="calculator-key key-op" onClick={() => handleOperator('+')}>
            +
          </button>

          <button type="button" className="calculator-key" onClick={() => handleDigit('4')}>
            4
          </button>
          <button type="button" className="calculator-key" onClick={() => handleDigit('5')}>
            5
          </button>
          <button type="button" className="calculator-key" onClick={() => handleDigit('6')}>
            6
          </button>
          <button type="button" className="calculator-key key-equals" onClick={handleEquals}>
            =
          </button>

          <button type="button" className="calculator-key" onClick={() => handleDigit('1')}>
            1
          </button>
          <button type="button" className="calculator-key" onClick={() => handleDigit('2')}>
            2
          </button>
          <button type="button" className="calculator-key" onClick={() => handleDigit('3')}>
            3
          </button>

          <button type="button" className="calculator-key key-zero" onClick={() => handleDigit('0')}>
            0
          </button>
          <button type="button" className="calculator-key" onClick={handleDot}>
            .
          </button>
        </div>
      )}
    </div>
  )
}
