from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .plugin_api import IRandom, IOperatorPlugin, Question


@dataclass(frozen=True)
class ViewState:
    question_text: str
    feedback_text: str
    streak: int
    input_enabled: bool


@dataclass(frozen=True)
class TrainerConfig:
    num_questions: int


class MathTrainerCore:
    def __init__(self, rng: IRandom, plugin: IOperatorPlugin):
        self._rng = rng
        self._plugin = plugin

        self._cfg: Optional[TrainerConfig] = None

        self._index = 0
        self._score = 0
        self._streak = 0
        self._current: Optional[Question] = None

    def start(self, cfg: TrainerConfig) -> ViewState:
        self._cfg = cfg
        self._index = 0
        self._score = 0
        self._streak = 0
        self._current = None
        return self._next_state(feedback="")

    def submit_answer(self, text: str) -> ViewState:
        if self._cfg is None:
            return ViewState("Not started", "Call start(config) first", 0, False)

        if self._index >= self._cfg.num_questions:
            return self._finished_state()

        assert self._current is not None

        try:
            value = int(text)
        except ValueError:
            return ViewState(
                question_text=self._current.display_question,
                feedback_text="Skriv en siffra! 🙃",
                streak=self._streak,
                input_enabled=True,
            )

        if value == self._current.correct_answer:
            self._score += 1
            self._streak += 1
            feedback = f"Rätt! ⭐  Streak: {self._streak}"
        else:
            feedback = f"Fel ❌  {self._current.display_answer_text}"
            self._streak = 0

        return self._next_state(feedback=feedback)

    def _next_state(self, feedback: str) -> ViewState:
        assert self._cfg is not None

        if self._index >= self._cfg.num_questions:
            return self._finished_state()

        self._index += 1
        self._current = self._plugin.make_question(self._rng)

        return ViewState(
            question_text=f"Fråga {self._index}:\n{self._current.display_question}",
            feedback_text=feedback,
            streak=self._streak,
            input_enabled=True,
        )

    def _finished_state(self) -> ViewState:
        assert self._cfg is not None
        return ViewState(
            question_text=f"Klart! Du fick {self._score} av {self._cfg.num_questions} rätt.",
            feedback_text="",
            streak=self._streak,
            input_enabled=False,
        )
