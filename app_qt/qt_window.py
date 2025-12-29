from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QLabel, QLineEdit, QVBoxLayout, QGridLayout, QPushButton
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from math_trainer_core.ports import ViewState, Progress, Step, Finished
from math_trainer_core.core import MathTrainerCore

STREAK_EMOJIS = {
    1: "🌕",
    2: "🦜",
    3: "🌴",
    4: "🪐",
    5: "🐢",
    6: "😃",
    7: "🤓",
    8: "🤩",
    9: "😲",
    12: "🤯",
    30: "🥳🎈🎉🎊",
}


def get_streak_emoji(streak: int) -> str:
    emoji = ""
    for threshold in sorted(STREAK_EMOJIS.keys()):
        if streak >= threshold:
            emoji = STREAK_EMOJIS[threshold]
        else:
            break
    return emoji


class MathWindow(QWidget):
    def __init__(self, core: MathTrainerCore):
        super().__init__()
        self._core = core
        self._step: Step | None = None

        self.setWindowTitle("Matteträning")
        layout = QVBoxLayout()

        self.question_label = QLabel("")
        self.question_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.question_label.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
        layout.addWidget(self.question_label)

        self.answer_edit = QLineEdit()
        self.answer_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.answer_edit.setFont(QFont("Segoe UI", 28))
        self.answer_edit.returnPressed.connect(self._on_enter)
        layout.addWidget(self.answer_edit)

        self.next_button = QPushButton("Nästa")
        self.next_button.clicked.connect(self._on_next)
        layout.addWidget(self.next_button)

        self.feedback_label = QLabel("")
        self.feedback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.feedback_label.setFont(QFont("Segoe UI Emoji", 18))
        layout.addWidget(self.feedback_label)

        self.streak_label = QLabel("")
        self.streak_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.streak_label.setFont(QFont("Segoe UI Emoji", 28))
        layout.addWidget(self.streak_label)

        self.progress_container = QWidget()
        self.progress_layout = QGridLayout(self.progress_container)
        self.progress_layout.setSpacing(4)
        layout.addWidget(self.progress_container)

        self.setLayout(layout)

    # Call this from main after core.start(...)
    def set_step(self, step: Step) -> None:
        self._step = step
        self.render(step.state)

    def render(self, state: ViewState) -> None:
        self.question_label.setText(state.question_text)
        self.feedback_label.setText(state.feedback_text)

        emoji = get_streak_emoji(state.streak)
        self.streak_label.setText(emoji)

        self._render_progress_grid(state.progress)

        # Input is only enabled in QuestionStep
        # self.answer_edit.setDisabled(not state.input_enabled)
        self.answer_edit.setReadOnly(not state.input_enabled)

        if state.input_enabled:
            self.answer_edit.setFocus()

        # Next button enabled in FeedbackStep (i.e. input disabled but game not finished)
        is_finished = isinstance(self._step, Finished) if self._step is not None else False
        self.next_button.setDisabled(state.input_enabled or is_finished)

    def _on_enter(self) -> None:
        if self._step is None:
            return

        # If we are on a question, Enter submits answer.
        if hasattr(self._step, "answer"):
            self._step = self._step.answer(self.answer_edit.text())
            self.answer_edit.clear()
            self.render(self._step.state)
            return

        # If we are on feedback, Enter goes next (nice for keyboard-only).
        if hasattr(self._step, "next"):
            self._step = self._step.next()
            self.answer_edit.clear()
            self.render(self._step.state)

    def _on_next(self) -> None:
        if self._step is None:
            return
        if hasattr(self._step, "next"):
            self._step = self._step.next()
            self.answer_edit.clear()
            self.render(self._step.state)

    def _render_progress_grid(self, progress: list[Progress]) -> None:
        while self.progress_layout.count():
            item = self.progress_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        symbols = {
            Progress.PENDING: "⬜",
            Progress.CORRECT: "🟩",
            Progress.WRONG: "🟥",
            Progress.TIMED_OUT: "🟧",
        }

        columns = max(1, self.width() // 28)

        for i, p in enumerate(progress):
            row = i // columns
            col = i % columns
            lbl = QLabel(symbols[p])
            lbl.setFont(QFont("Segoe UI Emoji", 14))
            self.progress_layout.addWidget(lbl, row, col)
