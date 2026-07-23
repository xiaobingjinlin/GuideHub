from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.examples.calculator import Calculator

router = APIRouter()

UNARY_MAP = {
    "sin": "sin",
    "cos": "cos",
    "tan": "tan",
    "ln": "ln",
    "log": "log10",
    "sqrt": "sqrt",
    "square": "square",
    "reciprocal": "reciprocal",
    "abs": "abs",
}


class CalcState(BaseModel):
    display: str = "0"
    accumulator: float | None = None
    operator: str | None = None
    fresh: bool = True


class CalcActionRequest(BaseModel):
    action: str
    value: str | None = None
    state: CalcState | None = None


class CalcActionResponse(BaseModel):
    state: CalcState
    expression: str | None = None
    log: str | None = None


@router.post("/action", response_model=CalcActionResponse)
def calculator_action(body: CalcActionRequest):
    calc = Calculator.from_state(body.state.model_dump() if body.state else None)
    action = body.action
    expression = None
    log = None
    before = calc.display
    before_acc = calc.accumulator
    before_op = calc.operator

    try:
        if action == "digit":
            if not body.value:
                raise HTTPException(400, "digit requires value")
            calc.input_digit(body.value)
        elif action == "dot":
            calc.input_dot()
        elif action == "operator":
            if not body.value:
                raise HTTPException(400, "operator requires value")
            will_calc = calc.accumulator is not None and calc.operator is not None
            left, op, right = calc.accumulator, calc.operator, calc.display
            calc.input_operator(body.value)
            if will_calc:
                log = f"{_fmt_num(left)} {op} {right} = {calc.display}"
            expression = f"{calc.display} {body.value}"
        elif action == "equals":
            will_calc = calc.accumulator is not None and calc.operator is not None
            left, op, right = calc.accumulator, calc.operator, calc.display
            calc.equals()
            if will_calc:
                expression = f"{_fmt_num(left)} {op} {right}"
                log = f"{expression} = {calc.display}"
        elif action == "clear":
            calc.clear()
            expression = ""
        elif action == "negate":
            calc.negate()
        elif action == "const":
            if body.value == "pi":
                calc.const_pi()
                expression = "π"
                log = f"π = {calc.display}"
            elif body.value == "e":
                calc.const_e()
                expression = "e"
                log = f"e = {calc.display}"
            else:
                raise HTTPException(400, "const value must be pi or e")
        elif action == "unary":
            if not body.value or body.value not in UNARY_MAP:
                raise HTTPException(400, "invalid unary")
            method = getattr(calc, UNARY_MAP[body.value])
            method()
            expression = _unary_expr(body.value, before)
            log = f"{expression} = {calc.display}"
        else:
            raise HTTPException(400, f"unknown action: {action}")
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, str(exc)) from exc

    # silence unused in some branches
    _ = (before_acc, before_op)

    return CalcActionResponse(
        state=CalcState(**calc.to_state()),
        expression=expression,
        log=log,
    )


def _fmt_num(n) -> str:
    if n is None:
        return "?"
    if float(n) == int(n):
        return str(int(n))
    return str(n)


def _unary_expr(label: str, arg: str) -> str:
    if label == "sqrt":
        return f"√{arg}"
    if label == "square":
        return f"{arg}²"
    if label == "reciprocal":
        return f"1/({arg})"
    if label == "abs":
        return f"|{arg}|"
    return f"{label}({arg})"
