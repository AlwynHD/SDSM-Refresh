import sys
import subprocess
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QMenuBar, QPushButton, QWidget,
                             QFrame, QSplitter, QLabel, QStackedWidget, QAction, QSizePolicy,)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QScreen, QFont
from importlib import import_module
import os

# Global variables for window dimensions
windowWidth = 1280
windowHeight = 720


class SDSMWindow(QMainWindow):
    def __init__(self):
        """
        Initialize the main SDSM application window.
        Sets up the UI layout: titleBar, toolbar, menu, content, and other configurations.
        """
        super().__init__()
        
        # Configure main window properties
        self.setWindowTitle("SDSM - Beta V1")  # Title Bar

        self.resize(windowWidth, windowHeight)  # Set initial size
        
        screen_geometry = QApplication.desktop().screenGeometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        # Calculate the font size based on the screen size
        font_size = max(10, min(16, int(screen_height * 0.025))) 

        # Set up the central widget, which contains the menu (sidebar) and content (main display area)
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        mainLayout = QVBoxLayout()
        centralWidget.setLayout(mainLayout)

        # Create a splitter to separate the menu and content
        menuContentSplitter = QSplitter(Qt.Horizontal)
        mainLayout.addWidget(menuContentSplitter)

        # Menu setup
        menuLayout = QVBoxLayout()
        menuLayout.setAlignment(Qt.AlignTop)
        menuLayout.setSpacing(0)  # No spacing between buttons for compact design
        menuLayout.setContentsMargins(0, 0, 0, 0)  # Remove margins for a neat look

        # Define menu buttons with names and icons
        self.menuButtonNames = ["Home", "Quality Control", "Transform Data", "Screen Variables", "Calibrate Model", 
                                 "Weather Generator", "Scenario Generator", "Summary Statistics", "Compare Results", 
                                 "Frequency Analysis", "Time Series Analysis"]
        self.menuButtonIcons = ["home.png", "arrow_down.png", "arrow_down.png", "arrow_down.png", "arrow_down.png",
                                 "arrow_down.png", "arrow_down.png", "arrow_down.png", "arrow_down.png", "arrow_down.png", "arrow_down.png"]

        # Create menu buttons dynamically
        self.menuButtons = []
        # Calculate button height based on screen height (3% of screen height)
        button_height = int(screen_height * 0.03)
        # Calculate font size based on button height (40% of button height)
        button_font_size = int(button_height * 0.5)

        for index, (name, icon) in enumerate(zip(self.menuButtonNames, self.menuButtonIcons)):
            menuButton = QPushButton(name)
            menuButton.setIcon(QIcon(icon))
            menuButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
            menuButton.setMinimumHeight(button_height)  # Dynamic button height
            menuButton.setStyleSheet(f"text-align: left; padding-left: 10px; border: 1px solid lightgray; font-size: {button_font_size}px;")
            menuButton.clicked.connect(lambda checked, idx=index: self.loadContent(idx))
            menuLayout.addWidget(menuButton)
            self.menuButtons.append(menuButton)

        # Menu frame to hold the buttons
        menuFrame = QFrame()
        menuFrame.setLayout(menuLayout)
        menuFrame.setFrameShape(QFrame.NoFrame)  # No border around the menu
        menuContentSplitter.addWidget(menuFrame)
        menuFrame.setFixedWidth(int(windowWidth * 0.15))  # Menu width as 15% of window width

        # Content area setup
        self.contentStack = QStackedWidget()  # Content container to manage and display screens
        menuContentSplitter.addWidget(self.contentStack)

        # Load the initial content for "Home"
        self.loadContent(0)

        # Toolbar setup
        toolbar = QMenuBar(self)  # Toolbar
        self.setMenuBar(toolbar)
        settingsMenu = toolbar.addMenu("Settings")
        helpMenu = toolbar.addMenu("Help")
        literatureMenu = toolbar.addMenu("Literature")
        contactMenu = toolbar.addMenu("Contact")
        aboutMenu = toolbar.addMenu("About")

        # Add "Open Settings" action to the toolbar
        openSettingsAction = QAction("Open Settings", self)
        openSettingsAction.triggered.connect(self.loadSettingsContent)  # Connect to settings loader
        settingsMenu.addAction(openSettingsAction)

        # Center the window on the user's screen
        self.centerOnScreen()

    def loadContent(self, index):
        """
        Load the screen (UI/UX) for the selected menu option and initialize the associated module (functionality).

        Args:
            index (int): The index of the menu option clicked.
        """
        moduleName = self.menuButtonNames[index].lower().replace(" ", "_")  # Convert menu name to module name
        self.loadModule(moduleName, self.menuButtonNames[index])  # Load the module and its corresponding screen

    def loadSettingsContent(self):
        """
        Load the settings module into the content container.
        """
        self.loadModule("settings", "Settings")

    def loadModule(self, moduleName, displayName):
        """
        Dynamically load a module (backend functionality) and display its corresponding screen (UI/UX) in the content area.
        If the module is not found, display a fallback message.

        Args:
            moduleName (str): The name of the module to load (functionality).
            displayName (str): The display name of the module, used for fallback messages and user-facing references.
        """
        # Define paths to search for modules
        modulePaths = {
            "home": os.path.dirname(__file__),  # "Home" is in the main directory
            "default": os.path.join(os.path.dirname(__file__), '..', 'modules')  # Other modules in "modules" directory
        }
        
        # Determine the appropriate path for the module
        modulePath = modulePaths.get(moduleName, modulePaths["default"])
        
        # Add the selected path to the system path if not already included
        if modulePath not in sys.path:
            sys.path.append(modulePath)

        try:
            # Import the module dynamically
            module = import_module(moduleName)
            if hasattr(module, 'ContentWidget'):  # Check if the module has a "ContentWidget" class
                contentWidget = module.ContentWidget()  # Screen (UI/UX)
                self.contentStack.addWidget(contentWidget)  # Add widget to the content container
                self.contentStack.setCurrentWidget(contentWidget)  # Display the screen
        except ModuleNotFoundError:
            # Display fallback content if the module isn't found
            fallbackLabel = QLabel(f"{displayName} screen not available. (Module missing or failed to load.)")
            fallbackLabel.setAlignment(Qt.AlignCenter)  # Center the fallback text
            fallbackLabel.setStyleSheet("font-size: 24px;")  # Style the fallback text
            fallbackWidget = QWidget()
            fallbackLayout = QVBoxLayout()
            fallbackLayout.addWidget(fallbackLabel)
            fallbackWidget.setLayout(fallbackLayout)
            self.contentStack.addWidget(fallbackWidget)
            self.contentStack.setCurrentWidget(fallbackWidget)

    def centerOnScreen(self):
        """
        Center the application window on the user's primary screen.
        """
        screenGeometry = QScreen.availableGeometry(QApplication.primaryScreen())  # Get primary screen dimensions
        screenCenter = screenGeometry.center()  # Calculate the screen center
        frameGeometry = self.frameGeometry()  # Get current window geometry
        frameGeometry.moveCenter(screenCenter)  # Move the window's center to the screen center
        self.move(frameGeometry.topLeft())  # Adjust the window's top-left corner to reflect new position

def run():
    # Create and launch the application
    app = QApplication(sys.argv)
    window = SDSMWindow()
    window.show()  # Display the main window
    sys.exit(app.exec_())  # Start the application event loop

if __name__ == "__main__":
    run()
