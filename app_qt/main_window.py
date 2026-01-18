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
    QHBoxLayout,
    QGridLayout,
    QLineEdit,
    QFrame,
    QProgressBar,
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
    Room,
    RoomProgress,
    Locked,
    Unlocked,
    AnswerEvent,
    NextEvent,
    RefreshEvent,
)


# Simple mapping for mastery level emoji
MASTERY_EMOJIS = {
    0: "🔒",
    1: "🔓",
    2: "👍",
    3: "👌",
    4: "🌟",
    5: "🔥",
    6: "😯",
    7: "😲",
    8: "🤯",
    9: "🚀",
    10: "💎",
}


def _mastery_emoji(streak: int) -> str:
    emoji = ""
    for threshold in sorted(MASTERY_EMOJIS.keys()):
        if streak >= threshold:
            emoji = MASTERY_EMOJIS[threshold]
        else:
            break
    return emoji


class MainWindow(QWidget):
    def __init__(self, screen: TrainingSelectScreen):
        super().__init__()
        self._screen: TrainingSelectScreen = screen
        self._answer_edit: Optional[QLineEdit] = None
        self._last_question_idx: Optional[int] = None
        self._time_bar: Optional[QProgressBar] = None
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
        if state_changed or self._time_bar is None:
            self._render()
            return

        if new_view.time is not None:
            ms_left = max(0, new_view.time.time_left_ms)
            total_ms = max(1, new_view.time.time_per_question_ms)
            self._time_bar.setRange(0, total_ms)
            self._time_bar.setValue(ms_left)

    # ------------------------------------------------------------------ Rendering

    def _clear_content(self) -> None:
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        self._answer_edit = None
        self._time_bar = None

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
        grid_layout.setSpacing(0)

        for room, cell in view.grid.items():
            if isinstance(cell, Locked):
                continue
            room_widget = self._build_room_widget(view, room, cell)
            grid_layout.addWidget(
                room_widget,
                (room.time_pressure - 1) * 2,
                (room.difficulty - 1) * 2,
            )

        for room, cell in view.grid.items():
            right_neighbor = Room(difficulty=room.difficulty + 1, time_pressure=room.time_pressure)
            if right_neighbor in view.grid:
                right_open = isinstance(view.grid[right_neighbor], Unlocked)
                corridor = self._corridor_widget(is_open=right_open, vertical=False)
                grid_layout.addWidget(
                    corridor,
                    (room.time_pressure - 1) * 2,
                    (room.difficulty - 1) * 2 + 1,
                    alignment=Qt.AlignmentFlag.AlignCenter,
                )

            down_neighbor = Room(difficulty=room.difficulty, time_pressure=room.time_pressure + 1)
            if down_neighbor in view.grid:
                down_open = isinstance(view.grid[down_neighbor], Unlocked)
                corridor = self._corridor_widget(is_open=down_open, vertical=True)
                grid_layout.addWidget(
                    corridor,
                    (room.time_pressure - 1) * 2 + 1,
                    (room.difficulty - 1) * 2,
                    alignment=Qt.AlignmentFlag.AlignCenter,
                )

        self._content_layout.addWidget(grid_widget)

        hint = QLabel(view.hint or "Arrows to move, Enter to start, Esc to go back")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._content_layout.addWidget(hint)

    def _build_room_widget(
        self,
        view: TrainingGridView,
        coord: Room,
        cell: RoomProgress,
    ) -> QWidget:
        is_current = coord.difficulty == view.current_x and coord.time_pressure == view.current_y
        mastery_level = cell.mastery_level if isinstance(cell, Unlocked) else 0

        room = QFrame()
        room.setFrameShape(QFrame.Shape.StyledPanel)
        room.setFixedSize(130, 110)
        border_color = "#1e88e5" if is_current else "#5f5f5f"
        room.setStyleSheet(
            "QFrame {"
            f"border: 2px solid {border_color};"
            "border-radius: 8px;"
            "background-color: #f7f2e7;"
            "}"
        )

        layout = QVBoxLayout(room)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(2)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(4)

        mastery_lbl = QLabel(_mastery_emoji(mastery_level) if mastery_level > 0 else "⬜")
        mastery_lbl.setFont(QFont("Segoe UI Emoji", 14))
        header.addWidget(mastery_lbl)

        if is_current:
            turtle_lbl = QLabel("🐢")
            turtle_lbl.setFont(QFont("Segoe UI Emoji", 14))
            header.addWidget(turtle_lbl)

        header.addStretch()
        layout.addLayout(header)

        score = cell.score if isinstance(cell, Unlocked) else 0
        score_lbl = QLabel(f"Score: {score}")
        score_lbl.setFont(QFont("Segoe UI", 9))
        layout.addWidget(score_lbl)

        return room

    def _corridor_widget(self, is_open: bool, vertical: bool) -> QFrame:
        corridor = QFrame()
        if vertical:
            corridor.setFixedSize(24, 24)
        else:
            corridor.setFixedSize(24, 24)
        color = "#7cb342" if is_open else "#b71c1c"
        corridor.setStyleSheet(
            "QFrame {"
            f"background-color: {color};"
            "border-radius: 3px;"
            "}"
        )
        return corridor

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

        if view.time is not None:
            total_ms = max(1, view.time.time_per_question_ms)
            ms_left = max(0, view.time.time_left_ms)
            self._time_bar = QProgressBar()
            self._time_bar.setRange(0, total_ms)
            self._time_bar.setValue(ms_left)
            self._time_bar.setTextVisible(False)
            self._content_layout.addWidget(self._time_bar)

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
        streak_lbl = QLabel(_mastery_emoji(view.mastery_level))
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

        hint = QLabel("Enter to answer / continue, Esc to go back")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._content_layout.addWidget(hint)

        self._last_question_idx = view.question_idx
