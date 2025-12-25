from __future__ import annotations

from ..ports import IOperatorPlugin, IRandom, Question


class MinusPlugin(IOperatorPlugin):
    def plugin_id(self) -> str:
        return "minus"

    def make_question(self, rng: IRandom, max_value: int, allow_negative: bool) -> Question:
        max_v = max(1, max_value)
        a = rng.randint(0, max_v)

        if allow_negative:
            b = rng.randint(0, max_v)
        else:
            b = rng.randint(0, a)

        return Question(
            a=a,
            b=b,
            display=f"{a} - {b} =",
            correct_answer=a - b,
        )


PLUGIN = MinusPlugin()
