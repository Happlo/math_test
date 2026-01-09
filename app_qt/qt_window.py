from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QGridLayout,
    QPushButton,
    QProgressBar,
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QTimer

from math_trainer_core import View, Progress, State, QuestionState

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
    def __init__(self, state: QuestionState):
        super().__init__()
        self._step: State = state

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

        # Timer-bar
        self.time_bar = QProgressBar()
        self.time_bar.setRange(0, 1000)  # vi skalar 0–1000
        self.time_bar.setTextVisible(True)
        layout.addWidget(self.time_bar)

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

        # Qt-timer som driver core.refresh()
        self._timer = QTimer(self)
        self._timer.setInterval(5)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start()

        self.render(self._step.view)

    def render(self, view: View) -> None:
        self.question_label.setText(view.question_text)
        self.feedback_label.setText(view.feedback_text)

        self.streak_label.setText(get_streak_emoji(view.streak))
        self._render_progress_grid(view.progress)

        # Timer-bar baserat på view.time
        if view.time is None:
            self.time_bar.hide()
        else:
            self.time_bar.show()
            total = max(1, view.time.time_per_question_ms)
            left = max(0, min(total, view.time.time_left_ms))
            frac = left / total
            self.time_bar.setValue(int(frac * 1000))
            self.time_bar.setFormat(f"{left / 1000:.1f} s")

        # Input aktiv bara när core säger det
        self.answer_edit.setReadOnly(not view.input_enabled)

        if view.input_enabled:
            self.answer_edit.setFocus()
        else:
            self.next_button.setFocus()

        # Next aktiv bara om state har next()
        is_feedback = hasattr(self._step, "next")
        self.next_button.setEnabled(is_feedback)

    def _on_tick(self) -> None:
        # Bara QuestionState har refresh()
        if hasattr(self._step, "refresh"):
            self._step = self._step.refresh()
            self.render(self._step.view)

    def _on_enter(self) -> None:
        if self._step is None:
            return

        if hasattr(self._step, "answer"):
            self._step = self._step.answer(self.answer_edit.text())
            self.answer_edit.clear()
            self.render(self._step.view)
            return

        if hasattr(self._step, "next"):
            self._step = self._step.next()
            self.answer_edit.clear()
            self.render(self._step.view)

    def _on_next(self) -> None:
        if self._step is None:
            return
        if hasattr(self._step, "next"):
            self._step = self._step.next()
            self.answer_edit.clear()
            self.render(self._step.view)

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
