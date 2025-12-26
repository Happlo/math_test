from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
import random

from ..plugin_api import PluginInfo, IOperatorPlugin, IRandom, Question


@dataclass(frozen=True)
class PlusConfig:
    max_sum: int = 20
    min_operand: int = 2


class PlusPlugin(IOperatorPlugin):
    def __init__(self, cfg: PlusConfig):
        self._cfg = cfg

    def make_question(self) -> Question:
        max_sum = max(0, int(self._cfg.max_sum))
        min_op = max(0, int(self._cfg.min_operand))

        a = random.randint(min_op, max_sum)
        b_max = max_sum - a
        b = random.randint(min_op, b_max) if b_max >= min_op else 0

        return Question(
            display_question=f"{a} + {b} =",
            correct_answer=a + b,
            display_answer_text=f"{a} + {b} = {a + b}",
        )


class PlusPluginFactory:
    @staticmethod
    def PluginInfo() -> PluginInfo:
        return PluginInfo(
            plugin_id="plus",
            name="Addition",
            description="Träna på plus med max-summa.",
        )

    @staticmethod
    def PluginConfig() -> dict[str, Any]:
        # Must include ALL keys with defaults
        cfg = PlusConfig()
        return {
            "max_sum": cfg.max_sum,
            "min_operand": cfg.min_operand,
        }

    @staticmethod
    def CreatePlugin(config: Mapping[str, Any]) -> IOperatorPlugin:
        defaults = PlusPluginFactory.PluginConfig()
        merged = {**defaults, **dict(config)}

        cfg = PlusConfig(
            max_sum=int(merged["max_sum"]),
            min_operand=int(merged["min_operand"]),
        )
        return PlusPlugin(cfg)


PLUGIN_FACTORY = PlusPluginFactory
