from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, List
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
class AlphabetOrderConfig:
    num_chars: int = 4          # how many characters to show
    case: str = "lower"         # "lower" or "upper"


@dataclass(frozen=True)
class AlphabetOrderQuestion(Question):
    shown: List[str]
    correct_order: List[str]

    def read_question(self) -> str:
        shown = " ".join(self.shown)
        return f"Sätt bokstäverna i alfabetisk ordning:\n{shown}"

    def answer_question(self, answer: str) -> QuestionResult:
        # normalize input: remove spaces, take characters
        raw = answer.strip().replace(" ", "")

        if len(raw) != len(self.correct_order):
            return QuestionResult(
                AnswerResult.INVALID_INPUT,
                f"Rätt ordning: {' '.join(self.correct_order)}",
            )

        given = list(raw)

        if given == self.correct_order:
            return QuestionResult(
                AnswerResult.CORRECT,
                f"Rätt ordning: {' '.join(self.correct_order)}",
            )

        return QuestionResult(
            AnswerResult.WRONG,
            f"Rätt ordning: {' '.join(self.correct_order)}",
        )


class AlphabetOrderPlugin(Plugin):
    def __init__(self, cfg: AlphabetOrderConfig):
        self._cfg = cfg

    def make_question(self) -> Question:
        alphabet = _SWEDISH_ALPHABET
        if self._cfg.case == "upper":
            alphabet = alphabet.upper()

        num_chars = max(2, int(self._cfg.num_chars))
        num_chars = min(num_chars, len(alphabet))

        chars = random.sample(list(alphabet), num_chars)

        correct = sorted(chars, key=lambda c: alphabet.index(c))
        shuffled = chars[:]
        random.shuffle(shuffled)

        return AlphabetOrderQuestion(
            shown=shuffled,
            correct_order=correct,
        )


class AlphabetOrderPluginFactory:
    @staticmethod
    def PluginInfo() -> PluginInfo:
        return PluginInfo(
            id="alphabet_order_se",
            name="Alfabetisk ordning (svenska)",
            description="Sätt bokstäver i alfabetisk ordning (inkl. å, ä, ö).",
        )

    @staticmethod
    def PluginConfig() -> dict[str, Any]:
        cfg = AlphabetOrderConfig()
        return {
            "num_chars": cfg.num_chars,
            "case": cfg.case,
        }

    @staticmethod
    def CreatePlugin(config: Mapping[str, Any]) -> Plugin:
        defaults = AlphabetOrderPluginFactory.PluginConfig()
        merged = {**defaults, **dict(config)}

        case = str(merged["case"]).lower()
        if case not in {"lower", "upper"}:
            case = "lower"

        cfg = AlphabetOrderConfig(
            num_chars=int(merged["num_chars"]),
            case=case,
        )
        return AlphabetOrderPlugin(cfg)


#PLUGIN_FACTORY = AlphabetOrderPluginFactory
