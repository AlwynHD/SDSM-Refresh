from PyQt5.QtWidgets import QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QSizePolicy, QFrame, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor, QIcon

class ContentWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Main content layout
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the main layout
        mainLayout.setSpacing(0)  # Remove spacing between elements
        self.setLayout(mainLayout)

        # Gradient background for content area (rest of the container)
        contentFrame = QFrame()
        contentFrame.setFrameShape(QFrame.NoFrame)
        contentLayout = QVBoxLayout()
        contentLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the content layout
        contentLayout.setSpacing(0)  # Remove spacing between elements
        contentFrame.setLayout(contentLayout)

        # Set the background color to gray
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(211, 211, 211))  # Light Gray background
        contentFrame.setAutoFillBackground(True)
        contentFrame.setPalette(palette)

        # Add the content frame to the main layout
        mainLayout.addWidget(contentFrame)

        # Center label for content area (REMOVE LATER)
        label = QLabel("Settings", self)
        contentLayout.addWidget(label)

        # Spacer to fill the rest of the layout
        contentLayout.addStretch()
