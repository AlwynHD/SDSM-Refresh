from PyQt5.QtWidgets import (QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QSizePolicy, 
                             QFrame, QLabel, QLineEdit, QFileDialog, QGroupBox, 
                             QGridLayout, QListWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class ContentWidget(QWidget):
    """
    A polished and modernized UI for the Weather Generator with an improved structure and user experience.
    """
    def __init__(self):
        super().__init__()

        # Main layout
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(30, 30, 30, 30)
        mainLayout.setSpacing(20)
        self.setLayout(mainLayout)

        # --- File Selection Section ---
        fileSelectionGroup = QGroupBox("File Selection")
        fileSelectionLayout = QGridLayout()

        self.parFileButton = QPushButton("📂 Select Parameter File")
        self.parFileButton.clicked.connect(self.selectPARFile)
        self.parFileText = QLabel("Not selected")

        self.outFileButton = QPushButton("💾 Save To File")
        self.outFileButton.clicked.connect(self.selectOutputFile)
        self.outFileText = QLabel("Not selected")

        fileSelectionLayout.addWidget(self.parFileButton, 0, 0)
        fileSelectionLayout.addWidget(self.parFileText, 0, 1)
        fileSelectionLayout.addWidget(self.outFileButton, 1, 0)
        fileSelectionLayout.addWidget(self.outFileText, 1, 1)

        fileSelectionGroup.setLayout(fileSelectionLayout)
        mainLayout.addWidget(fileSelectionGroup)

        # --- Predictor Information Section ---
        predInfoGroup = QGroupBox("Predictor Information")
        predInfoLayout = QGridLayout()

        self.noOfPredText = QLabel("📊 No. of predictors: 0")
        self.autoRegressLabel = QLabel("🔄 Autoregression: Unknown")
        self.processLabel = QLabel("⚙️ Process: Unknown")
        self.rStartText = QLabel("📅 Record Start: Unknown")
        self.rLengthText = QLabel("📏 Record Length: Unknown")

        self.viewPredictorsButton = QPushButton("👁️ View Predictors")
        self.viewPredictorsButton.clicked.connect(self.viewPredictors)
        
        predInfoLayout.addWidget(self.noOfPredText, 0, 0)
        predInfoLayout.addWidget(self.autoRegressLabel, 0, 1)
        predInfoLayout.addWidget(self.processLabel, 1, 0)
        predInfoLayout.addWidget(self.rStartText, 1, 1)
        predInfoLayout.addWidget(self.rLengthText, 2, 0)
        predInfoLayout.addWidget(self.viewPredictorsButton, 2, 1)

        predInfoGroup.setLayout(predInfoLayout)
        mainLayout.addWidget(predInfoGroup)

        # --- Predictors List Section ---
        predictorsGroup = QGroupBox("Predictors List")
        predictorsLayout = QVBoxLayout()
        
        self.predictorList = QListWidget()
        predictorsLayout.addWidget(self.predictorList)
        
        predictorsGroup.setLayout(predictorsLayout)
        mainLayout.addWidget(predictorsGroup)

        # --- Synthesis Parameters ---
        synthesisGroup = QGroupBox("Synthesis Parameters")
        synthesisLayout = QGridLayout()

        self.fStartText = QLineEdit()
        self.fStartText.setPlaceholderText("DD/MM/YYYY")
        self.fLengthText = QLineEdit()
        self.fLengthText.setPlaceholderText("Enter number of days")
        
        self.eSize = QLineEdit("20")
        self.eSize.setPlaceholderText("1-100")
        
        synthesisLayout.addWidget(QLabel("📅 Synthesis Start Date:"), 0, 0)
        synthesisLayout.addWidget(self.fStartText, 0, 1)
        synthesisLayout.addWidget(QLabel("📏 Synthesis Length:"), 0, 2)
        synthesisLayout.addWidget(self.fLengthText, 0, 3)
        synthesisLayout.addWidget(QLabel("📊 Ensemble Size:"), 1, 0)
        synthesisLayout.addWidget(self.eSize, 1, 1)

        synthesisGroup.setLayout(synthesisLayout)
        mainLayout.addWidget(synthesisGroup)

        # --- Progress Bar (hidden by default) ---
        self.progressPicture = QFrame()
        self.progressPicture.setFrameShape(QFrame.Box)
        self.progressPicture.setFixedHeight(30)
        self.progressPicture.setVisible(False)
        mainLayout.addWidget(self.progressPicture)

        # --- Buttons ---
        buttonLayout = QHBoxLayout()
        
        self.synthesizeButton = QPushButton("🚀 Synthesize Data")
        self.synthesizeButton.clicked.connect(self.synthesizeData)
        self.synthesizeButton.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        
        self.resetButton = QPushButton("🔄 Reset")
        self.resetButton.clicked.connect(self.reset_all)
        self.resetButton.setStyleSheet("background-color: #F44336; color: white; font-weight: bold;")
        
        buttonLayout.addWidget(self.synthesizeButton)
        buttonLayout.addWidget(self.resetButton)
        mainLayout.addLayout(buttonLayout)

    def selectPARFile(self):
        """Opens a file dialog to select a PAR file."""
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Parameter File", "", "PAR Files (*.PAR);;All Files (*.*)")
        if file_name:
            self.parFileText.setText(f"📂 {file_name}")
            # In a real application, you would parse the PAR file and update the UI fields

    def selectOutputFile(self):
        """Opens a file dialog to select an output file."""
        file_name, _ = QFileDialog.getSaveFileName(self, "Save To File", "", "OUT Files (*.OUT);;All Files (*.*)")
        if file_name:
            self.outFileText.setText(f"💾 {file_name}")
            
    def viewPredictors(self):
        """Loads and displays predictors from the PAR file."""
        # In a real application, this would read the PAR file and populate the predictorList
        if self.parFileText.text() != "Not selected":
            self.predictorList.clear()
            # Example items for demonstration
            self.predictorList.addItem("Predictand.DAT")
            self.predictorList.addItem("Predictor1.DAT")
            self.predictorList.addItem("Predictor2.DAT")
            
            # Update predictor info
            self.noOfPredText.setText("📊 No. of predictors: 2")
            self.autoRegressLabel.setText("🔄 Autoregression: False")
            self.processLabel.setText("⚙️ Processssss: Conditional")
            self.rStartText.setText("📅 Record Start: 01/01/1961")
            self.rLengthText.setText("📏 Record Length: 14610")
    
    def synthesizeData(self):
        """Handles the synthesis of weather data."""
        # Check input fields validity
        if self.parFileText.text() == "Not selected":
            # Show error message
            print("You must select a parameter file first.")
            return
        
        if self.outFileText.text() == "Not selected":
            # Show error message
            print("You must select a suitable output file to save to.")
            return
        
        # Show progress
        self.progressPicture.setVisible(True)
        
        # In a real application, this would process the data
        # For now, just simulate progress
        import time
        time.sleep(1)
        
        # Hide progress
        self.progressPicture.setVisible(False)
        print("Synthesis completed.")
    
    def reset_all(self):
        try:
            self.parFileText.setText("Not selected")
            self.outFileText.setText("Not selected")
            self.eSize.setText("20")
            self.predictorList.clear()
            self.noOfPredText.setText("📊 No. of predictors: 0")
            self.autoRegressLabel.setText("🔄 Autoregression: Unknown")
            self.processLabel.setText("⚙️ Process: Unknown")
            self.rStartText.setText("📅 Record Start: Unknown")
            self.rLengthText.setText("📏 Record Length: Unknown")
            self.fStartText.setText("")
            self.fLengthText.setText("")
        except OSError as e:
            if e.errno == 2:
                print("Error: default directory no good")
                raise
            else:
                print("Error Number: ", e.errno)
                raise