from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .ports import FeedbackStep, Finished, Progress, QuestionStep, Step, ViewState
from .plugin_api import Plugin, AnswerResult, Question


@dataclass(frozen=True)
class TrainerConfig:
    num_questions: int
    time_limit_ms: Optional[int] = None  # None => no timer


class MathTrainerCore:
    def __init__(self, plugin: Plugin):
        self._plugin = plugin

        self._cfg: Optional[TrainerConfig] = None
        self._index = 0  # 1-based question number when a question is active
        self._score = 0
        self._streak = 0
        self._progress: list[Progress] = []
        self._current: Optional[Question] = None

        # Timer (optional). If you don’t want it yet, keep it unused.
        self._deadline_ms: Optional[int] = None

    def start(self, cfg: TrainerConfig) -> Step:
        self._cfg = cfg
        self._index = 0
        self._score = 0
        self._streak = 0
        self._progress = [Progress.PENDING] * cfg.num_questions
        self._current = None
        self._deadline_ms = None

        return self._enter_next_question(feedback="")

    # ---------- transitions (private) ----------

    def _enter_next_question(self, feedback: str) -> Step:
        assert self._cfg is not None

        if self._index >= self._cfg.num_questions:
            return self._finished_step()

        self._index += 1
        self._current = self._plugin.make_question()

        # Timer: set deadline here when you add a clock.
        # if self._cfg.time_limit_ms:
        #     self._deadline_ms = now_ms + self._cfg.time_limit_ms
        # else:
        self._deadline_ms = None

        state = ViewState(
            question_text=f"Fråga {self._index}:\n{self._current.read_question()}",
            feedback_text=feedback,
            streak=self._streak,
            progress=list(self._progress),
            input_enabled=True,
            remaining_ms=None,
        )
        return _QuestionStepImpl(core=self, state=state)

    def _enter_feedback(self, feedback: str, input_enabled: bool = False) -> Step:
        assert self._cfg is not None
        assert self._current is not None

        state = ViewState(
            question_text=f"Fråga {self._index}:\n{self._current.read_question()}",
            feedback_text=feedback,
            streak=self._streak,
            progress=list(self._progress),
            input_enabled=input_enabled,
            remaining_ms=None,
        )
        return _FeedbackStepImpl(core=self, state=state)

    def _finished_step(self) -> Finished:
        assert self._cfg is not None
        state = ViewState(
            question_text=f"Klart! Du fick {self._score} av {self._cfg.num_questions} rätt.",
            feedback_text="",
            streak=self._streak,
            progress=list(self._progress),
            input_enabled=False,
            remaining_ms=None,
        )
        return Finished(state=state)

    # ---------- actions called by steps (private) ----------

    def _answer_current(self, raw_answer: str) -> Step:
        assert self._cfg is not None
        assert self._current is not None

        qr = self._current.answer_question(raw_answer)

        if qr.result == AnswerResult.INVALID_INPUT:
            # stay on question, don’t advance
            state = ViewState(
                question_text=f"Fråga {self._index}:\n{self._current.read_question()}",
                feedback_text="Skriv en siffra! 🙃",
                streak=self._streak,
                progress=list(self._progress),
                input_enabled=True,
                remaining_ms=None,
            )
            return _QuestionStepImpl(core=self, state=state)

        # mark progress
        idx0 = self._index - 1

        if qr.result == AnswerResult.CORRECT:
            self._score += 1
            self._streak += 1
            self._progress[idx0] = Progress.CORRECT
            feedback = f"Rätt! ⭐ Antal rätt: {self._score} Streak: {self._streak}"
        else:
            self._streak = 0
            self._progress[idx0] = Progress.WRONG
            feedback = f"Fel ❌  {qr.display_answer_text}"

        # Important: do NOT auto-advance. Enter feedback step, wait for next().
        self._deadline_ms = None
        return self._enter_feedback(feedback=feedback)

    def _refresh_current(self) -> Step:
        # Timer handling goes here later. For now: no-op, stay in question.
        assert self._cfg is not None
        assert self._current is not None

        state = ViewState(
            question_text=f"Fråga {self._index}:\n{self._current.read_question()}",
            feedback_text="",  # keep whatever? you can keep last feedback if you want
            streak=self._streak,
            progress=list(self._progress),
            input_enabled=True,
            remaining_ms=None,
        )
        return _QuestionStepImpl(core=self, state=state)

    def _next_after_feedback(self) -> Step:
        # Called when user presses Next after seeing feedback
        return self._enter_next_question(feedback="")

# ---------- step implementations (private classes) ----------

@dataclass(frozen=True)
class _QuestionStepImpl(QuestionStep):
    core: MathTrainerCore
    state: ViewState

    def answer(self, raw_answer: str) -> Step:
        return self.core._answer_current(raw_answer)

    def refresh(self) -> Step:
        return self.core._refresh_current()


@dataclass(frozen=True)
class _FeedbackStepImpl(FeedbackStep):
    core: MathTrainerCore
    state: ViewState

    def next(self) -> Step:
        return self.core._next_after_feedback()
