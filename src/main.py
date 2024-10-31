import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QMenuBar, QPushButton, QWidget,
                             QFrame, QSplitter, QLabel, QStackedWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QScreen
from importlib import import_module

class SDSMWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SDSM Wireframe")
        self.setGeometry(100, 100, 900, 600)
        self.setFixedSize(900, 600)  # Set fixed window size, no resizing

        # Central widget
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)

        # Main layout
        mainLayout = QVBoxLayout()
        centralWidget.setLayout(mainLayout)

        # Create a QSplitter to divide sidebar and content (vertically split)
        splitter = QSplitter(Qt.Horizontal)
        mainLayout.addWidget(splitter)

        # Sidebar (left)
        sidebarLayout = QVBoxLayout()
        sidebarLayout.setAlignment(Qt.AlignTop)
        sidebarLayout.setSpacing(0)  # Remove spacing between buttons
        sidebarLayout.setContentsMargins(0, 0, 0, 0)

        self.buttonNames = ["Home", "Quality Control", "Transform Data", "Screen Variables", "Calibrate Model", 
                            "Weather Generator", "Scenario Generator", "Summary Statistics", "Compare Results", 
                            "Frequency Analysis", "Time Series Analysis"]
        self.buttonIcons = ["home.png", "arrow_down.png", "arrow_down.png", "arrow_down.png", "arrow_down.png",
                            "arrow_down.png", "arrow_down.png", "arrow_down.png", "arrow_down.png", "arrow_down.png", "arrow_down.png"]

        # Create fixed-size buttons
        self.buttons = []
        for index, (name, icon) in enumerate(zip(self.buttonNames, self.buttonIcons)):
            button = QPushButton(name)
            button.setIcon(QIcon(icon))
            button.setFixedSize(180, 50)  # Fixed button size for consistency
            button.setStyleSheet("text-align: left; padding-left: 10px; border: 1px solid lightgray;")
            button.clicked.connect(lambda checked, idx=index: self.loadContent(idx))
            sidebarLayout.addWidget(button)
            self.buttons.append(button)

        # Sidebar frame
        sidebarFrame = QFrame()
        sidebarFrame.setLayout(sidebarLayout)
        sidebarFrame.setFrameShape(QFrame.NoFrame)
        splitter.addWidget(sidebarFrame)
        sidebarFrame.setFixedWidth(200)

        # Content area
        self.contentStack = QStackedWidget()
        splitter.addWidget(self.contentStack)

        # Load initial content for Home
        self.loadContent(0)

        # Menu bar
        menuBar = QMenuBar(self)
        self.setMenuBar(menuBar)
        settingsMenu = menuBar.addMenu("Settings")
        helpMenu = menuBar.addMenu("Help")
        literatureMenu = menuBar.addMenu("Literature")
        contactMenu = menuBar.addMenu("Contact")
        aboutMenu = menuBar.addMenu("About")

        # Center the window on the screen
        self.centerOnScreen()

    def loadContent(self, index):
        moduleName = self.buttonNames[index].lower().replace(" ", "_")
        try:
            module = import_module(moduleName)
            if hasattr(module, 'ContentWidget'):
                contentWidget = module.ContentWidget()
                self.contentStack.addWidget(contentWidget)
                self.contentStack.setCurrentWidget(contentWidget)
        except ModuleNotFoundError:
            fallbackLabel = QLabel(f"Content for {self.buttonNames[index]} not available.")
            fallbackLabel.setAlignment(Qt.AlignCenter)
            fallbackLabel.setStyleSheet("font-size: 24px;")
            fallbackWidget = QWidget()
            fallbackLayout = QVBoxLayout()
            fallbackLayout.addWidget(fallbackLabel)
            fallbackWidget.setLayout(fallbackLayout)
            self.contentStack.addWidget(fallbackWidget)
            self.contentStack.setCurrentWidget(fallbackWidget)

    def centerOnScreen(self):
        screenGeometry = QScreen.availableGeometry(QApplication.primaryScreen())
        screenCenter = screenGeometry.center()
        frameGeometry = self.frameGeometry()
        frameGeometry.moveCenter(screenCenter)
        self.move(frameGeometry.topLeft())

if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_DisableHighDpiScaling, True)  # Disable scaling for consistent fixed size
    app = QApplication(sys.argv)
    window = SDSMWindow()
    window.show()
    sys.exit(app.exec_())
