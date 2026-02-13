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

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QPoint, QEasingCurve, QEvent
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLineEdit,
    QFrame,
    QProgressBar,
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
from math_trainer_core.plugins.plugin_api import AnswerButton


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
    request_login = pyqtSignal()

    def __init__(self, screen: TrainingSelectScreen):
        super().__init__()
        self._screen: TrainingSelectScreen = screen
        self._answer_edit: Optional[QLineEdit] = None
        self._last_question_idx: Optional[int] = None
        self._time_bar: Optional[QProgressBar] = None
        self._skip_next_enter: bool = False
        self._last_grid_move: Optional[GridMove] = None
        self._last_grid_centered_before: Optional[bool] = None
        self._grid_anim: Optional[QPropertyAnimation] = None
        self._turtle_anim: Optional[QPropertyAnimation] = None

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

    def _accepted_answer_buttons(self) -> List[AnswerButton]:
        buttons = getattr(self._screen, "accepted_answer_buttons", None)
        if buttons is None:
            return [AnswerButton.SPACE, AnswerButton.ENTER]
        return list(buttons)

    def _accepted_answer_keys(self) -> set[Qt.Key]:
        keys: set[Qt.Key] = set()
        buttons = self._accepted_answer_buttons()
        if AnswerButton.ENTER in buttons:
            keys.update({Qt.Key.Key_Return, Qt.Key.Key_Enter})
        if AnswerButton.SPACE in buttons:
            keys.add(Qt.Key.Key_Space)
        return keys

    # ------------------------------------------------------------------ GUI → core
    def _window_range(
        self, center: int, min_value: int, max_value: int, size: int
    ) -> tuple[int, int]:
        span = max_value - min_value + 1
        if span <= size:
            return min_value, max_value
        half = size // 2
        start = max(min_value, center - half)
        end = start + size - 1
        if end > max_value:
            end = max_value
            start = end - size + 1
        return start, end

    def _grid_window(self, view: TrainingGridView, max_window: int) -> tuple[int, int, int, int]:
        max_x = max(room.difficulty for room in view.grid)
        max_y = max(room.time_pressure for room in view.grid)
        x_start, x_end = self._window_range(view.current_x, 1, max_x, max_window)
        y_start, y_end = self._window_range(view.current_y, 1, max_y, max_window)
        return x_start, x_end, y_start, y_end

    def _is_grid_window_centered(self, view: TrainingGridView, max_window: int) -> bool:
        if not view.grid:
            return False
        x_start, x_end, y_start, y_end = self._grid_window(view, max_window)
        cols = x_end - x_start + 1
        rows = y_end - y_start + 1
        half_window = max_window // 2
        return (
            cols == max_window
            and rows == max_window
            and x_start == view.current_x - half_window
            and y_start == view.current_y - half_window
        )

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
            if key == Qt.Key.Key_Escape:
                self.request_login.emit()
                return

        # Training grid: arrows, enter, escape
        if isinstance(view, TrainingGridView):
            if key in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down):
                old_x, old_y = view.current_x, view.current_y
                was_centered = self._is_grid_window_centered(view, 5)
                direction = {
                    Qt.Key.Key_Left: GridMove.LEFT,
                    Qt.Key.Key_Right: GridMove.RIGHT,
                    Qt.Key.Key_Up: GridMove.UP,
                    Qt.Key.Key_Down: GridMove.DOWN,
                }[key]
                self._screen = self._screen.move(direction)
                new_view = self._screen.view
                if isinstance(new_view, TrainingGridView) and (
                    new_view.current_x != old_x or new_view.current_y != old_y
                ):
                    self._last_grid_move = direction
                    self._last_grid_centered_before = was_centered
                else:
                    self._last_grid_move = None
                    self._last_grid_centered_before = None
                self._render()
                return

            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self._last_grid_move = None
                self._last_grid_centered_before = None
                self._screen = self._screen.enter()
                self._render()
                return

            if key == Qt.Key.Key_Escape:
                self._last_grid_move = None
                self._last_grid_centered_before = None
                self._screen = self._screen.escape()
                self._render()
                return

        # Question: escape handled here, Enter handled via QLineEdit
        if isinstance(view, QuestionView):
            if key == Qt.Key.Key_Escape:
                self._last_grid_move = None
                self._last_grid_centered_before = None
                self._screen = self._screen.escape()
                self._render()
                return
            if key in self._accepted_answer_keys():
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
        meta = QLabel(f"Player: {view.player_name}  |  Total score: {view.total_score}")
        meta.setFont(QFont("Segoe UI", 11))
        meta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._content_layout.addWidget(meta)

        for idx, item in enumerate(view.items):
            prefix = "👉 " if idx == view.selected_index else "   "
            text = f"{prefix}{item.icon_text}  {item.label} (Score: {item.score})"
            lbl = QLabel(text)
            lbl.setFont(QFont("Segoe UI", 16))
            self._content_layout.addWidget(lbl)

        if view.items:
            desc = view.items[view.selected_index].description
            desc_lbl = QLabel(desc)
            desc_lbl.setWordWrap(True)
            desc_lbl.setFont(QFont("Segoe UI", 10))
            self._content_layout.addWidget(desc_lbl)

        hint = QLabel("Use ↑/↓ to choose, Enter to start, Esc for login")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._content_layout.addWidget(hint)

    def _render_grid(self, view: TrainingGridView) -> None:
        self._clear_content()
        self._title_label.setText(view.title)

        if not view.grid:
            empty = QLabel("No rooms available")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._content_layout.addWidget(empty)
            return

        room_w, room_h = 130, 110
        corridor_size = 24
        max_window = 5
        x_start, x_end, y_start, y_end = self._grid_window(view, max_window)

        def _in_window(room: Room) -> bool:
            return x_start <= room.difficulty <= x_end and y_start <= room.time_pressure <= y_end

        cols = x_end - x_start + 1
        rows = y_end - y_start + 1
        total_w = cols * room_w + max(0, cols - 1) * corridor_size
        total_h = rows * room_h + max(0, rows - 1) * corridor_size
        window_centered = self._is_grid_window_centered(view, max_window)

        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(0)

        for room, cell in view.grid.items():
            if isinstance(cell, Locked):
                continue
            if not _in_window(room):
                continue
            room_widget = self._build_room_widget(view, room, cell)
            grid_layout.addWidget(
                room_widget,
                (room.time_pressure - y_start) * 2,
                (room.difficulty - x_start) * 2,
            )

        for room, cell in view.grid.items():
            if not _in_window(room):
                continue
            right_neighbor = Room(difficulty=room.difficulty + 1, time_pressure=room.time_pressure)
            if right_neighbor in view.grid and _in_window(right_neighbor):
                right_open = isinstance(view.grid[right_neighbor], Unlocked)
                corridor = self._corridor_widget(is_open=right_open, vertical=False)
                grid_layout.addWidget(
                    corridor,
                    (room.time_pressure - y_start) * 2,
                    (room.difficulty - x_start) * 2 + 1,
                    alignment=Qt.AlignmentFlag.AlignCenter,
                )

            down_neighbor = Room(difficulty=room.difficulty, time_pressure=room.time_pressure + 1)
            if down_neighbor in view.grid and _in_window(down_neighbor):
                down_open = isinstance(view.grid[down_neighbor], Unlocked)
                corridor = self._corridor_widget(is_open=down_open, vertical=True)
                grid_layout.addWidget(
                    corridor,
                    (room.time_pressure - y_start) * 2 + 1,
                    (room.difficulty - x_start) * 2,
                    alignment=Qt.AlignmentFlag.AlignCenter,
                )

        grid_widget.setFixedSize(total_w, total_h)

        viewport = QWidget()
        viewport.setFixedSize(total_w, total_h)
        grid_widget.setParent(viewport)

        offset_x = 0
        offset_y = 0
        step_x = room_w + corridor_size
        step_y = room_h + corridor_size
        if self._last_grid_move == GridMove.LEFT:
            offset_x = step_x
        elif self._last_grid_move == GridMove.RIGHT:
            offset_x = -step_x
        elif self._last_grid_move == GridMove.UP:
            offset_y = step_y
        elif self._last_grid_move == GridMove.DOWN:
            offset_y = -step_y

        if self._grid_anim is not None:
            self._grid_anim.stop()
            self._grid_anim = None

        if self._turtle_anim is not None:
            self._turtle_anim.stop()
            self._turtle_anim = None

        grid_widget.move(QPoint(offset_x, offset_y))
        if (
            window_centered
            and self._last_grid_centered_before
            and (offset_x != 0 or offset_y != 0)
        ):
            anim = QPropertyAnimation(grid_widget, b"pos", self)
            anim.setDuration(240)
            anim.setStartValue(QPoint(offset_x, offset_y))
            anim.setEndValue(QPoint(0, 0))
            anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
            anim.start()
            self._grid_anim = anim
        else:
            grid_widget.move(QPoint(0, 0))

        turtle_lbl = QLabel("🐢", parent=viewport)
        turtle_lbl.setFont(QFont("Segoe UI Emoji", 16))
        turtle_lbl.adjustSize()
        turtle_size = turtle_lbl.sizeHint()
        turtle_margin_x = max(0, (room_w - turtle_size.width()) // 2)
        turtle_margin_y = max(0, (room_h - turtle_size.height()) // 2)

        def _cell_top_left(room: Room) -> QPoint:
            col = room.difficulty - x_start
            row = room.time_pressure - y_start
            return QPoint(col * step_x, row * step_y)

        def _turtle_pos(room: Room) -> QPoint:
            top_left = _cell_top_left(room)
            return QPoint(
                top_left.x() + turtle_margin_x,
                top_left.y() + turtle_margin_y,
            )

        current_room = Room(difficulty=view.current_x, time_pressure=view.current_y)
        current_pos = _turtle_pos(current_room)

        animate_turtle = (
            self._last_grid_move is not None
            and not (window_centered and self._last_grid_centered_before)
        )
        if animate_turtle:
            if self._last_grid_move == GridMove.LEFT:
                prev_room = Room(difficulty=view.current_x + 1, time_pressure=view.current_y)
            elif self._last_grid_move == GridMove.RIGHT:
                prev_room = Room(difficulty=view.current_x - 1, time_pressure=view.current_y)
            elif self._last_grid_move == GridMove.UP:
                prev_room = Room(difficulty=view.current_x, time_pressure=view.current_y + 1)
            else:
                prev_room = Room(difficulty=view.current_x, time_pressure=view.current_y - 1)

            if _in_window(prev_room):
                start_pos = _turtle_pos(prev_room)
                turtle_lbl.move(start_pos)
                anim = QPropertyAnimation(turtle_lbl, b"pos", self)
                anim.setDuration(200)
                anim.setStartValue(start_pos)
                anim.setEndValue(current_pos)
                anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
                anim.start()
                self._turtle_anim = anim
            else:
                turtle_lbl.move(current_pos)
        else:
            turtle_lbl.move(current_pos)
        turtle_lbl.raise_()

        self._content_layout.addWidget(viewport, alignment=Qt.AlignmentFlag.AlignCenter)
        self._last_grid_move = None
        self._last_grid_centered_before = None

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

        # Pictures (if any)
        if view.optional_question_pictures:
            # Keep pictures within the visible window area on Wayland/X11.
            # Unbounded height requests can trigger compositor protocol errors.
            max_width = min(1200, max(240, self.width() - 80))
            max_height = min(700, max(220, self.height() - 280))
            for item in view.optional_question_pictures:
                pixmap = QPixmap(str(item.picture))
                if pixmap.isNull():
                    missing_lbl = QLabel(f"[missing image: {item.picture}]")
                    missing_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    missing_lbl.setFont(QFont("Segoe UI", 10))
                    self._content_layout.addWidget(missing_lbl)
                else:
                    image_lbl = QLabel()
                    image_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    image_lbl.setPixmap(
                        pixmap.scaled(
                            max_width,
                            max_height,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                    )
                    self._content_layout.addWidget(image_lbl)

                if item.optional_text:
                    caption_lbl = QLabel(item.optional_text)
                    caption_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    caption_lbl.setFont(QFont("Segoe UI", 12))
                    self._content_layout.addWidget(caption_lbl)

        # Answer input
        self._answer_edit = QLineEdit()
        self._answer_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._answer_edit.setFont(QFont("Segoe UI", 20))
        self._answer_edit.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._answer_edit.setReadOnly(not view.input_enabled)
        self._answer_edit.returnPressed.connect(self._on_answer_entered)
        self._answer_edit.installEventFilter(self)
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

        hint = QLabel(self._question_hint_text())
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._content_layout.addWidget(hint)

        self._last_question_idx = view.question_idx

    def _question_hint_text(self) -> str:
        buttons = self._accepted_answer_buttons()
        if AnswerButton.SPACE in buttons and AnswerButton.ENTER in buttons:
            accept = "Enter/Space"
        elif AnswerButton.SPACE in buttons:
            accept = "Space"
        else:
            accept = "Enter"
        return f"{accept} to answer / continue, Esc to go back"

    def eventFilter(self, obj, event) -> bool:
        if obj is self._answer_edit and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Space:
                if AnswerButton.SPACE in self._accepted_answer_buttons():
                    self._on_answer_entered()
                    return True
        return super().eventFilter(obj, event)
