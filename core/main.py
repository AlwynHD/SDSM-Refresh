import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QMenuBar, QPushButton, QWidget,
                             QFrame, QSplitter, QSizePolicy, QLabel, QStackedWidget)
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QScreen
from importlib import import_module

class SDSMWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SDSM")
        self.setGeometry(100, 100, 1280, 720)
        self.setFixedSize(1280, 720)  # Lock in the initial aspect ratio

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Create a QSplitter to divide sidebar and content (vertically split)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Sidebar (left)
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setAlignment(Qt.AlignTop)

        # Remove spacing between buttons and margins around the layout
        sidebar_layout.setSpacing(0)  # Remove spacing between buttons
        sidebar_layout.setContentsMargins(0, 0, 0, 0)

        self.button_names = ["Home", "Quality Control", "Transform Data", "Screen Variables", "Calibrate Model", "Weather Generator", "Scenario Generator", "Summary Statistics", "Compare Results", "Frequency Analysis", "Time Series Analysis"]
        self.button_icons = [
            "home.png", "arrow_down.png", "arrow_down.png", "arrow_down.png", "arrow_down.png",
            "arrow_down.png", "arrow_down.png", "arrow_down.png", "arrow_down.png", "arrow_down.png", "arrow_down.png"
        ]

        self.buttons = []
        for index, (name, icon) in enumerate(zip(self.button_names, self.button_icons)):
            button = QPushButton(name)  # Name buttons for clarity
            button.setIcon(QIcon(icon))  # Set icon for the button
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # Make button fill horizontally but fixed vertically
            button.setFixedHeight(50)  # Set fixed height for uniformity
            button.setStyleSheet("""
              QPushButton {
                  background-color: #3498db;
                  color: white;
              }
              QPushButton:hover {
                 background-color: #2980b9;
              }
           """)
# Align text left, add border between buttons, and remove whitespace
            button.clicked.connect(lambda checked, idx=index: self.load_content(idx))  # Connect each button to load content
            sidebar_layout.addWidget(button)
            self.buttons.append(button)

        sidebar_frame = QFrame()
        sidebar_frame.setLayout(sidebar_layout)
        sidebar_frame.setFrameShape(QFrame.NoFrame)

        # Add sidebar to splitter
        splitter.addWidget(sidebar_frame)
        sidebar_frame.setFixedWidth(200)  # Set fixed width for the sidebar

        # Content area (right) using QStackedWidget to load different pages
        self.content_stack = QStackedWidget()
        splitter.addWidget(self.content_stack)

        # Load initial content for Home
        self.load_content(0)

        # Menu bar
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)

        settings_menu = menu_bar.addMenu("Settings")
        help_menu = menu_bar.addMenu("Help")
        literature_menu = menu_bar.addMenu("Literature")
        contact_menu = menu_bar.addMenu("Contact")
        about_menu = menu_bar.addMenu("About")

        # Center the window on the screen
        self.center_on_screen()

    def load_content(self, index):
        module_name = self.button_names[index].lower().replace(" ", "_")
        try:
            # Dynamically import the content module
            module = import_module(module_name)
            if hasattr(module, 'ContentWidget'):
                content_widget = module.ContentWidget()
                self.content_stack.addWidget(content_widget)
                self.content_stack.setCurrentWidget(content_widget)
        except ModuleNotFoundError:
            # Display a simple fallback content if the module is not found
            fallback_label = QLabel(f"Content for {self.button_names[index]} not available.")
            fallback_label.setAlignment(Qt.AlignCenter)
            fallback_label.setStyleSheet("font-size: 24px;")
            fallback_widget = QWidget()
            fallback_layout = QVBoxLayout()
            fallback_layout.addWidget(fallback_label)
            fallback_widget.setLayout(fallback_layout)
            self.content_stack.addWidget(fallback_widget)
            self.content_stack.setCurrentWidget(fallback_widget)

    def resizeEvent(self, event):
        original_width = 1280
        original_height = 720

        # Calculate the scaling factor while maintaining the aspect ratio
        scale_factor_width = event.size().width() / original_width
        scale_factor_height = event.size().height() / original_height
        scale_factor = min(scale_factor_width, scale_factor_height)

        # Ensure the window maintains the correct aspect ratio
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)
        self.setFixedSize(new_width, new_height)

        # Adjust the font size and button size proportionally
        new_font_size = int(24 * scale_factor)
        for button in self.buttons:
            button.setFixedHeight(int(50 * scale_factor))
            button.setStyleSheet(f"text-align: left; padding-left: 10px; border: 1px solid lightgray; font-size: {new_font_size * 0.75}px;")

        super().resizeEvent(event)

    def center_on_screen(self):
        # Get the screen geometry
        screen_geometry = QScreen.availableGeometry(QApplication.primaryScreen())
        screen_center = screen_geometry.center()

        # Get the window geometry
        frame_geometry = self.frameGeometry()
        frame_geometry.moveCenter(screen_center)

        # Move the top-left point of the window to center it
        self.move(frame_geometry.topLeft())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SDSMWindow()
    window.show()  # Show the window in the center of the screen
    sys.exit(app.exec_())