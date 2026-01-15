from __future__ import annotations

from typing import Optional, List

from PyQt6.QtCore import Qt
Qt.Key.Key_Up
Qt.Key.Key_Down
Qt.Key.Key_Left
Qt.Key.Key_Right
Qt.Key.Key_Return
Qt.Key.Key_Enter
Qt.Key.Key_Escape

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QGridLayout,
    QLineEdit,
    QApplication,
)

from math_trainer_core.api_types import (
    TrainingSelectScreen,
    TrainingGridScreen,
    QuestionScreen,
    TrainingSelectView,
    TrainingGridView,
    QuestionView,
    SelectMove,
    GridMove,
    Progress,
    CellProgress,
    AnswerEvent,
    NextEvent,
    RefreshEvent,
)


# Simple mapping for question streak emoji
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


def _streak_emoji(streak: int) -> str:
    emoji = ""
    for threshold in sorted(STREAK_EMOJIS.keys()):
        if streak >= threshold:
            emoji = STREAK_EMOJIS[threshold]
        else:
            break
    return emoji


class MainWindow(QWidget):
    def __init__(self, screen: TrainingSelectScreen):
        super().__init__()
        self._screen: TrainingSelectScreen = screen
        self._answer_edit: Optional[QLineEdit] = None
        self._last_question_idx: Optional[int] = None
        self._time_label: Optional[QLabel] = None
        self._skip_next_enter: bool = False

        self.setWindowTitle("Math Trainer")

        self._root_layout = QVBoxLayout(self)

        self._title_label = QLabel("")
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self._root_layout.addWidget(self._title_label)

        self._content_widget = QWidget()
        self._content_layout = QVBoxLayout(self._content_widget)
        self._root_layout.addWidget(self._content_widget)

        # Timer for RefreshEvent (question timer updates)
        self._timer = QTimer(self)
        self._timer.setInterval(50)  # ms
        self._timer.timeout.connect(self._on_timer)
        self._timer.start()

        self._render()

    # ------------------------------------------------------------------ GUI → core

    def keyPressEvent(self, event) -> None:
        key = event.key()

        view = self._screen.view

        # Training select: up/down/enter
        if isinstance(view, TrainingSelectView):
            if key == Qt.Key.Key_Up:
                self._screen = self._screen.move(SelectMove.UP)
                self._render()
                return
            if key == Qt.Key.Key_Down:
                self._screen = self._screen.move(SelectMove.DOWN)
                self._render()
                return
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self._screen = self._screen.enter()
                self._render()
                return

        # Training grid: arrows, enter, escape
        if isinstance(view, TrainingGridView):
            if key in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down):
                direction = {
                    Qt.Key.Key_Left: GridMove.LEFT,
                    Qt.Key.Key_Right: GridMove.RIGHT,
                    Qt.Key.Key_Up: GridMove.UP,
                    Qt.Key.Key_Down: GridMove.DOWN,
                }[key]
                self._screen = self._screen.move(direction)
                self._render()
                return

            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self._screen = self._screen.enter()
                self._render()
                return

            if key == Qt.Key.Key_Escape:
                self._screen = self._screen.escape()
                self._render()
                return

        # Question: escape handled here, Enter handled via QLineEdit
        if isinstance(view, QuestionView):
            if key == Qt.Key.Key_Escape:
                self._screen = self._screen.escape()
                self._render()
                return
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                events = self._screen.possible_events
                if view.input_enabled and AnswerEvent in events:
                    if self._answer_edit is not None and not self._answer_edit.hasFocus():
                        self._answer_edit.setFocus(Qt.FocusReason.ActiveWindowFocusReason)
                        return
                    # Let QLineEdit emit returnPressed to avoid double-submit.
                    return
                if (not view.input_enabled) and NextEvent in events:
                    if self._skip_next_enter:
                        self._skip_next_enter = False
                        return
                    self._screen = self._screen.handle(NextEvent())
                    self._render()
                    return

        super().keyPressEvent(event)

    def _on_answer_entered(self) -> None:
        """Called when user presses Enter in the answer box."""
        if not isinstance(self._screen.view, QuestionView):
            return

        view: QuestionView = self._screen.view
        events = self._screen.possible_events

        # If we are in "answer" mode (input enabled)
        if view.input_enabled and AnswerEvent in events:
            text = self._answer_edit.text() if self._answer_edit else ""
            self._screen = self._screen.handle(AnswerEvent(text=text))
            self._skip_next_enter = True
            self._render()
            return

        # If we are in "feedback" mode, NextEvent should be available
        if (not view.input_enabled) and NextEvent in events:
            self._screen = self._screen.handle(NextEvent())
            self._render()
            return

    def _on_timer(self) -> None:
        """Periodic timer -> RefreshEvent for question timer updates."""
        view = self._screen.view
        if not isinstance(view, QuestionView):
            return

        if view.time is None:
            return

        events = self._screen.possible_events
        if RefreshEvent not in events:
            return

        was_input_enabled = view.input_enabled
        was_feedback = view.feedback_text
        was_question_idx = view.question_idx
        was_progress = list(view.progress)
        had_time = view.time is not None

        self._screen = self._screen.handle(RefreshEvent())
        new_view = self._screen.view
        if not isinstance(new_view, QuestionView):
            self._render()
            return

        state_changed = (
            new_view.question_idx != was_question_idx
            or new_view.input_enabled != was_input_enabled
            or new_view.feedback_text != was_feedback
            or new_view.progress != was_progress
            or had_time != (new_view.time is not None)
        )
        if state_changed or self._time_label is None:
            self._render()
            return

        if new_view.time is not None:
            ms_left = max(0, new_view.time.time_left_ms)
            seconds = ms_left / 1000.0
            self._time_label.setText(f"Time left: {seconds:.1f}s")

    # ------------------------------------------------------------------ Rendering

    def _clear_content(self) -> None:
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        self._answer_edit = None
        self._time_label = None

    def _render(self) -> None:
        view = self._screen.view

        if isinstance(view, TrainingSelectView):
            self._render_select(view)
        elif isinstance(view, TrainingGridView):
            self._render_grid(view)
        elif isinstance(view, QuestionView):
            self._render_question(view)
        else:
            # Fallback: just show type name
            self._clear_content()
            self._title_label.setText("Unknown screen")
            label = QLabel(str(view))
            self._content_layout.addWidget(label)

    def _render_select(self, view: TrainingSelectView) -> None:
        self._clear_content()
        self._title_label.setText(view.title)

        for idx, item in enumerate(view.items):
            prefix = "👉 " if idx == view.selected_index else "   "
            text = f"{prefix}{item.icon_text}  {item.label}"
            lbl = QLabel(text)
            lbl.setFont(QFont("Segoe UI", 16))
            self._content_layout.addWidget(lbl)

        if view.items:
            desc = view.items[view.selected_index].description
            desc_lbl = QLabel(desc)
            desc_lbl.setWordWrap(True)
            desc_lbl.setFont(QFont("Segoe UI", 10))
            self._content_layout.addWidget(desc_lbl)

        hint = QLabel("Use ↑/↓ to choose, Enter to start")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._content_layout.addWidget(hint)

    def _render_grid(self, view: TrainingGridView) -> None:
        self._clear_content()
        self._title_label.setText(view.title)

        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(6)

        symbol_map = {
            CellProgress.LOCKED: "⬛",
            CellProgress.AVAILABLE: "⬜",
            CellProgress.COMPLETED: "✅",
            CellProgress.CURRENT: "🟦",
        }

        for y, row in enumerate(view.grid):
            for x, cell in enumerate(row):
                symbol = symbol_map.get(cell, "?")
                lbl = QLabel(symbol)
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl.setFont(QFont("Segoe UI Emoji", 20))
                grid_layout.addWidget(lbl, y, x)

        self._content_layout.addWidget(grid_widget)

        hint = QLabel(view.hint or "Arrows to move, Enter to start, Esc to go back")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._content_layout.addWidget(hint)

    def _render_question(self, view: QuestionView) -> None:
        prev_text = ""
        if self._answer_edit is not None and self._last_question_idx == view.question_idx:
            prev_text = self._answer_edit.text()

        self._clear_content()
        self._title_label.setText("Question")

        # Question text
        q_lbl = QLabel(view.question_text)
        q_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        q_lbl.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        self._content_layout.addWidget(q_lbl)

        # Answer input
        self._answer_edit = QLineEdit()
        self._answer_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._answer_edit.setFont(QFont("Segoe UI", 20))
        self._answer_edit.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._answer_edit.setReadOnly(not view.input_enabled)
        self._answer_edit.returnPressed.connect(self._on_answer_entered)
        if view.input_enabled and prev_text:
            self._answer_edit.setText(prev_text)
        self._content_layout.addWidget(self._answer_edit)

        if view.input_enabled:
            self._skip_next_enter = False
            QTimer.singleShot(
                0,
                lambda: self._answer_edit.setFocus(
                    Qt.FocusReason.ActiveWindowFocusReason
                ),
            )
            self._answer_edit.setCursorPosition(len(self._answer_edit.text()))

        # Feedback
        fb_lbl = QLabel(view.feedback_text)
        fb_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fb_lbl.setFont(QFont("Segoe UI Emoji", 16))
        self._content_layout.addWidget(fb_lbl)

        # Streak emoji
        streak_lbl = QLabel(_streak_emoji(view.streak))
        streak_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        streak_lbl.setFont(QFont("Segoe UI Emoji", 30))
        self._content_layout.addWidget(streak_lbl)

        # Progress row
        progress_widget = QWidget()
        progress_layout = QGridLayout(progress_widget)
        progress_layout.setSpacing(2)

        symbols = {
            Progress.PENDING: "⬜",
            Progress.CORRECT: "🟩",
            Progress.WRONG: "🟥",
            Progress.TIMED_OUT: "🟧",
        }

        columns = max(1, self.width() // 28)
        for i, p in enumerate(view.progress):
            row = i // columns
            col = i % columns
            lbl = QLabel(symbols[p])
            lbl.setFont(QFont("Segoe UI Emoji", 14))
            progress_layout.addWidget(lbl, row, col)

        self._content_layout.addWidget(progress_widget)

        # Timer display (if any)
        if view.time is not None:
            ms_left = max(0, view.time.time_left_ms)
            seconds = ms_left / 1000.0
            self._time_label = QLabel(f"Time left: {seconds:.1f}s")
            self._time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._content_layout.addWidget(self._time_label)

        hint = QLabel("Enter to answer / continue, Esc to go back")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._content_layout.addWidget(hint)

        self._last_question_idx = view.question_idx
