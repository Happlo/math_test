from __future__ import annotations

import sys
import random

from PyQt6.QtWidgets import QApplication

from math_trainer_core.plugin_loader import load_plugin_factories
from math_trainer_core.plugin_api import IRandom
from math_trainer_core.core import MathTrainerCore, TrainerConfig

from app_qt.qt_window import MathWindow
from app_qt.start_dialog import StartDialog


class PythonRandom(IRandom):
    def randint(self, lo: int, hi: int) -> int:
        return random.randint(lo, hi)


def main() -> int:
    plugins = load_plugin_factories()
    if not plugins:
        print("No plugins found.")
        return 2

    app = QApplication(sys.argv)

    dlg = StartDialog(plugins)
    if dlg.exec() != dlg.DialogCode.Accepted:
        return 0

    choice = dlg.selection()
    loaded = plugins[choice.plugin_id]

    plugin_instance = loaded.factory.CreatePlugin(choice.overrides)
    core = MathTrainerCore(rng=PythonRandom(), plugin=plugin_instance)

    window = MathWindow(core)
    window.resize(420, 280)
    window.show()

    window.render(core.start(TrainerConfig(num_questions=choice.num_questions)))
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
