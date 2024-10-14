import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QToolBar, QAction, 
    QToolButton, QMenu, QDockWidget, QPushButton, QSizePolicy
)
from PyQt5.QtCore import Qt
from Screens.screen1 import Screen1
from Screens.screen2 import Screen2
from Screens.screen3 import Screen3


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set the window title
        self.setWindowTitle("PyQt Main Window with Toolbar and Side Nav Bar")

        # Set the fixed size for the window
        self.setFixedSize(1600, 800)

        # Set the central widget
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        # Create a layout and add a placeholder label to it
        self.layout = QVBoxLayout()

        # Create a content widget where the screens will be loaded
        self.content_widget = QWidget(self)
        self.content_widget.setLayout(QVBoxLayout())  # Set layout for content_widget
        self.layout.addWidget(self.content_widget)

        # Set the layout to the central widget
        self.central_widget.setLayout(self.layout)

        # Set a status bar
        self.statusBar().showMessage("Status Bar Ready")

        # Create a toolbar
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        # Create tool buttons with a dropdown menu
        file_button = QToolButton(self)
        file_button.setText("File")
        file_button.setPopupMode(QToolButton.InstantPopup)
        file_button.setStyleSheet("QToolButton::menu-indicator { image: none; }")  # Remove arrow

        options_button = QToolButton(self)
        options_button.setText("Options")
        options_button.setPopupMode(QToolButton.InstantPopup)
        options_button.setStyleSheet("QToolButton::menu-indicator { image: none; }")  # Remove arrow

        help_button = QToolButton(self)
        help_button.setText("Help")
        help_button.setPopupMode(QToolButton.InstantPopup)
        help_button.setStyleSheet("QToolButton::menu-indicator { image: none; }")  # Remove arrow

        # Create menus and add actions to them
        file_menu = QMenu(file_button)
        options_menu = QMenu(options_button)
        help_menu = QMenu(help_button)

        # Add actions to the menu
        option1 = QAction("Option 1", self)
        option1.triggered.connect(self.on_option1_selected)
        file_menu.addAction(option1)

        option2 = QAction("Option 2", self)
        option2.triggered.connect(self.on_option2_selected)
        options_menu.addAction(option2)

        option3 = QAction("Option 3", self)
        option3.triggered.connect(self.on_option3_selected)
        help_menu.addAction(option3)

        file_button.setMenu(file_menu)
        options_button.setMenu(options_menu)
        help_button.setMenu(help_menu)

        # Add the buttons to the toolbar
        toolbar.addWidget(file_button)
        toolbar.addWidget(options_button)
        toolbar.addWidget(help_button)

        # Create a side navigation bar
        self.create_side_nav_bar()

        # Load the default screen initially
        self.current_screen = Screen1()
        self.load_screen(self.current_screen)

    def create_side_nav_bar(self):
        # Create a dock widget for the side nav bar
        dock_widget = QDockWidget(self)

        # Remove features (no closing, no floating, no resizing)
        dock_widget.setFeatures(QDockWidget.NoDockWidgetFeatures)

        # Remove title bar
        dock_widget.setTitleBarWidget(QWidget())  # Empty widget to hide the title bar

        # Create a QWidget for the side nav content
        nav_widget = QWidget()
        nav_layout = QVBoxLayout()

        # Set spacing to 0 to avoid large gaps between buttons
        nav_layout.setSpacing(0)

        # Add buttons to switch screens
        screen1_button = QPushButton("Screen 1", self)
        screen1_button.clicked.connect(lambda: self.switch_screen(Screen1()))

        screen2_button = QPushButton("Screen 2", self)
        screen2_button.clicked.connect(lambda: self.switch_screen(Screen2()))

        screen3_button = QPushButton("Screen 3", self)
        screen3_button.clicked.connect(lambda: self.switch_screen(Screen3()))

        # Make button heights dynamic based on the height of the navigation bar
        screen1_button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        screen2_button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        screen3_button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        screen1_button.setFixedWidth(200)
        screen2_button.setFixedWidth(200)
        screen3_button.setFixedWidth(200)

        # Add buttons to the layout
        nav_layout.addWidget(screen1_button)
        nav_layout.addWidget(screen2_button)
        nav_layout.addWidget(screen3_button)

        # Set layout and assign it to the nav_widget
        nav_widget.setLayout(nav_layout)

        # Add the widget to the dock
        dock_widget.setWidget(nav_widget)

        # Add the dock widget to the left side (non-resizable and non-closeable)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock_widget)

    def switch_screen(self, new_screen):
        # Clear the current content and load the new screen
        self.load_screen(new_screen)

    def load_screen(self, screen):
        # Clear the previous screen
        if self.content_widget.layout() is not None:  # Check if layout exists
            for i in reversed(range(self.content_widget.layout().count())):
                widget = self.content_widget.layout().itemAt(i).widget()
                if widget is not None:
                    widget.deleteLater()

        # Load the new screen
        self.content_widget.layout().addWidget(screen)  # Add the screen widget to the layout
        self.current_screen = screen

    def on_option1_selected(self):
        self.statusBar().showMessage("Option 1 selected!")

    def on_option2_selected(self):
        self.statusBar().showMessage("Option 2 selected!")

    def on_option3_selected(self):
        self.statusBar().showMessage("Option 3 selected!")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
