import sys
import random
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt


NUM_QUESTIONS = 40

STREAK_EMOJIS = {
    1: "🌕",
    2: "🦜",
    3: "🌴",
    4: "🪐",
    5: "🐢",
    6: "😃",
    7: "🤓",
    8: "🤩",
    9: "😲",
    12: "🤯",
    30: "🥳🎈🎉🎊"
}

def get_streak_emoji(streak: int) -> str:
    emoji = ""
    for threshold in sorted(STREAK_EMOJIS.keys()):
        if streak >= threshold:
            emoji = STREAK_EMOJIS[threshold]
        else:
            break
    return emoji


class MathWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.score = 0
        self.streak = 0
        self.question_number = 0
        self.a = 0
        self.b = 0

        self.setWindowTitle("Matteträning")

        layout = QVBoxLayout()

        self.question_label = QLabel("")
        self.question_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.question_label.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
        layout.addWidget(self.question_label)

        self.answer_edit = QLineEdit()
        self.answer_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.answer_edit.setFont(QFont("Segoe UI", 28))
        self.answer_edit.returnPressed.connect(self.check_answer)
        layout.addWidget(self.answer_edit)

        self.feedback_label = QLabel("")
        self.feedback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.feedback_label.setFont(QFont("Segoe UI Emoji", 20))
        layout.addWidget(self.feedback_label)

        self.setLayout(layout)

        self.next_question()

    def next_question(self):
        if self.question_number >= NUM_QUESTIONS:
            self.question_label.setText(
                f"Klart! Du fick {self.score} av {NUM_QUESTIONS} rätt."
            )
            self.answer_edit.setDisabled(True)
            return

        self.question_number += 1

        self.a = random.randint(2, 18)
        self.b = random.randint(2, 20 - self.a)
        # self.a = random.randint(2, 7)
        # self.b = random.randint(1, self.a - 1)
        

        self.question_label.setText(f"Fråga {self.question_number}: \n {self.a} + {self.b} =")
        self.answer_edit.clear()
        self.answer_edit.setFocus()

    def check_answer(self):
        text = self.answer_edit.text()

        try:
            value = int(text)
        except ValueError:
            self.feedback_label.setText("Skriv en siffra! 🙃")
            return

        if value == self.a + self.b:
            self.score += 1
            self.streak += 1
            emoji = get_streak_emoji(self.streak)
            # inga färger sätts – bara ren text + emoji
            self.feedback_label.setText(f"Rätt! ⭐  Streak: {self.streak} {emoji}")
        else:
            self.feedback_label.setText(
                f"Fel ❌  {self.a} + {self.b} = {self.a + self.b}"
            )
            self.streak = 0

        self.next_question()


def main():
    app = QApplication(sys.argv)
    window = MathWindow()
    window.resize(400, 250)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
