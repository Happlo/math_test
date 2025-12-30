from __future__ import annotations

import sys
from PyQt6.QtWidgets import QApplication

from math_trainer_core import CoreApi, TrainerConfig
from app_qt.qt_window import MathWindow
from app_qt.start_dialog import StartDialog


def main() -> int:
    app = QApplication(sys.argv)

    modes = CoreApi.Modes()
    if not modes:
        return 2

    dlg = StartDialog(modes=modes, get_defaults=CoreApi.DefaultConfig)
    if dlg.exec() != dlg.DialogCode.Accepted:
        return 0

    choice = dlg.selection()

    question_state = CoreApi.Start(
        mode_id=choice.mode_id,
        config=TrainerConfig(num_questions=choice.num_questions),
        overrides=choice.overrides,
    )

    window = MathWindow(question_state)
    window.resize(420, 280)
    window.show()

    # window.render(core.start(TrainerConfig(num_questions=choice.num_questions)))
    #window.set_step(step)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
