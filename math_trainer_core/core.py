from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import time

from .api_types import Progress, View, State, QuestionState, FeedbackState, FinishedState, TrainerConfig
from .plugin_api import Plugin, AnswerResult, QuestionResult


def _now_ms() -> int:
    return int(time.monotonic() * 1000)


class FinishedImpl(FinishedState):
    def __init__(self, view: View):
        self.view = view  # keep name consistent with your ports (state or view)

def next_question(view: View, plugin: Plugin, config: TrainerConfig) -> State:
    # advance to next question
    view.question_idx += 1

    if view.question_idx >= len(view.progress):
        view.question_text = f"Klart! Du fick {view.score} av {len(view.progress)} rätt."
        view.feedback_text = ""
        view.input_enabled = False
        view.remaining_ms = None
        return FinishedImpl(view)

    return QuestionImpl(view=view, plugin=plugin, config=config)


class FeedbackImpl(FeedbackState):
    def __init__(self, view: View, plugin: Plugin, config: TrainerConfig):
        self.view = view
        self._plugin = plugin
        self._config = config
        self.state = view

        self.view.input_enabled = False
        self.view.remaining_ms = None

    def next(self) -> State:
        return next_question(view=self.view, plugin=self._plugin, config=self._config)


class QuestionImpl(QuestionState):
    def __init__(self, view: View, plugin: Plugin, config: TrainerConfig):
        self.view = view
        self._plugin = plugin
        self._config = config
        self.state = view

        self._question = plugin.make_question()

        self.view.question_text = f"Fråga {self.view.question_idx + 1}:\n{self._question.read_question()}"
        self.view.input_enabled = True

        if config.time_limit_ms is not None and config.time_limit_ms > 0:
            self._deadline_ms = _now_ms() + config.time_limit_ms
            self.view.remaining_ms = config.time_limit_ms
        else:
            self._deadline_ms = None
            self.view.remaining_ms = None

    def answer(self, raw_answer: str) -> State:
        # if timed out, go to feedback first
        if self._deadline_ms is not None and _now_ms() >= self._deadline_ms:
            return self._timeout()

        result: QuestionResult = self._question.answer_question(raw_answer)

        if result.result == AnswerResult.INVALID_INPUT:
            self.view.feedback_text = "Skriv en siffra! 🙃"
            return self  # stay in question state

        if result.result == AnswerResult.CORRECT:
            self.view.score += 1
            self.view.streak += 1
            self.view.progress[self.view.question_idx] = Progress.CORRECT
            self.view.feedback_text = f"Rätt! ⭐ Antal rätt: {self.view.score} Streak: {self.view.streak}"
            return next_question(view=self.view, plugin=self._plugin, config=self._config)
        else:  # WRONG
            self.view.streak = 0
            self.view.progress[self.view.question_idx] = Progress.WRONG
            self.view.feedback_text = f"Fel ❌  {result.display_answer_text}"

        return FeedbackImpl(view=self.view, plugin=self._plugin, config=self._config)

    def refresh(self) -> State:
        if self._deadline_ms is None:
            return self

        remaining = self._deadline_ms - _now_ms()
        if remaining <= 0:
            return self._timeout()

        self.view.remaining_ms = remaining
        return self

    def _timeout(self) -> State:
        self.view.streak = 0
        self.view.progress[self.view.question_idx] = Progress.TIMED_OUT
        self.view.feedback_text = "Tiden är slut! ⏰"
        self.view.remaining_ms = None
        return FeedbackImpl(view=self.view, plugin=self._plugin, config=self._config)


def Start(plugin: Plugin, config: TrainerConfig) -> State:
    # mutable view, owned by states
    view = View(
        question_idx=0,
        question_text="",
        feedback_text="",
        streak=0,
        score=0,
        progress=[Progress.PENDING] * config.num_questions,
        input_enabled=True,
        remaining_ms=None,
    )
    return QuestionImpl(view=view, plugin=plugin, config=config)
