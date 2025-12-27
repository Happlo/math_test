from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QLabel, QLineEdit, QVBoxLayout, QGridLayout
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from math_trainer_core.ports import ViewState, Progress
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
    def __init__(self, core):
        super().__init__()
        self._core : MathTrainerCore = core

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

    def render(self, state: ViewState) -> None:
        self.question_label.setText(state.question_text)
        self.feedback_label.setText(state.feedback_text)

        emoji = get_streak_emoji(state.streak)
        self.streak_label.setText(emoji)

        self._render_progress_grid(state.progress)

        self.answer_edit.setDisabled(not state.input_enabled)
        if state.input_enabled:
            self.answer_edit.clear()
            self.answer_edit.setFocus()


    def _on_enter(self) -> None:
        state : ViewState = self._core.submit_answer(self.answer_edit.text())
        self.render(state)

    def _render_progress_grid(self, progress: list[Progress]) -> None:
        # clear previous widgets
        while self.progress_layout.count():
            item = self.progress_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        symbols = {
            Progress.PENDING: "⬜",
            Progress.CORRECT: "🟩",
            Progress.WRONG: "🟥",
        }

        columns = max(1, self.width() // 28)  # responsive to window width

        for i, p in enumerate(progress):
            row = i // columns
            col = i % columns
            lbl = QLabel(symbols[p])
            lbl.setFont(QFont("Segoe UI Emoji", 14))
            self.progress_layout.addWidget(lbl, row, col)