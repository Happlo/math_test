from __future__ import annotations
from dataclasses import dataclass

from ..ports import IOperatorPlugin, IRandom, Question


class PlusPlugin(IOperatorPlugin):
    def plugin_id(self) -> str:
        return "plus"

    def make_question(self, rng: IRandom, max_value: int, allow_negative: bool) -> Question:
        max_v = max(1, max_value)
        a = rng.randint(0, max_v)
        b = rng.randint(0, max_v - a)
        return Question(
            a=a,
            b=b,
            display=f"{a} + {b} =",
            correct_answer=a + b,
        )


PLUGIN = PlusPlugin()
