from __future__ import annotations
from typing import Optional

from .config import TrainerConfig
from .ports import IOperatorPlugin, IRandom, Question, ViewState


class MathTrainerCore:
    def __init__(self, rng: IRandom, operator: IOperatorPlugin):
        self._rng = rng
        self._operator = operator

        self._config: Optional[TrainerConfig] = None
        self._current: Optional[Question] = None
        self._index = 0
        self._score = 0
        self._streak = 0

    def start(self, config: TrainerConfig) -> ViewState:
        self._config = config
        self._index = 0
        self._score = 0
        self._streak = 0
        self._current = None
        return self._next_state(feedback="", streak=self._streak)

    def submit_answer(self, text: str) -> ViewState:
        if self._config is None:
            return ViewState("Not started", "Call start(config) first", False)

        if self._is_finished():
            return self._finished_state()

        assert self._current is not None
        try:
            value = int(text)
        except ValueError:
            return ViewState(self._current.display, "Skriv en siffra! 🙃", True)

        if value == self._current.correct_answer:
            self._score += 1
            self._streak += 1
            feedback = f"Rätt! ⭐  Streak: {self._streak}"
        else:
            feedback = f"Fel ❌  Rätt svar: {self._current.correct_answer}"
            self._streak = 0

        return self._next_state(feedback=feedback, streak=self._streak)

    def _is_finished(self) -> bool:
        assert self._config is not None
        return self._index >= self._config.num_questions

    def _next_state(self, feedback: str, streak: int) -> ViewState:
        assert self._config is not None
        if self._is_finished():
            return self._finished_state()

        self._index += 1
        q = self._operator.make_question(
            rng=self._rng,
            max_value=self._config.max_value,
            allow_negative=self._config.allow_negative,
        )
        self._current = q

        return ViewState(
            question_text=f"Fråga {self._index}:\n{q.display}",
            feedback_text=feedback,
            streak=streak,
            input_enabled=True,
        )

    def _finished_state(self) -> ViewState:
        assert self._config is not None
        return ViewState(
            question_text=f"Klart! Du fick {self._score} av {self._config.num_questions} rätt.",
            feedback_text="",
            input_enabled=False,
        )
