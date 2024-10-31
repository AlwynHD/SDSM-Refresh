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

        # Top button bar layout
        topBarLayout = QHBoxLayout()
        topBarLayout.setSpacing(0)
        topBarLayout.setContentsMargins(0, 0, 0, 0)
        topBarLayout.setAlignment(Qt.AlignLeft)

        # Placeholder buttons for top bar - These buttons are duplicatable based on page needs
        buttonNames = ["Reset", "Settings"] # Add name to list to create more buttons
        for name in buttonNames:
            button = QPushButton(name)  # Name buttons for clarity
            button.setIcon(QIcon("placeholder_icon.png"))  # Assuming placeholder icons are available
            button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            button.setFixedSize(50, 50)  # Set a fixed size matching the height of the Home button
            button.setStyleSheet("border: 1px solid lightgray; background-color: #F0F0F0; text-align: left;")  # Match color with sidebar buttons
            topBarLayout.addWidget(button)

        # Top bar frame to add layout
        topBarFrame = QFrame()
        topBarFrame.setLayout(topBarLayout)
        topBarFrame.setFrameShape(QFrame.NoFrame)
        topBarFrame.setFixedHeight(50)  # Match height with sidebar buttons (Home button)
        topBarFrame.setStyleSheet("background-color: #A9A9A9;")  # Dark Gray background for the top bar
        mainLayout.addWidget(topBarFrame)

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
        label = QLabel("Scenario Generator", self)
        contentLayout.addWidget(label)

        # Spacer to fill the rest of the layout
        contentLayout.addStretch()
