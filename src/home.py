from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPalette, QBrush, QPainter

class ContentWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Content layout
        contentLayout = QVBoxLayout()
        self.setLayout(contentLayout)

        # Set background image for content area and fit to the page
        backgroundImage = QPixmap("sdsm_home_background.jpg").scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(backgroundImage))
        self.setAutoFillBackground(True)
        self.setPalette(palette)

        # Center label for content area
        label = QLabel("Statistical DownScaling Model -\nDecision Centric\nSDSM-DC\nVersion X.Y", self)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 24px; color: black;")
        contentLayout.addWidget(label)

    def resizeEvent(self, event):
        # Resize background image to fit the window
        backgroundImage = QPixmap("sdsm_home_background.jpg").scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(backgroundImage))
        self.setPalette(palette)
        super().resizeEvent(event)