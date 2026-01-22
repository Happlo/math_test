import os
import sys

from PyQt6.QtWidgets import QApplication, QDialog

from math_trainer_core.api import CoreApi
from app_qt.login_dialog import LoginDialog
from app_qt.main_window import MainWindow


def _is_wayland_session() -> bool:
    return os.environ.get("XDG_SESSION_TYPE") == "wayland" or "WAYLAND_DISPLAY" in os.environ


def main() -> int:
    app = QApplication(sys.argv)

    login = LoginDialog()
    if login.exec() != QDialog.DialogCode.Accepted or login.profile is None:
        return 0

    # Start in training select screen
    screen = CoreApi.Start(login.profile)

    window = MainWindow(screen)
    if not _is_wayland_session():
        window.resize(640, 480)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
