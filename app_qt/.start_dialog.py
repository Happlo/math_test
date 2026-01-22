from dataclasses import dataclass
from typing import Any, Callable

from PyQt6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QLabel, QPlainTextEdit, QSpinBox, QVBoxLayout, QHBoxLayout


@dataclass(frozen=True)
class StartSelection:
    mode_id: str
    num_questions: int
    timer_seconds: int  # 0 = no timer
    overrides: dict[str, Any]


class StartDialog(QDialog):
    def __init__(self, modes, get_defaults: Callable[[str], dict[str, Any]], parent=None):
        super().__init__(parent)
        self._modes = modes
        self._get_defaults = get_defaults
        self._current_defaults: dict[str, Any] = {}

        self.setWindowTitle("Start")
        root = QVBoxLayout(self)

        row = QHBoxLayout()
        row.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        for m in modes:
            self.mode_combo.addItem(f"{m.name} ({m.mode_id})", userData=m.mode_id)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        row.addWidget(self.mode_combo)
        root.addLayout(row)

        qrow = QHBoxLayout()
        qrow.addWidget(QLabel("Antal frågor:"))
        self.num_questions = QSpinBox()
        self.num_questions.setRange(1, 500)
        self.num_questions.setValue(40)
        qrow.addWidget(self.num_questions)
        qrow.addStretch(1)
        root.addLayout(qrow)

        trow = QHBoxLayout()
        trow.addWidget(QLabel("Timer per fråga (sek):"))
        self.timer_seconds = QSpinBox()
        self.timer_seconds.setRange(0, 3600)  # 0 = off
        self.timer_seconds.setValue(0)
        trow.addWidget(self.timer_seconds)
        trow.addStretch(1)
        root.addLayout(trow)


        root.addWidget(QLabel("Config (key=value):"))
        self.config_edit = QPlainTextEdit()
        self.config_edit.setMinimumHeight(180)
        root.addWidget(self.config_edit)

        self.desc_label = QLabel("")
        self.desc_label.setWordWrap(True)
        root.addWidget(self.desc_label)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self._on_mode_changed()

    def selection(self) -> StartSelection:
        mode_id = self.mode_combo.currentData()
        overrides = _parse_kv_text(self.config_edit.toPlainText(), self._current_defaults)
        return StartSelection(
            mode_id=mode_id,
            num_questions=int(self.num_questions.value()),
            timer_seconds=int(self.timer_seconds.value()),
            overrides=overrides,
        )

    def _on_mode_changed(self) -> None:
        mode_id = self.mode_combo.currentData()
        mode = next(m for m in self._modes if m.mode_id == mode_id)

        self._current_defaults = self._get_defaults(mode_id)
        self.config_edit.setPlainText(_defaults_to_kv_text(self._current_defaults))
        self.desc_label.setText(mode.description)


def _defaults_to_kv_text(defaults: dict[str, Any]) -> str:
    return "\n".join(f"{k}={defaults[k]}" for k in sorted(defaults.keys()))


def _parse_kv_text(text: str, defaults: dict[str, Any]) -> dict[str, Any]:
    merged = dict(defaults)
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = [x.strip() for x in line.split("=", 1)]
        if key not in defaults:
            continue
        default = defaults[key]
        if isinstance(default, bool):
            merged[key] = value.lower() in {"1", "true", "yes", "y", "on"}
        elif isinstance(default, int):
            merged[key] = int(value)
        else:
            merged[key] = value

    return {k: v for k, v in merged.items() if v != defaults[k]}
