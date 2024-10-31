from PyQt5.QtWidgets import QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QSizePolicy, QFrame, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor, QIcon

class ContentWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Main content layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the main layout
        main_layout.setSpacing(0)  # Remove spacing between elements
        self.setLayout(main_layout)

        # Top button bar layout
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setSpacing(0)
        top_bar_layout.setContentsMargins(0, 0, 0, 0)
        top_bar_layout.setAlignment(Qt.AlignLeft)

        # Placeholder buttons for top bar - These buttons are duplicatable based on page needs
        button_names = ["Reset", "Settings"] # Add name to list to create more buttons
        for name in button_names:
            button = QPushButton(name)  # Name buttons for clarity
            button.setIcon(QIcon("placeholder_icon.png"))  # Assuming placeholder icons are available
            button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            button.setFixedSize(50, 50)  # Set a fixed size matching the height of the Home button
            button.setStyleSheet("border: 1px solid lightgray; background-color: #F0F0F0; text-align: left;")  # Match color with sidebar buttons
            top_bar_layout.addWidget(button)

        # Top bar frame to add layout
        top_bar_frame = QFrame()
        top_bar_frame.setLayout(top_bar_layout)
        top_bar_frame.setFrameShape(QFrame.NoFrame)
        top_bar_frame.setFixedHeight(50)  # Match height with sidebar buttons (Home button)
        top_bar_frame.setStyleSheet("background-color: #A9A9A9;")  # Dark Gray background for the top bar
        main_layout.addWidget(top_bar_frame)

        # Gradient background for content area (rest of the container)
        content_frame = QFrame()
        content_frame.setFrameShape(QFrame.NoFrame)
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the content layout
        content_layout.setSpacing(0)  # Remove spacing between elements
        content_frame.setLayout(content_layout)

        # Set the background color to gray
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(211, 211, 211))  # Light Gray background
        content_frame.setAutoFillBackground(True)
        content_frame.setPalette(palette)

        # Add the content frame to the main layout
        main_layout.addWidget(content_frame)

        # Center label for content area (REMOVE LATER)
        label = QLabel("Frequency Analysis", self)
        content_layout.addWidget(label)

        # Spacer to fill the rest of the layout
        content_layout.addStretch()
