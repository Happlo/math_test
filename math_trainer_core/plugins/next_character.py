from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
import random

from ..plugin_api import (
    AnswerResult,
    Plugin,
    Question,
    PluginInfo,
    QuestionResult,
)


_SWEDISH_ALPHABET = "abcdefghijklmnopqrstuvwxyzåäö"


@dataclass(frozen=True)
class NextCharConfig:
    min_index: int = 0          # 0 -> 'a'
    max_index: int = 28         # 28 -> 'ö' (so question char max is 27)
    case: str = "lower"         # "lower" or "upper"


@dataclass(frozen=True)
class NextCharQuestion(Question):
    current_char: str
    expected_char: str

    def read_question(self) -> str:
        return f"Nästa bokstav efter '{self.current_char}' är:"

    def answer_question(self, answer: str) -> QuestionResult:
        raw = answer.strip()
        if not raw:
            return QuestionResult(AnswerResult.INVALID_INPUT, f"Rätt svar: {self.expected_char}")

        # Accept first character only
        raw_char = raw[0]

        if raw_char == self.expected_char:
            return QuestionResult(AnswerResult.CORRECT, f"Rätt svar: {self.expected_char}")

        return QuestionResult(AnswerResult.WRONG, f"Rätt svar: {self.expected_char}")


class NextCharPlugin(Plugin):
    def __init__(self, cfg: NextCharConfig):
        self._cfg = cfg

    def make_question(self) -> Question:
        alphabet = _SWEDISH_ALPHABET
        if self._cfg.case == "upper":
            alphabet = alphabet.upper()

        # Ensure indexes are sane and leave room for "next char"
        max_i = min(max(1, int(self._cfg.max_index)), len(alphabet) - 1)
        min_i = max(0, min(int(self._cfg.min_index), max_i - 1))

        idx = random.randint(min_i, max_i - 1)  # -1 so idx+1 is valid
        current_char = alphabet[idx]
        expected_char = alphabet[idx + 1]

        return NextCharQuestion(current_char=current_char, expected_char=expected_char)


class NextCharPluginFactory:
    @staticmethod
    def PluginInfo() -> PluginInfo:
        return PluginInfo(
            id="next_char_se",
            name="Nästa bokstav (svenska alfabetet)",
            description="Frågar efter nästa bokstav i svenska alfabetet (inkl. å, ä, ö).",
        )

    @staticmethod
    def PluginConfig() -> dict[str, Any]:
        cfg = NextCharConfig()
        return {
            "min_index": cfg.min_index,
            "max_index": cfg.max_index,
            "case": cfg.case,  # "lower" or "upper"
        }

    @staticmethod
    def CreatePlugin(config: Mapping[str, Any]) -> Plugin:
        defaults = NextCharPluginFactory.PluginConfig()
        merged = {**defaults, **dict(config)}

        case = str(merged["case"]).lower()
        if case not in {"lower", "upper"}:
            case = "lower"

        cfg = NextCharConfig(
            min_index=int(merged["min_index"]),
            max_index=int(merged["max_index"]),
            case=case,
        )
        return NextCharPlugin(cfg)


#PLUGIN_FACTORY = NextCharPluginFactory
