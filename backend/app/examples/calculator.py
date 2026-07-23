"""
计算器示例 —— 与教程代码中的 Calculator 类对齐。
"""

from __future__ import annotations

import math


class Calculator:
    """封装显示值、累计值与待执行运算符。"""

    def __init__(self) -> None:
        self.display = "0"
        self.accumulator = None
        self.operator = None
        self.fresh = True

    def input_digit(self, digit: str) -> str:
        if self.fresh or self.display == "0":
            self.display = digit
        else:
            self.display += digit
        self.fresh = False
        return self.display

    def input_dot(self) -> str:
        if self.fresh:
            self.display = "0."
            self.fresh = False
            return self.display
        if "." not in self.display:
            self.display += "."
        return self.display

    def input_operator(self, op: str) -> str:
        self._commit()
        self.operator = op
        self.fresh = True
        return self.display

    def equals(self) -> str:
        self._commit()
        self.operator = None
        self.fresh = True
        return self.display

    def clear(self) -> str:
        self.__init__()
        return self.display

    def negate(self) -> str:
        if self.display in {"0", "Error"}:
            return self.display
        if self.display.startswith("-"):
            self.display = self.display[1:]
        else:
            self.display = f"-{self.display}"
        self.fresh = False
        return self.display

    def sin(self) -> str:
        return self._unary(lambda x: math.sin(math.radians(x)))

    def cos(self) -> str:
        return self._unary(lambda x: math.cos(math.radians(x)))

    def tan(self) -> str:
        return self._unary(lambda x: math.tan(math.radians(x)))

    def ln(self) -> str:
        return self._unary(math.log)

    def log10(self) -> str:
        return self._unary(math.log10)

    def sqrt(self) -> str:
        return self._unary(math.sqrt)

    def square(self) -> str:
        return self._unary(lambda x: x * x)

    def reciprocal(self) -> str:
        return self._unary(lambda x: 1 / x)

    def abs(self) -> str:
        return self._unary(abs)

    def const_pi(self) -> str:
        self.display = self._fmt(math.pi)
        self.fresh = True
        return self.display

    def const_e(self) -> str:
        self.display = self._fmt(math.e)
        self.fresh = True
        return self.display

    def _unary(self, fn) -> str:
        value = float(self.display)
        try:
            result = fn(value)
        except (ValueError, ZeroDivisionError, OverflowError):
            self.display = "Error"
            self.accumulator = None
            self.operator = None
            self.fresh = True
            return self.display
        self.display = self._fmt(result)
        self.accumulator = float(self.display) if self.display != "Error" else None
        self.operator = None
        self.fresh = True
        return self.display

    def _commit(self) -> None:
        value = float(self.display)
        if self.accumulator is None or self.operator is None:
            self.accumulator = value
        else:
            a, b, op = self.accumulator, value, self.operator
            if op == "+":
                self.accumulator = a + b
            elif op == "-":
                self.accumulator = a - b
            elif op == "*":
                self.accumulator = a * b
            elif op == "/":
                self.accumulator = a / b if b != 0 else float("nan")
            elif op == "^":
                self.accumulator = a**b
        self.display = self._fmt(self.accumulator)

    @staticmethod
    def _fmt(n) -> str:
        if n != n or n in (float("inf"), float("-inf")):
            return "Error"
        return str(int(n)) if float(n) == int(n) else str(n)

    def to_state(self) -> dict:
        return {
            "display": self.display,
            "accumulator": self.accumulator,
            "operator": self.operator,
            "fresh": self.fresh,
        }

    @classmethod
    def from_state(cls, state: dict | None) -> "Calculator":
        calc = cls()
        if not state:
            return calc
        calc.display = state.get("display", "0")
        calc.accumulator = state.get("accumulator")
        calc.operator = state.get("operator")
        calc.fresh = bool(state.get("fresh", True))
        return calc
