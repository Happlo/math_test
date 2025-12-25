from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QLabel, QLineEdit, QVBoxLayout
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from math_trainer_core.ports import ViewState


class MathWindow(QWidget):
    def __init__(self, core):
        super().__init__()
        self._core = core

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

        self.setLayout(layout)

    def render(self, state: ViewState) -> None:
        self.question_label.setText(state.question_text)
        self.feedback_label.setText(state.feedback_text)

        self.answer_edit.setDisabled(not state.input_enabled)
        if state.input_enabled:
            self.answer_edit.clear()
            self.answer_edit.setFocus()

    def _on_enter(self) -> None:
        state = self._core.submit_answer(self.answer_edit.text())
        self.render(state)
