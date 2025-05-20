from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPalette, QBrush

class ContentWidget(QWidget):
    """
    Home screen (UI/UX) for the application.
    Displays introductory information and dynamically adjusts the background image.
    """
    def __init__(self):
        """
        Initialize the Home screen UI/UX elements.
        """
        super().__init__()

        # Layout for arranging elements in the Home screen
        homeScreenLayout = QVBoxLayout()
        self.setLayout(homeScreenLayout)

        # Set the initial background image for the Home screen
        self.updateBackgroundImage()
        self.setAutoFillBackground(True)  # Enable auto-fill for the background

        # Label displaying application details near the top-center of the Home screen
        appDetails = (
            "Statistical DownScaling Model -\n"
            "Decision Centric\n"
            "SDSM-DC\n"
            "Version 7.0"
        )
        homeScreenLabel = QLabel(appDetails, self)
        homeScreenLabel.setAlignment(Qt.AlignCenter)            # center text within the label
        homeScreenLabel.setStyleSheet("font-size: 72px; color: black;")

        # Layout tweaks
        homeScreenLayout.setContentsMargins(0, 200, 0, 0)        # 50px padding at top
        homeScreenLayout.addWidget(homeScreenLabel, 
                                alignment=Qt.AlignHCenter)  # center the widget horizontally
        homeScreenLayout.addStretch(1)                          # push remaining space below

    def resizeEvent(self, event):
        """
        Handle the resize event to dynamically adjust the background image.
        Ensures the background scales properly as the window resizes.
        """
        self.updateBackgroundImage()  # Update the background image size
        super().resizeEvent(event)  # Call the parent class's resize event for standard handling

    def updateBackgroundImage(self):
        """
        Updates the background image to fit the current size of the Home screen widget.
        Ensures the image maintains its aspect ratio and smooth scaling for better quality.
        """
        backgroundImage = QPixmap("src/images/sdsm_home_background.jpg").scaled(
            self.size(),  # Scale the image to match the widget's size
            Qt.KeepAspectRatioByExpanding,  # Maintain aspect ratio while expanding to fill
            Qt.SmoothTransformation  # Use smooth scaling for high-quality rendering
        )
        palette = self.palette()  # Access the widget's current color palette
        palette.setBrush(QPalette.Window, QBrush(backgroundImage))  # Set the background image as a brush
        self.setPalette(palette)  # Apply the updated palette to the widget
