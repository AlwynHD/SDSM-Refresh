from PyQt5.QtWidgets import (QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QSizePolicy, 
                             QFrame, QLabel, QLineEdit, QComboBox, QGridLayout, 
                             QCheckBox, QRadioButton, QButtonGroup, QFileDialog, QGroupBox, 
                             QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class ContentWidget(QWidget):
    """
    A polished and modernized UI for the Scenario Generator with an improved structure and user experience.
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
        fileSelectionLayout = QHBoxLayout()

        self.inputFileButton = QPushButton("📂 Select Input File")
        self.inputFileButton.clicked.connect(self.selectInputFile)
        self.inputFileLabel = QLabel("No file selected")

        self.outputFileButton = QPushButton("💾 Save To File")
        self.outputFileButton.clicked.connect(self.selectOutputFile)
        self.outputFileLabel = QLabel("No file selected")

        fileSelectionLayout.addWidget(self.inputFileButton)
        fileSelectionLayout.addWidget(self.inputFileLabel)
        fileSelectionLayout.addStretch()
        fileSelectionLayout.addWidget(self.outputFileButton)
        fileSelectionLayout.addWidget(self.outputFileLabel)

        fileSelectionGroup.setLayout(fileSelectionLayout)
        mainLayout.addWidget(fileSelectionGroup)

        # --- General Parameters ---
        generalParamsGroup = QGroupBox("General Parameters")
        generalParamsLayout = QGridLayout()

        self.startDateInput = QLineEdit()
        self.startDateInput.setPlaceholderText("DD/MM/YYYY")
        self.ensembleSizeInput = QLineEdit()
        self.ensembleSizeInput.setPlaceholderText("Enter a number")

        self.conditionalProcessCheck = QCheckBox("Enable Conditional Processing?")
        self.eventThresholdInput = QLineEdit()
        self.eventThresholdInput.setPlaceholderText("Threshold Value")

        generalParamsLayout.addWidget(QLabel("📅 File Start Date:"), 0, 0)
        generalParamsLayout.addWidget(self.startDateInput, 0, 1)
        generalParamsLayout.addWidget(QLabel("📊 Ensemble Size:"), 0, 2)
        generalParamsLayout.addWidget(self.ensembleSizeInput, 0, 3)
        generalParamsLayout.addWidget(self.conditionalProcessCheck, 1, 0, 1, 2)
        generalParamsLayout.addWidget(QLabel("🔢 Event Threshold:"), 1, 2)
        generalParamsLayout.addWidget(self.eventThresholdInput, 1, 3)

        generalParamsGroup.setLayout(generalParamsLayout)
        mainLayout.addWidget(generalParamsGroup)

        # --- Treatments Section ---
        treatmentsGroup = QGroupBox("Treatment Parameters")
        treatmentsLayout = QGridLayout()

        # Occurrence
        self.occurrenceCheck = QCheckBox("⚡ Occurrence")
        self.frequencyChangeInput = QLineEdit()
        self.frequencyChangeInput.setPlaceholderText("0 %")
        self.stochasticRadio = QRadioButton("Stochastic")
        self.forcedRadio = QRadioButton("Forced")
        self.preserveTotalCheck = QCheckBox("Preserve Total?")
        occurrenceButtonGroup = QButtonGroup()
        occurrenceButtonGroup.addButton(self.stochasticRadio)
        occurrenceButtonGroup.addButton(self.forcedRadio)

        treatmentsLayout.addWidget(self.occurrenceCheck, 0, 0)
        treatmentsLayout.addWidget(QLabel("Frequency change:"), 0, 1)
        treatmentsLayout.addWidget(self.frequencyChangeInput, 0, 2)
        treatmentsLayout.addWidget(self.stochasticRadio, 0, 3)
        treatmentsLayout.addWidget(self.forcedRadio, 0, 4)
        treatmentsLayout.addWidget(self.preserveTotalCheck, 0, 5)

        # Variance
        self.varianceCheck = QCheckBox("📈 Variance")
        self.varianceFactorInput = QLineEdit()
        self.varianceFactorInput.setPlaceholderText("0 %")
        treatmentsLayout.addWidget(self.varianceCheck, 1, 0)
        treatmentsLayout.addWidget(QLabel("Factor:"), 1, 1)
        treatmentsLayout.addWidget(self.varianceFactorInput, 1, 2)

        # Mean
        self.meanCheck = QCheckBox("📊 Mean")
        self.meanFactorInput = QLineEdit()
        self.meanFactorInput.setPlaceholderText("0 %")
        self.meanAdditionInput = QLineEdit()
        self.meanAdditionInput.setPlaceholderText("0")
        treatmentsLayout.addWidget(self.meanCheck, 2, 0)
        treatmentsLayout.addWidget(QLabel("Factor:"), 2, 1)
        treatmentsLayout.addWidget(self.meanFactorInput, 2, 2)
        treatmentsLayout.addWidget(QLabel("Addition:"), 2, 3)
        treatmentsLayout.addWidget(self.meanAdditionInput, 2, 4)

        # Trend
        self.trendCheck = QCheckBox("📉 Trend")
        self.linearInput = QLineEdit()
        self.linearInput.setPlaceholderText("0 /year")
        self.exponentialInput = QLineEdit()
        self.exponentialInput.setPlaceholderText("1")
        self.logisticInput = QLineEdit()
        self.logisticInput.setPlaceholderText("1")
        treatmentsLayout.addWidget(self.trendCheck, 3, 0)
        treatmentsLayout.addWidget(QLabel("Linear:"), 3, 1)
        treatmentsLayout.addWidget(self.linearInput, 3, 2)
        treatmentsLayout.addWidget(QLabel("Exponential:"), 3, 3)
        treatmentsLayout.addWidget(self.exponentialInput, 3, 4)
        treatmentsLayout.addWidget(QLabel("Logistic:"), 3, 5)
        treatmentsLayout.addWidget(self.logisticInput, 3, 6)

        treatmentsGroup.setLayout(treatmentsLayout)
        mainLayout.addWidget(treatmentsGroup)

        # --- Buttons ---
        buttonLayout = QHBoxLayout()
        generateButton = QPushButton("🚀 Generate")
        generateButton.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        resetButton = QPushButton("🔄 Reset")
        resetButton.setStyleSheet("background-color: #F44336; color: white; font-weight: bold;")
        buttonLayout.addWidget(generateButton)
        buttonLayout.addWidget(resetButton)
        mainLayout.addLayout(buttonLayout)

    def selectInputFile(self):
        """
        Opens a file dialog to select an input file.
        """
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Input File")
        if file_name:
            self.inputFileLabel.setText(f"📂 {file_name}")

    def selectOutputFile(self):
        """
        Opens a file dialog to select an output file.
        """
        file_name, _ = QFileDialog.getSaveFileName(self, "Save To File")
        if file_name:
            self.outputFileLabel.setText(f"💾 {file_name}")
