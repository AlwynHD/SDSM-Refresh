from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout

class Screen2(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        label = QLabel("This is Screen 2")
        layout.addWidget(label)

        self.setLayout(layout)
