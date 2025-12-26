from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
import random

from ..plugin_api import PluginInfo, IOperatorPlugin, IRandom, Question


@dataclass(frozen=True)
class MinusConfig:
    max_value: int = 10
    allow_negative: bool = False


class MinusPlugin(IOperatorPlugin):
    def __init__(self, cfg: MinusConfig):
        self._cfg = cfg

    def make_question(self) -> Question:
        max_value = max(0, int(self._cfg.max_value))
        allow_negative = bool(self._cfg.allow_negative)

        a = random.randint(0, max_value)
        b = random.randint(0, max_value) if allow_negative else random.randint(0, a)
        result = a - b

        return Question(
            display_question=f"{a} - {b} =",
            correct_answer=result,
            display_answer_text=f"{a} - {b} = {result}",
        )


class MinusPluginFactory:
    @staticmethod
    def PluginInfo() -> PluginInfo:
        return PluginInfo(
            plugin_id="minus",
            name="Subtraktion",
            description="Träna på minus (val för negativa svar).",
        )

    @staticmethod
    def PluginConfig() -> dict[str, Any]:
        cfg = MinusConfig()
        return {
            "max_value": cfg.max_value,
            "allow_negative": cfg.allow_negative,
        }

    @staticmethod
    def CreatePlugin(config: Mapping[str, Any]) -> IOperatorPlugin:
        defaults = MinusPluginFactory.PluginConfig()
        merged = {**defaults, **dict(config)}

        cfg = MinusConfig(
            max_value=int(merged["max_value"]),
            allow_negative=bool(merged["allow_negative"]),
        )
        return MinusPlugin(cfg)


PLUGIN_FACTORY = MinusPluginFactory
