from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from math_trainer_core.api import CoreApi
from math_trainer_core.api_types import AuthError, UserProfile


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._profile: Optional[UserProfile] = None

        self.setWindowTitle("Login")

        root = QVBoxLayout(self)

        title = QLabel("Welcome")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        root.addWidget(title)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Name:"))
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Enter your name")
        self._name_edit.returnPressed.connect(self._on_login)
        name_row.addWidget(self._name_edit)
        root.addLayout(name_row)

        self._error_label = QLabel("")
        self._error_label.setWordWrap(True)
        self._error_label.setStyleSheet("color: #b00020;")
        root.addWidget(self._error_label)

        button_box = QDialogButtonBox()
        self._login_button = QPushButton("Login")
        self._create_button = QPushButton("Create")
        self._cancel_button = QPushButton("Cancel")
        button_box.addButton(self._login_button, QDialogButtonBox.ButtonRole.AcceptRole)
        button_box.addButton(self._create_button, QDialogButtonBox.ButtonRole.ActionRole)
        button_box.addButton(self._cancel_button, QDialogButtonBox.ButtonRole.RejectRole)
        root.addWidget(button_box)

        self._login_button.clicked.connect(self._on_login)
        self._create_button.clicked.connect(self._on_create)
        self._cancel_button.clicked.connect(self.reject)

        self._name_edit.setFocus(Qt.FocusReason.ActiveWindowFocusReason)

    @property
    def profile(self) -> Optional[UserProfile]:
        return self._profile

    def _on_login(self) -> None:
        name = self._name_edit.text()
        result = CoreApi.Login(name)
        self._handle_result(result)

    def _on_create(self) -> None:
        name = self._name_edit.text()
        result = CoreApi.CreateUser(name)
        self._handle_result(result)

    def _handle_result(self, result: UserProfile | AuthError) -> None:
        if isinstance(result, AuthError):
            self._error_label.setText(result.message)
            return
        self._profile = result
        self.accept()
