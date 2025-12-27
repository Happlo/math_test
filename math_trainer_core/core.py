from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List
from .ports import Progress, ViewState


from .plugin_api import Plugin, Question, AnswerResult

@dataclass(frozen=True)
class TrainerConfig:
    num_questions: int


class MathTrainerCore:
    def __init__(self, plugin: Plugin):
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
        self._progress = [Progress.PENDING] * cfg.num_questions
        return self._next_question(feedback="")

    def submit_answer(self, text: str) -> ViewState:
        qr = self._current.answer_question(text)

        if qr.result == AnswerResult.INVALID_INPUT:
            return ViewState(
                question_text=self._current.read_question(),
                feedback_text="Skriv en siffra! 🙃",
                streak=self._streak,
                progress=list(self._progress),
                input_enabled=True,
            )

        if qr.result == AnswerResult.CORRECT:
            self._score += 1
            self._streak += 1
            self._progress[self._index - 1] = Progress.CORRECT
            feedback = f"Rätt! ⭐ Antal rätt: {self._score} Streak: {self._streak}"
        else:  # WRONG
            self._streak = 0
            self._progress[self._index - 1] = Progress.WRONG
            feedback = f"Fel ❌  {qr.display_answer_text}"

        if self._index >= self._cfg.num_questions:
            return self._finished_state()

        return self._next_question(feedback=feedback)


    def _next_question(self, feedback: str) -> ViewState:
        self._index += 1
        self._current = self._plugin.make_question()

        return ViewState(
            question_text=f"Fråga {self._index}:\n{self._current.read_question()}",
            feedback_text=feedback,
            streak=self._streak,
            progress=list(self._progress),
            input_enabled=True,
        )


    def _finished_state(self) -> ViewState:
        return ViewState(
            question_text=f"Klart! Du fick {self._score} av {self._cfg.num_questions} rätt.",
            feedback_text="",
            streak=self._streak,
            progress=list(self._progress),
            input_enabled=False,
        )
