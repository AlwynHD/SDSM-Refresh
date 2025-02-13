from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QComboBox, 
    QLineEdit, QListWidget, QFileDialog, QCheckBox, QRadioButton, QButtonGroup, 
    QGridLayout, QGroupBox, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class ContentWidget(QWidget):
    """
    A well-optimized UI layout based on the user's feedback.
    """
    def __init__(self):
        super().__init__()

        # --- Main Layout ---
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(15, 15, 15, 15)  # Reduced margins to save space
        mainLayout.setSpacing(12)  # Adjusted spacing for better layout flow
        self.setLayout(mainLayout)

        # --- Time Period Selection (Smaller) ---
        timePeriodGroup = QGroupBox("Time Period")
        timePeriodLayout = QHBoxLayout()
        self.timePeriodDropdown = QComboBox()
        self.timePeriodDropdown.addItems(["Raw Data", "Processed Data"])
        self.timePeriodDropdown.setFixedHeight(25)  # Reduced height for better fit
        timePeriodLayout.addWidget(self.timePeriodDropdown, alignment=Qt.AlignCenter)
        timePeriodGroup.setLayout(timePeriodLayout)
        mainLayout.addWidget(timePeriodGroup, alignment=Qt.AlignCenter)

        # --- File Selection Section (Side-by-Side) ---
        fileSelectionLayout = QHBoxLayout()

        # Left File Selection (Reduced height)
        self.fileSelectionLeft = self.createFileSelectionGroup("File Selection")
        fileSelectionLayout.addWidget(self.fileSelectionLeft)

        # Right File Selection
        self.fileSelectionRight = self.createFileSelectionGroup("File Selection")
        fileSelectionLayout.addWidget(self.fileSelectionRight)

        mainLayout.addLayout(fileSelectionLayout)

        # --- Bottom Section (Data Range + Save Results) ---
        bottomLayout = QHBoxLayout()

        # Data Range Box (Smaller Height)
        dataGroup = QGroupBox("Data")
        dataLayout = QGridLayout()

        self.startDateInput = QLineEdit()
        self.startDateInput.setPlaceholderText("01/01/1948")
        self.startDateInput.setFixedHeight(25)

        self.endDateInput = QLineEdit()
        self.endDateInput.setPlaceholderText("31/12/2017")
        self.endDateInput.setFixedHeight(25)

        dataLayout.addWidget(QLabel("Start:"), 0, 0)
        dataLayout.addWidget(self.startDateInput, 0, 1)
        dataLayout.addWidget(QLabel("End:"), 1, 0)
        dataLayout.addWidget(self.endDateInput, 1, 1)

        dataGroup.setLayout(dataLayout)
        dataGroup.setFixedHeight(80)  # Reduced height to fit better
        bottomLayout.addWidget(dataGroup)

        # Save Results Box (Aligned with Data Section)
        saveGroup = QGroupBox("Save Results To")
        saveLayout = QVBoxLayout()

        saveButtonsLayout = QHBoxLayout()
        self.selectSaveButton = QPushButton("📂 Select")
        self.selectSaveButton.clicked.connect(self.selectSaveFile)
        self.selectSaveButton.setFixedHeight(30)

        self.clearSaveButton = QPushButton("❌ Clear")
        self.clearSaveButton.clicked.connect(self.clearSaveFile)
        self.clearSaveButton.setFixedHeight(30)

        saveButtonsLayout.addWidget(self.selectSaveButton)
        saveButtonsLayout.addWidget(self.clearSaveButton)

        self.saveFileLabel = QLabel("File: *.CSV")
        self.saveFileLabel.setStyleSheet("border: 1px solid gray; padding: 5px;")

        saveLayout.addLayout(saveButtonsLayout)
        saveLayout.addWidget(self.saveFileLabel)

        saveGroup.setLayout(saveLayout)
        bottomLayout.addWidget(saveGroup)

        mainLayout.addLayout(bottomLayout)

        # --- Statistics Selection (Better Organized) ---
        statsGroup = QGroupBox("Select Statistics")
        statsLayout = QGridLayout()

        self.statsOptions = [
            "Sum", "Mean", "Maximum", "Winter/Summer ratio",
            "Maximum dry spell", "Maximum wet spell",
            "Dry day persistence", "Wet day persistence",
            "Partial Duration Series", "Percentile",
            "Standard Precipitation Index", "Peaks Over Threshold"
        ]

        self.statCheckboxes = []
        for i, stat in enumerate(self.statsOptions):
            checkbox = QCheckBox(stat)
            self.statCheckboxes.append(checkbox)
            statsLayout.addWidget(checkbox, i // 2, i % 2)  # Two columns

        # --- Spell Duration Selection (Smaller to Fit) ---
        spellGroup = QGroupBox("Spell Duration Selection")
        spellLayout = QVBoxLayout()
        self.spellOptions = [
            "Mean dry spell", "Mean wet spell",
            "Median dry spell", "Median wet spell",
            "SD dry spell", "SD wet spell", "Spell length correlation"
        ]
        self.spellGroup = QButtonGroup()

        for option in self.spellOptions:
            radio = QRadioButton(option)
            self.spellGroup.addButton(radio)
            spellLayout.addWidget(radio)

        spellGroup.setLayout(spellLayout)
        spellGroup.setFixedHeight(150)  # Reduced height to fit better
        statsLayout.addWidget(spellGroup, 0, 2, len(self.spellOptions) // 2, 1)

        # --- Threshold Inputs (Now Fits Properly) ---
        thresholdLayout = QGridLayout()

        self.percentileInput = QLineEdit()
        self.percentileInput.setPlaceholderText("90")
        self.percentileInput.setFixedHeight(25)

        self.precipLongTermInput = QLineEdit()
        self.precipLongTermInput.setPlaceholderText("90")
        self.precipLongTermInput.setFixedHeight(25)

        self.numEventsInput = QLineEdit()
        self.numEventsInput.setPlaceholderText("90")
        self.numEventsInput.setFixedHeight(25)

        thresholdLayout.addWidget(QLabel("%Prec > annual %ile:"), 0, 0)
        thresholdLayout.addWidget(self.percentileInput, 0, 1)

        thresholdLayout.addWidget(QLabel("% All precip from events > long-term %ile:"), 1, 0)
        thresholdLayout.addWidget(self.precipLongTermInput, 1, 1)

        thresholdLayout.addWidget(QLabel("No. of events > long-term %ile:"), 2, 0)
        thresholdLayout.addWidget(self.numEventsInput, 2, 1)

        statsLayout.addLayout(thresholdLayout, 6, 0, 1, 2)
        statsGroup.setLayout(statsLayout)
        mainLayout.addWidget(statsGroup)

        # --- Action Buttons (Smaller & Aligned) ---
        buttonLayout = QHBoxLayout()
        generateButton = QPushButton("🚀 Generate")
        generateButton.setStyleSheet("background-color: #4CAF50; color: white; font-size: 14px; padding: 8px;")

        resetButton = QPushButton("🔄 Reset")
        resetButton.setStyleSheet("background-color: #F44336; color: white; font-size: 14px; padding: 8px;")

        buttonLayout.addWidget(generateButton)
        buttonLayout.addWidget(resetButton)
        mainLayout.addLayout(buttonLayout)

    def createFileSelectionGroup(self, title):
        group = QGroupBox(title)
        layout = QVBoxLayout()
        fileList = QListWidget()
        fileList.setFixedHeight(80)
        directoryBrowser = QListWidget()
        directoryBrowser.setFixedHeight(80)
        layout.addWidget(fileList)
        layout.addWidget(directoryBrowser)
        group.setLayout(layout)
        return group

    def selectSaveFile(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save To File", filter="CSV Files (*.csv)")
        if file_name:
            self.saveFileLabel.setText(f"File: {file_name}")

    def clearSaveFile(self):
        self.saveFileLabel.setText("File: *.CSV")
