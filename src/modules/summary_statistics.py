from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QRadioButton, QCheckBox, QSizePolicy, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class ContentWidget(QWidget):
    """
    Summary Statistics UI replicating the exact layout and functionality from the provided image.
    """
    def __init__(self):
        super().__init__()

        # --- Main Layout ---
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

        # Ensemble Size
        ensembleSizeLayout = QVBoxLayout()
        ensembleSizeLayout.setSpacing(5)
        ensembleSizeLabel = QLabel("Ensemble Size")
        ensembleMeanCheckbox = QCheckBox("Use Ensemble Mean?")
        ensembleMemberLabel = QLabel("Ensemble Member:")
        ensembleMemberInput = QLineEdit("0")
        ensembleSizeLayout.addWidget(ensembleSizeLabel)
        ensembleSizeLayout.addWidget(ensembleMeanCheckbox)
        ensembleSizeLayout.addWidget(ensembleMemberLabel)
        ensembleSizeLayout.addWidget(ensembleMemberInput)
        ensembleSizeFrame = QFrame()
        ensembleSizeFrame.setLayout(ensembleSizeLayout)
        rightPanelLayout.addWidget(ensembleSizeFrame)

        contentAreaLayout.addLayout(rightPanelLayout)
        mainLayout.addLayout(contentAreaLayout)

        # Auto-resizing setup
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
