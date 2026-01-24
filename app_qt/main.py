import os
import sys

from PyQt6.QtCore import QObject, QRect
from PyQt6.QtWidgets import QApplication, QDialog

from math_trainer_core.api import CoreApi
from app_qt.login_dialog import LoginDialog
from app_qt.main_window import MainWindow


def _is_wayland_session() -> bool:
    return os.environ.get("XDG_SESSION_TYPE") == "wayland" or "WAYLAND_DISPLAY" in os.environ


class AppController(QObject):
    def __init__(self, app: QApplication):
        super().__init__()
        self._app = app
        self._window: MainWindow | None = None
        self._last_window_geometry: QRect | None = None

    def start(self) -> None:
        self._show_login()

    def _show_login(self) -> None:
        login_screen = CoreApi.CreateLoginScreen()
        login = LoginDialog(login_screen)
        if self._last_window_geometry is not None:
            login.move(self._last_window_geometry.topLeft())
        if login.exec() != QDialog.DialogCode.Accepted or login.profile is None:
            self._app.quit()
            return

        screen = login_screen.Start(login.profile)
        window = MainWindow(screen)
        window.request_login.connect(self._on_request_login)
        if self._last_window_geometry is not None:
            window.setGeometry(self._last_window_geometry)
        elif not _is_wayland_session():
            window.resize(640, 480)
        window.show()
        self._window = window

    def _on_request_login(self) -> None:
        if self._window is not None:
            self._last_window_geometry = self._window.geometry()
            self._window.close()
            self._window = None
        self._show_login()


def main() -> int:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    controller = AppController(app)
    controller.start()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
