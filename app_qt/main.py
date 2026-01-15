import sys

from PyQt6.QtWidgets import QApplication

from math_trainer_core.api import CoreApi
from app_qt.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)

    # Start in training select screen
    screen = CoreApi.Start()

    window = MainWindow(screen)
    window.resize(640, 480)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
