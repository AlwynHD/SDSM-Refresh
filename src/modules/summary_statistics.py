from PyQt5.QtWidgets import QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QSizePolicy, QFrame, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor, QIcon

# Define the name of the module for display in the content area
moduleName = "Summary Statistics"

class ContentWidget(QWidget):
    """
    A widget to display the Summary Statistics screen (UI/UX).
    Includes a buttonBar at the top and a contentArea for displaying details.
    """
    def __init__(self):
        """
        Initialize the Summary Statistics screen UI/UX, setting up the layout, buttonBar, and contentArea.
        """
        super().__init__()

        # Main layout for the entire widget
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(10, 10, 10, 10)
        mainLayout.setSpacing(10)
        self.setLayout(mainLayout)

        # --- Toolbar ---
        toolbarLayout = QHBoxLayout()
        toolbarLayout.setSpacing(10)
        toolbarLayout.setContentsMargins(0, 0, 0, 0)

        for name in ["Reset", "Statistics", "Analyse", "Delta Stats", "Settings"]:
            button = QPushButton(name)
            button.setFixedSize(90, 40)
            toolbarLayout.addWidget(button)

        toolbarFrame = QFrame()
        toolbarFrame.setLayout(toolbarLayout)
        toolbarFrame.setStyleSheet("background-color: #A9A9A9;")
        mainLayout.addWidget(toolbarFrame)

        # --- Content Area Layout ---
        contentAreaLayout = QHBoxLayout()
        contentAreaLayout.setSpacing(20)

        # --- Left Panel ---
        leftPanelLayout = QVBoxLayout()
        leftPanelLayout.setSpacing(20)

        # Data Source
        dataSourceLabel = QLabel("Data Source")
        modelledButton = QRadioButton("Modelled")
        observedButton = QRadioButton("Observed")
        dataSourceLayout = QVBoxLayout()
        dataSourceLayout.addWidget(dataSourceLabel)
        dataSourceLayout.addWidget(modelledButton)
        dataSourceLayout.addWidget(observedButton)
        dataSourceFrame = QFrame()
        dataSourceFrame.setLayout(dataSourceLayout)
        leftPanelLayout.addWidget(dataSourceFrame)

        # Input File
        inputFileLayout = QVBoxLayout()
        inputFileLayout.setSpacing(5)
        inputFileLabel = QLabel("Select Input File")
        inputFileButton = QPushButton("Select File")
        fileStatusLabel = QLabel("File: Not selected")
        inputFileLayout.addWidget(inputFileLabel)
        inputFileLayout.addWidget(inputFileButton)
        inputFileLayout.addWidget(fileStatusLabel)
        inputFileFrame = QFrame()
        inputFileFrame.setLayout(inputFileLayout)
        leftPanelLayout.addWidget(inputFileFrame)

        # Output File
        outputFileLayout = QVBoxLayout()
        outputFileLayout.setSpacing(5)
        outputFileLabel = QLabel("Select Output File")
        saveStatisticsButton = QPushButton("Save Statistics To")
        outputStatusLabel = QLabel("File: Not selected")
        outputFileLayout.addWidget(outputFileLabel)
        outputFileLayout.addWidget(saveStatisticsButton)
        outputFileLayout.addWidget(outputStatusLabel)
        outputFileFrame = QFrame()
        outputFileFrame.setLayout(outputFileLayout)
        leftPanelLayout.addWidget(outputFileFrame)
 
        # Analysis Period
        analysisPeriodLayout = QVBoxLayout()
        analysisPeriodLayout.setSpacing(5)
        analysisPeriodLabel = QLabel("Analysis Period")
        startDateLabel = QLabel("Analysis start date:")
        startDateInput = QLineEdit("01/01/1948")
        endDateLabel = QLabel("Analysis end date:")
        endDateInput = QLineEdit("31/12/2017")
        analysisPeriodLayout.addWidget(analysisPeriodLabel)
        analysisPeriodLayout.addWidget(startDateLabel)
        analysisPeriodLayout.addWidget(startDateInput)
        analysisPeriodLayout.addWidget(endDateLabel)
        analysisPeriodLayout.addWidget(endDateInput)
        analysisPeriodFrame = QFrame()
        analysisPeriodFrame.setLayout(analysisPeriodLayout)
        leftPanelLayout.addWidget(analysisPeriodFrame)

        contentAreaLayout.addLayout(leftPanelLayout)

        # --- Right Panel ---
        rightPanelLayout = QVBoxLayout()
        rightPanelLayout.setSpacing(20)

        # Modelled Scenario
        modelledScenarioLayout = QVBoxLayout()
        modelledScenarioLayout.setSpacing(5)
        modelledScenarioLabel = QLabel("Modelled Scenario")
        modelDetailsLabel = QLabel("Model Details")
        modelDetails = [
            "Predictors: unknown", "Season code: unknown", "Year length: unknown",
            "Scenario start: unknown", "No. of days: unknown", "Ensemble size: unknown"
        ]
        modelDetailsWidgets = [QLabel(detail) for detail in modelDetails]
        viewDetailsButton = QPushButton("View Details")
        modelledScenarioLayout.addWidget(modelledScenarioLabel)
        modelledScenarioLayout.addWidget(modelDetailsLabel)
        for widget in modelDetailsWidgets:
            modelledScenarioLayout.addWidget(widget)
        modelledScenarioLayout.addWidget(viewDetailsButton)
        modelledScenarioFrame = QFrame()
        modelledScenarioFrame.setLayout(modelledScenarioLayout)
        rightPanelLayout.addWidget(modelledScenarioFrame)

        # --- Center Label (Placeholder) ---
        # Label to display the name of the module (Summary Statistics)
        moduleLabel = QLabel(moduleName, self)
        moduleLabel.setStyleSheet("font-size: 24px; color: black;")  # Style the label text
        contentAreaLayout.addWidget(moduleLabel)  # Add the label to the contentArea layout

        # Add a spacer to ensure content is properly spaced
        contentAreaLayout.addStretch()
