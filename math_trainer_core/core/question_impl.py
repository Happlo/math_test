from __future__ import annotations

from typing import Optional, List
import time

from ..api_types import (
    Progress,
    QuestionTime,
    QuestionView,
    QuestionEvent,
    RefreshEvent,
    AnswerEvent,
    NextEvent,
)
from ..plugins.plugin_api import Plugin, AnswerResult, QuestionResult


DEFAULT_TIME_LIMIT_MS: Optional[int] = None  # e.g. 5000 for 5 seconds
_MAX_MASTERY_LEVEL = 10


def _now_ms() -> int:
    return int(time.monotonic() * 1000)


class QuestionImpl:
    """
    Concrete implementation of QuestionScreen.

    Internal sub-states:
      - waiting for answer
      - showing feedback and waiting for Next
      - finished (no more questions)
    """

    def __init__(
        self,
        plugin: Plugin,
        level_index: int,
        streak_to_advance_mastery: int,
        initial_highest_streak: int = 0,
        time_limit_ms: Optional[int] = DEFAULT_TIME_LIMIT_MS,
    ):
        self._plugin = plugin
        self._level_index = level_index
        self._time_limit_ms = time_limit_ms
        self._streak_to_advance_mastery = max(1, streak_to_advance_mastery)

        # Public view object, mutated in place
        initial_highest = max(0, initial_highest_streak)
        initial_mastery = min(
            initial_highest // self._streak_to_advance_mastery, _MAX_MASTERY_LEVEL
        )
        self._view = QuestionView(
            question_text="",
            feedback_text="",
            current_streak=0,
            highest_streak=initial_highest,
            streak_to_advance_mastery=self._streak_to_advance_mastery,
            mastery_level=initial_mastery,
            progress=[Progress.PENDING],
            question_idx=0,
            input_enabled=True,
            time=None,
        )

        # Internal state
        self._question = self._plugin.make_question(self._level_index)
        self._deadline_ms: Optional[int] = None
        self._awaiting_next: bool = False

        self._start_new_question(initial=True)

    @property
    def view(self) -> QuestionView:
        return self._view

    @property
    def possible_events(self) -> List[type[QuestionEvent]]:
        """
        Expose what makes sense in the current sub-state:
          - waiting for answer: AnswerEvent, RefreshEvent
          - waiting for next:  NextEvent, RefreshEvent (timer is usually off)
        """
        if self._awaiting_next:
            return [NextEvent, RefreshEvent]

        return [AnswerEvent, RefreshEvent]

    def handle(self, event: QuestionEvent) -> QuestionScreen:
        if isinstance(event, RefreshEvent):
            return self._handle_refresh()

        if isinstance(event, AnswerEvent):
            return self._handle_answer(event.text)

        if isinstance(event, NextEvent):
            return self._handle_next()

        return self

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _start_new_question(self, initial: bool = False) -> None:
        """
        Prepare view + timers for the current question_idx.
        """
        if not initial:
            # fetch a new question from plugin
            self._question = self._plugin.make_question(self._level_index)

        self._awaiting_next = False
        self._view.input_enabled = True
        self._view.feedback_text = ""
        if self._view.question_idx >= len(self._view.progress):
            self._view.progress.append(Progress.PENDING)

        # timer setup
        if self._time_limit_ms is not None:
            self._deadline_ms = _now_ms() + self._time_limit_ms
            self._view.time = QuestionTime(
                time_per_question_ms=self._time_limit_ms,
                time_left_ms=self._time_limit_ms,
            )
        else:
            self._deadline_ms = None
            self._view.time = None

        # render question text
        self._view.question_text = (
            f"Streak: {self._view.current_streak}\n{self._question.read_question()}"
        )

    def _handle_refresh(self) -> QuestionScreen:
        if self._awaiting_next:
            return self

        if self._deadline_ms is None:
            return self

        remaining = self._deadline_ms - _now_ms()
        if remaining <= 0:
            return self._timeout()

        if self._view.time is not None:
            self._view.time.time_left_ms = remaining
        return self

    def _handle_answer(self, raw_answer: str) -> QuestionScreen:
        if self._awaiting_next:
            # ignore extra answers when waiting for next
            return self

        if self._deadline_ms is not None and _now_ms() >= self._deadline_ms:
            return self._timeout()

        result: QuestionResult = self._question.answer_question(raw_answer)

        if result.result == AnswerResult.INVALID_INPUT:
            self._view.feedback_text = "Please enter a valid number. 🙃"
            return self  # stay on current question, still waiting for answer

        if result.result == AnswerResult.CORRECT:
            self._view.current_streak += 1
            if self._view.current_streak > self._view.highest_streak:
                self._view.highest_streak = self._view.current_streak
                self._view.mastery_level = (
                    min(
                        self._view.highest_streak // self._view.streak_to_advance_mastery,
                        _MAX_MASTERY_LEVEL,
                    )
                )
            self._view.progress[self._view.question_idx] = Progress.CORRECT
            # Advance immediately to the next question on correct answers.
            self._view.question_idx += 1
            self._start_new_question(initial=False)
            return self

        else:  # WRONG
            self._view.current_streak = 0
            self._view.progress[self._view.question_idx] = Progress.WRONG
            self._view.feedback_text = result.display_answer_text

        # We now consider this question "consumed" and wait for Next
        self._awaiting_next = True
        self._view.input_enabled = False
        self._view.time = None  # stop showing timer

        return self

    def _handle_next(self) -> QuestionScreen:
        if not self._awaiting_next:
            # Nothing to advance; ignore
            return self

        # Move to the next question index
        self._view.question_idx += 1

        # Otherwise, start a fresh question
        self._start_new_question(initial=False)
        return self

    def _timeout(self) -> QuestionScreen:
        self._awaiting_next = True
        self._view.current_streak = 0
        self._view.progress[self._view.question_idx] = Progress.TIMED_OUT

        reveal: QuestionResult = self._question.reveal_answer()
        self._view.feedback_text = f"Time is up! ⏰  {reveal.display_answer_text}"

        self._view.time = None
        self._view.input_enabled = False

        return self


# ---------------------------------------------------------------------------
# Factory function for creating a QuestionScreen
# ---------------------------------------------------------------------------

def start_question_session(
    plugin: Plugin,
    level_index: int,
    streak_to_advance_mastery: int,
    initial_highest_streak: int = 0,
    time_limit_ms: Optional[int] = DEFAULT_TIME_LIMIT_MS,
):
    """
    Core entry point for the training grid implementation:
    start a new question session for a given plugin + level.

    GUI never calls this directly; it will call TrainingGridScreen.enter(),
    and your grid implementation will call this function internally.
    """
    return QuestionImpl(
        plugin=plugin,
        level_index=level_index,
        streak_to_advance_mastery=streak_to_advance_mastery,
        initial_highest_streak=initial_highest_streak,
        time_limit_ms=time_limit_ms,
    )
