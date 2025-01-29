from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSizePolicy, QFrame, QLabel, QFileDialog, QLineEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor, QIcon

# Define the name of the module for display in the content area
moduleName = "Weather Generator"

class ContentWidget(QWidget):
    """
    A widget to display the Weather Generator screen (UI/UX).
    Includes a buttonBar at the top and a contentArea for displaying details.
    """
    def __init__(self):
        """
        Initialize the Weather Generator screen UI/UX, setting up the layout, buttonBar, and contentArea.
        """
        super().__init__()

        # Main layout for the entire widget
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout
        mainLayout.setSpacing(0)  # No spacing between elements
        self.setLayout(mainLayout)  # Apply the main layout to the widget

        # --- Button Bar (Toolbar) ---
        buttonBarLayout = QHBoxLayout()
        buttonBarLayout.setSpacing(0)  
        buttonBarLayout.setContentsMargins(0, 0, 0, 0)  
        buttonBarLayout.setAlignment(Qt.AlignLeft)  

        buttonNames = ["Reset", "Settings"]  
        for name in buttonNames:
            button = QPushButton(name)  
            button.setIcon(QIcon("placeholder_icon.png"))  
            button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  
            button.setFixedSize(50, 50)  
            button.setStyleSheet(
                "border: 1px solid lightgray; background-color: #F0F0F0; text-align: left;"
            )  
            buttonBarLayout.addWidget(button)  

        buttonBarFrame = QFrame()
        buttonBarFrame.setLayout(buttonBarLayout)  
        buttonBarFrame.setFrameShape(QFrame.NoFrame)  
        buttonBarFrame.setFixedHeight(50)  
        buttonBarFrame.setStyleSheet("background-color: #A9A9A9;")  
        mainLayout.addWidget(buttonBarFrame)  

        # --- Content Area ---
        contentAreaFrame = QFrame()
        contentAreaFrame.setFrameShape(QFrame.NoFrame)  

        contentAreaLayout = QVBoxLayout()
        contentAreaLayout.setContentsMargins(20, 20, 20, 20)  
        contentAreaLayout.setSpacing(10)  
        contentAreaFrame.setLayout(contentAreaLayout)  

        contentAreaFrame.setStyleSheet("background-color: #D3D3D3;")
        mainLayout.addWidget(contentAreaFrame)  

        # --- Input File Selection ---
        self.inputFileButton = QPushButton("Select Input File")
        self.inputFileButton.clicked.connect(self.selectInputFile)
        self.inputFileLabel = QLabel("File: Not selected")

        contentAreaLayout.addWidget(self.inputFileButton)
        contentAreaLayout.addWidget(self.inputFileLabel)

        # --- Select Predictor Directory ---
        self.predictorDirButton = QPushButton("Select Predictor Directory")
        contentAreaLayout.addWidget(self.predictorDirButton)

        # --- Predictor Information ---
        self.numPredictorsLabel = QLabel("No. of predictors: 0")
        self.autoRegressionLabel = QLabel("Autoregression: Unknown")
        self.processLabel = QLabel("Process: Unknown")
        self.recordStartLabel = QLabel("Record Start: Unknown")
        self.recordLengthLabel = QLabel("Record Length: Unknown")

        contentAreaLayout.addWidget(self.numPredictorsLabel)
        contentAreaLayout.addWidget(self.autoRegressionLabel)
        contentAreaLayout.addWidget(self.processLabel)
        contentAreaLayout.addWidget(self.recordStartLabel)
        contentAreaLayout.addWidget(self.recordLengthLabel)

        # --- Synthesis Section ---
        self.synthesisStartLabel = QLabel("Synthesis Start:")
        self.synthesisStartInput = QLineEdit()
        self.synthesisLengthLabel = QLabel("Synthesis Length:")
        self.synthesisLengthInput = QLineEdit()

        contentAreaLayout.addWidget(self.synthesisStartLabel)
        contentAreaLayout.addWidget(self.synthesisStartInput)
        contentAreaLayout.addWidget(self.synthesisLengthLabel)
        contentAreaLayout.addWidget(self.synthesisLengthInput)

        # --- Output File Selection ---
        self.outputFileButton = QPushButton("Select Output File")
        self.outputFileButton.clicked.connect(self.selectOutputFile)
        self.outputFileLabel = QLabel("File: Not selected")

        contentAreaLayout.addWidget(self.outputFileButton)
        contentAreaLayout.addWidget(self.outputFileLabel)

        # --- Control Buttons ---
        controlLayout = QHBoxLayout()
        self.runButton = QPushButton("Run Simulation")
        self.cancelButton = QPushButton("Cancel")
        controlLayout.addWidget(self.runButton)
        controlLayout.addWidget(self.cancelButton)
        contentAreaLayout.addLayout(controlLayout)

        # --- Auto Resize ---
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def selectInputFile(self):
        """
        Opens a file dialog to select an input file and updates the label.
        """
        filePath, _ = QFileDialog.getOpenFileName(self, "Select Input File", "", "All Files (*)")
        if filePath:
            self.inputFileLabel.setText(f"File: {filePath}")

    def selectOutputFile(self):
        """
        Opens a file dialog to select an output file and updates the label.
        """
        filePath, _ = QFileDialog.getSaveFileName(self, "Select Output File", "", "All Files (*)")
        if filePath:
            self.outputFileLabel.setText(f"File: {filePath}")
