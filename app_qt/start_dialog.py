from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPlainTextEdit,
    QSpinBox,
    QVBoxLayout,
    QHBoxLayout,
)
from PyQt6.QtCore import Qt


@dataclass(frozen=True)
class StartSelection:
    plugin_id: str
    num_questions: int
    overrides: dict[str, Any]


def _defaults_to_kv_text(defaults: dict[str, Any]) -> str:
    lines = []
    for key in sorted(defaults.keys()):
        lines.append(f"{key}={defaults[key]}")
    return "\n".join(lines)


def _parse_kv_text(text: str, defaults: dict[str, Any]) -> dict[str, Any]:
    merged = dict(defaults)

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if key not in defaults:
            continue

        default = defaults[key]
        if isinstance(default, bool):
            merged[key] = value.lower() in {"1", "true", "yes", "y", "on"}
        elif isinstance(default, int):
            merged[key] = int(value)
        else:
            merged[key] = value

    # return only overrides (diff vs defaults)
    return {k: v for k, v in merged.items() if v != defaults[k]}


class StartDialog(QDialog):
    def __init__(self, loaded_plugins: dict, parent=None):
        super().__init__(parent)
        self._loaded_plugins = loaded_plugins
        self._current_defaults: dict[str, Any] = {}

        self.setWindowTitle("Start")
        self.setModal(True)

        root = QVBoxLayout(self)

        row = QHBoxLayout()
        row.addWidget(QLabel("Plugin:"))

        self.plugin_combo = QComboBox()
        for plugin_id, loaded in sorted(loaded_plugins.items()):
            info = loaded.info
            self.plugin_combo.addItem(f"{info.name} ({info.plugin_id})", userData=info.plugin_id)
        self.plugin_combo.currentIndexChanged.connect(self._on_plugin_changed)
        row.addWidget(self.plugin_combo)
        root.addLayout(row)

        qrow = QHBoxLayout()
        qrow.addWidget(QLabel("Antal frågor:"))
        self.num_questions = QSpinBox()
        self.num_questions.setRange(1, 500)
        self.num_questions.setValue(40)
        qrow.addWidget(self.num_questions)
        qrow.addStretch(1)
        root.addLayout(qrow)

        root.addWidget(QLabel("Config (key=value), # för kommentarer:"))

        self.config_edit = QPlainTextEdit()
        self.config_edit.setMinimumHeight(180)
        root.addWidget(self.config_edit)

        self.desc_label = QLabel("")
        self.desc_label.setWordWrap(True)
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        root.addWidget(self.desc_label)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self._on_plugin_changed()

    def selection(self) -> StartSelection:
        plugin_id = self.plugin_combo.currentData()
        overrides = _parse_kv_text(self.config_edit.toPlainText(), self._current_defaults)
        return StartSelection(plugin_id=plugin_id, num_questions=int(self.num_questions.value()), overrides=overrides)

    def _on_plugin_changed(self) -> None:
        plugin_id = self.plugin_combo.currentData()
        loaded = self._loaded_plugins[plugin_id]

        self._current_defaults = loaded.factory.PluginConfig()
        self.config_edit.setPlainText(_defaults_to_kv_text(self._current_defaults))
        self.desc_label.setText(loaded.info.description)
