from __future__ import annotations
import sys
import random
from PyQt6.QtWidgets import QApplication

from math_trainer_core.config import TrainerConfig
from math_trainer_core.core import MathTrainerCore
from math_trainer_core.plugin_loader import load_operator_plugins
from math_trainer_core.ports import IRandom

from .qt_window import MathWindow


class PythonRandom(IRandom):
    def randint(self, lo: int, hi: int) -> int:
        return random.randint(lo, hi)


def main() -> int:
    plugins = load_operator_plugins()

    config = TrainerConfig(
        num_questions=40,
        max_value=10,
        operator_plugin="plus",   # "minus"
        allow_negative=False,
    )

    operator = plugins[config.operator_plugin]
    rng = PythonRandom()
    core = MathTrainerCore(rng=rng, operator=operator)

    app = QApplication(sys.argv)
    window = MathWindow(core)
    window.resize(420, 280)
    window.show()

    window.render(core.start(config))
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
