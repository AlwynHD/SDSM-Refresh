import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QMenuBar, QPushButton, QWidget,
    QFrame, QSplitter, QLabel, QStackedWidget, QAction, QSizePolicy, QMessageBox,
    QDialog, QTextBrowser
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QIcon, QScreen, QDesktopServices  # Added QDesktopServices import
from importlib import import_module

# Global variables for window dimensions
windowWidth = 1600
windowHeight = 1300

class SDSMWindow(QMainWindow):
    def __init__(self):
        """
        Initialize the main SDSM application window.
        Sets up the UI layout: title bar, sidebar menu, content area, settings, and help.
        """
        super().__init__()
        
        self.setWindowTitle("SDSM - Beta V1")
        self.resize(windowWidth, windowHeight)
        
        screen_geometry = QApplication.desktop().screenGeometry()
        screen_height = screen_geometry.height()
        
        # Central widget and main layout
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        mainLayout = QVBoxLayout()
        centralWidget.setLayout(mainLayout)
        
        # Splitter for menu and content
        menuContentSplitter = QSplitter(Qt.Horizontal)
        mainLayout.addWidget(menuContentSplitter)
        
        # Sidebar menu setup
        menuLayout = QVBoxLayout()
        menuLayout.setAlignment(Qt.AlignTop)
        menuLayout.setSpacing(0)
        menuLayout.setContentsMargins(0, 0, 0, 0)
        
        self.menuButtonNames = [
            "Home", "Quality Control", "Transform Data", "Screen Variables",
            "Calibrate Model", "Weather Generator", "Scenario Generator",
            "Summary Statistics", "Compare Results", "Frequency Analysis",
            "Time Series Analysis"
        ]
        self.menuButtonIcons = [
            "home.png", "arrow_down.png", "arrow_down.png", "arrow_down.png", "arrow_down.png",
            "arrow_down.png", "arrow_down.png", "arrow_down.png", "arrow_down.png", "arrow_down.png",
            "arrow_down.png"
        ]
        
        self.menuButtons = []
        self.button_height = int(screen_height * 0.03)
        self.button_font_size = int(self.button_height * 0.5)
        
        for index, (name, icon) in enumerate(zip(self.menuButtonNames, self.menuButtonIcons)):
            menuButton = QPushButton(name)
            
            menuButton.setIcon(QIcon(icon))
            menuButton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
            menuButton.setMinimumHeight(self.button_height)
            menuButton.setStyleSheet(
                f"text-align: left; padding-left: 10px; border: 1px solid lightgray; font-size: {self.button_font_size}px;"
            )
            menuButton.clicked.connect(lambda checked, idx=index: self.loadContent(idx))
            menuLayout.addWidget(menuButton)
            self.menuButtons.append(menuButton)
        
        # Menu Frame
        menuFrame = QFrame()
        menuFrame.setLayout(menuLayout)
        menuFrame.setFrameShape(QFrame.NoFrame)
        menuContentSplitter.addWidget(menuFrame)
        menuContentSplitter.setStretchFactor(0, 1)
        
        # Content area setup
        self.contentStack = QStackedWidget()
        self.contentStack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.contentStack.setMinimumSize(0, 0)
        menuContentSplitter.addWidget(self.contentStack)
        menuContentSplitter.setStretchFactor(1, 4)
        
        # Menu bar and toolbar
        toolbar = QMenuBar(self)
        self.setMenuBar(toolbar)
        settingsMenu = toolbar.addMenu("Settings")
        
        # --- Help Menu Setup ---
        self.helpMenu = toolbar.addMenu("Help")
        self.addHelpActions()  # Populate the Help menu with help actions
        
        # Links Menu
        linksMenu = toolbar.addMenu("Links")
        
        # Add links to Menu
        link1Action = QAction("Official Webpage", self)
        link1Action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl("https://www.sdsm.org.uk/")))
        linksMenu.addAction(link1Action)
        
        link2Action = QAction("SDSM Paper", self)
        link2Action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl("https://www.sciencedirect.com/science/article/abs/pii/S1364815201000603?via%3Dihub")))
        linksMenu.addAction(link2Action)
        
        link3Action = QAction("SDSM-DC Paper", self)
        link3Action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl("https://www.int-res.com/abstracts/cr/v61/n3/p259-276/")))
        linksMenu.addAction(link3Action)
        
        openSettingsAction = QAction("Open Data Settings", self)
        openSettingsAction.triggered.connect(self.loadDataSettingsContent)
        settingsMenu.addAction(openSettingsAction)
        
        openSettingsAction2 = QAction("Open System Settings", self)
        openSettingsAction2.triggered.connect(self.loadSystemSettingsContent)
        settingsMenu.addAction(openSettingsAction2)
        
        # Load initial content (Home screen)
        self.loadContent(0)
        
        # Center the window on the screen
        self.centerOnScreen()
    
    def loadContent(self, index, *args):
        """
        Load the content for the selected menu option.
        """
        
      
        for btn in self.menuButtons:
            btn.setStyleSheet(f"text-align: left; padding-left: 10px; background-color: #F0F0F0; border: 1px solid lightgray; font-size: {self.button_font_size}px;")
        self.menuButtons[index].setStyleSheet(f"text-align: left; padding-left: 10px; background-color: #B0B0B0; border: 1px solid lightgray; font-size: {self.button_font_size}px;")
        moduleName = self.menuButtonNames[index].lower().replace(" ", "_")
        displayName = self.menuButtonNames[index]
        self.loadModule(moduleName, displayName)
        self.updateHelpMenu(displayName)
    
    def loadDataSettingsContent(self):
        """
        Load the Data Settings module.
        """
        self.loadModule("data_settings", "Data Settings")
        self.updateHelpMenu("Data Settings")
    
    def loadSystemSettingsContent(self):
        """
        Load the System Settings module.
        """
        self.loadModule("system_settings", "System Settings")
        self.updateHelpMenu("System Settings")
    
    def loadModule(self, moduleName, displayName):
        """
        Dynamically load a module and display its screen.
        If the module is not found, display a fallback message.
        """
        modulePaths = {
            "home": os.path.dirname(__file__),
            "default": os.path.join(os.path.dirname(__file__), '..', 'modules')
        }
        modulePath = modulePaths.get(moduleName, modulePaths["default"])
        if modulePath not in sys.path:
            sys.path.append(modulePath)
        while self.contentStack.count() > 0:
            widget_to_remove = self.contentStack.widget(0)
            self.contentStack.removeWidget(widget_to_remove)
            widget_to_remove.deleteLater()
        try:
            module = import_module(moduleName)
            if hasattr(module, 'ContentWidget'):
                contentWidget = module.ContentWidget()
                contentWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                contentWidget.setMinimumSize(0, 0)
                self.contentStack.addWidget(contentWidget)
                self.contentStack.setCurrentWidget(contentWidget)
        except ModuleNotFoundError:
            fallbackLabel = QLabel(f"{displayName} screen not available. (Module missing or failed to load.)")
            fallbackLabel.setAlignment(Qt.AlignCenter)
            fallbackLabel.setStyleSheet("font-size: 24px;")
            fallbackWidget = QWidget()
            fallbackLayout = QVBoxLayout()
            fallbackLayout.addWidget(fallbackLabel)
            fallbackWidget.setLayout(fallbackLayout)
            self.contentStack.addWidget(fallbackWidget)
            self.contentStack.setCurrentWidget(fallbackWidget)
    
    def addHelpActions(self):
        """
        Populate the Help menu with a general help option and specific help actions.
        Uses the single HTML file 'SDSMHelp.html' (in the same folder as the code).
        """
        # Path to the single HTML help file
        help_file_path = os.path.abspath("src/core/SDSMHelp.html")
        
        # General Help Contents action (opens the whole page)
        helpContentsAction = QAction("Help Contents", self)
        helpContentsAction.triggered.connect(lambda: self.openHelpFile())
        self.helpMenu.addAction(helpContentsAction)
        
        # Mapping of page names to their anchor IDs within SDSMHelp.html
        self.help_urls = {
            "Quality Control": "IDH_Quality",
            "Transform Data": "IDH_Transform",
            "Screen Variables": "IDH_Screen",
            "Calibrate Model": "IDH_Calibrate",
            "Weather Generator": "IDH_WeatherG",
            "Scenario Generator": "IDH_Generate",
            "Summary Statistics": "IDH_SummaryStatistics",
            "Compare Results": "IDH_CompareResults",
            "Frequency Analysis": "IDH_FrequencyAnalysis",
            "Time Series Analysis": "IDH_TimeSeries",
            "Data Settings": "IDH_DataSettings",
            "System Settings": "IDH_SystemSettings"
        }
        self.help_actions = {}
        for name, section in self.help_urls.items():
            # Create an action for specific help topics
            action = QAction(f"{name} Help", self)
            # Use default argument binding in the lambda to capture section
            action.triggered.connect(lambda checked, section=section: self.openHelpFile(section))
            self.help_actions[name] = action
    
    def updateHelpMenu(self, page_name):
        """
        Update the Help menu to show the relevant help action for the current page.
        """
        self.helpMenu.clear()
        self.addHelpActions()
        if page_name in self.help_actions:
            self.helpMenu.addAction(self.help_actions[page_name])
    
    def openHelpFile(self, section=None):
        """
        Open the help viewer.
        If a section (anchor) is provided, jump to that part of SDSMHelp.html.
        Otherwise, load the entire help file.
        """
        help_file = os.path.abspath("src/core/SDSMHelp.html")
        url = QUrl.fromLocalFile(help_file)
        if section:
            # Set the fragment (anchor) for in-page navigation
            url.setFragment(section)
        try:
            helpDialog = QDialog(self)
            helpDialog.setWindowTitle("Help")
            helpDialog.resize(800, 600)
            layout = QVBoxLayout(helpDialog)
            textBrowser = QTextBrowser(helpDialog)
            layout.addWidget(textBrowser)
            textBrowser.setSource(url)
            helpDialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open help content: {str(e)}")
    
    def centerOnScreen(self):
        """
        Center the application window on the primary screen.
        """
        screenGeometry = QScreen.availableGeometry(QApplication.primaryScreen())
        screenCenter = screenGeometry.center()
        frameGeometry = self.frameGeometry()
        frameGeometry.moveCenter(screenCenter)
        self.move(frameGeometry.topLeft())
        
def run():
    # Create and launch the application
    app = QApplication(sys.argv)
    window = SDSMWindow()
    window.show()  # Display the main window
    sys.exit(app.exec_())  # Start the application event loop

if __name__ == "__main__":
    run()
