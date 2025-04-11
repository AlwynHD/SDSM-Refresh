from PyQt5.QtWidgets import (QApplication, QCheckBox, QPushButton, QComboBox, QFrame, QWidget, 
                             QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, QTableWidget, QTableWidgetItem, 
                             QRadioButton, QGroupBox, QSpinBox, QLineEdit, QDateEdit, QFileDialog)
from PyQt5.QtCore import Qt
import sys
from src.lib.FrequencyAnalysis.FATabular import *

moduleName = "Frequency Analysis"

class ContentWidget(QWidget):
    """
    A widget to display the Frequency Analysis screen (UI/UX).
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Frequency Analysis")
        self.setGeometry(100, 100, 800, 600)
        layout = QVBoxLayout()
        
        # --- Row 1: Observed Data & Modelled Data --- #
        dataLayout = QHBoxLayout()
        
        # Observed Data Group Box
        obsDataGroupBox = QGroupBox("Observed Data")
        obsDataGroupBox.setStyleSheet("color: black;")
        obsDataLayout = QVBoxLayout()
        self.obsDataButton = QPushButton("Select Observed Data 📂 ")
        self.obsDataLabel = QLabel("File: Not selected")
        self.obsDataButton.clicked.connect(self.selectObservedData)
        obsDataLayout.addWidget(self.obsDataButton)
        obsDataLayout.addWidget(self.obsDataLabel)
        obsDataGroupBox.setLayout(obsDataLayout)
        obsDataGroupBox.setFixedHeight(100)
        
        # Modelled Data Group Box
        modDataGroupBox = QGroupBox("Modelled Data")
        modDataGroupBox.setStyleSheet("color: black;")
        modDataLayout = QVBoxLayout()
        self.modDataButton = QPushButton("Select Modelled Data 📂 ")
        self.modDataLabel = QLabel("File: Not selected")
        self.modDataButton.clicked.connect(self.selectModelledData)
        modDataLayout.addWidget(self.modDataButton)
        modDataLayout.addWidget(self.modDataLabel)
        modDataGroupBox.setLayout(modDataLayout)
        modDataGroupBox.setFixedHeight(100)
        
        dataLayout.addWidget(obsDataGroupBox)
        dataLayout.addWidget(modDataGroupBox)
        layout.addLayout(dataLayout)
        
        # --- Row 2: Analysis Series & Frequency Analysis --- #
        analysisFreqLayout = QHBoxLayout()
        
        # Left Side: Analysis Series + Ensemble
        leftSideLayout = QVBoxLayout()
        
        # Analysis Series Group Box
        analysisGroupBox = QGroupBox("Analysis Series")
        analysisGroupBox.setStyleSheet("color: black;")
        analysisLayoutBox = QVBoxLayout()
        self.startDateLabel = QLabel("Analysis start date:")
        self.startDate = QDateEdit()
        self.endDateLabel = QLabel("Analysis end date:")
        self.endDate = QDateEdit()
        analysisLayoutBox.addWidget(self.startDateLabel)
        analysisLayoutBox.addWidget(self.startDate)
        analysisLayoutBox.addWidget(self.endDateLabel)
        analysisLayoutBox.addWidget(self.endDate)
        analysisGroupBox.setLayout(analysisLayoutBox)
        analysisGroupBox.setFixedHeight(200)
        
        # Ensemble Group Box
        ensembleGroupBox = QGroupBox("Ensemble")
        ensembleGroupBox.setStyleSheet("color: black;")
        ensembleLayout = QVBoxLayout()
        self.allMembersRadio = QRadioButton("All Members")
        self.ensembleMeanRadio = QRadioButton("Ensemble Mean")
        self.ensembleMemberRadio = QRadioButton("Ensemble Member:")
        self.ensembleMemberSpinBox = QSpinBox()
        self.ensembleMemberSpinBox.setValue(0)
        self.allMeanEnsembleRadio = QRadioButton("All + Mean Ensemble")
        self.allMembersRadio.setChecked(True)
        
        ensembleRow = QHBoxLayout()
        ensembleRow.addWidget(self.ensembleMemberRadio)
        ensembleRow.addWidget(self.ensembleMemberSpinBox)
        
        ensembleLayout.addWidget(self.allMembersRadio)
        ensembleLayout.addWidget(self.ensembleMeanRadio)
        ensembleLayout.addLayout(ensembleRow)
        ensembleLayout.addWidget(self.allMeanEnsembleRadio)
        
        ensembleGroupBox.setLayout(ensembleLayout)
        ensembleGroupBox.setFixedHeight(150)
        
        leftSideLayout.addWidget(analysisGroupBox)
        leftSideLayout.addWidget(ensembleGroupBox)
        
        # Frequency Analysis Group Box
        faGroupBox = QGroupBox("Frequency Analysis")
        faGroupBox.setStyleSheet("color: black;")
        faLayout = QVBoxLayout()
        self.confidenceLabel = QLabel("Confidence (%):")
        self.confidenceInput = QSpinBox()
        self.confidenceInput.setValue(5)
        faLayout.addWidget(self.confidenceLabel)
        faLayout.addWidget(self.confidenceInput)
        
        self.empiricalRadio = QRadioButton("Empirical")
        self.gevRadio = QRadioButton("GEV")
        self.gumbelRadio = QRadioButton("Gumbel")
        self.stretchedExpRadio = QRadioButton("Stretched Exponential")
        self.empiricalRadio.setChecked(True)
        faLayout.addWidget(self.empiricalRadio)
        faLayout.addWidget(self.gevRadio)
        faLayout.addWidget(self.gumbelRadio)
        faLayout.addWidget(self.stretchedExpRadio)
        
        self.thresholdLabel = QLabel("Threshold:")
        self.thresholdInput = QSpinBox()
        self.thresholdInput.setValue(10)
        faLayout.addWidget(self.thresholdLabel)
        faLayout.addWidget(self.thresholdInput)
        
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        faLayout.addWidget(separator)
        
        self.saveButton = QPushButton("Save Results To 💾")
        self.saveLabel = QLabel("File: Not selected")
        self.saveButton.clicked.connect(self.saveResults)
        faLayout.addWidget(self.saveButton)
        faLayout.addWidget(self.saveLabel)
        faGroupBox.setFixedHeight(350)
        faGroupBox.setLayout(faLayout)
        
        analysisFreqLayout.addLayout(leftSideLayout)
        analysisFreqLayout.addWidget(faGroupBox)
        layout.addLayout(analysisFreqLayout)
        
        # --- Extra Settings --- #
        extraSettingsLayout = QHBoxLayout()
        dataPeriodGroupBox = QGroupBox("Data Period")
        dataPeriodLayout = QVBoxLayout()
        self.dataPeriodCombo = QComboBox()
        self.dataPeriodCombo.addItems(["All Data", "January", "February", "March", "April", "May", "June", "July", "August", "Septemeber", "October", "November", "December", "Winter", "Autumn", "Summer", "Spring"])
        dataPeriodLayout.addWidget(self.dataPeriodCombo)
        dataPeriodGroupBox.setFixedHeight(100)
        dataPeriodGroupBox.setLayout(dataPeriodLayout)
        
        thresholdGroupBox = QGroupBox("Threshold")
        thresholdLayout = QVBoxLayout()
        self.applyThresholdCheckbox = QCheckBox("Apply threshold?")
        thresholdLayout.addWidget(self.applyThresholdCheckbox)
        thresholdGroupBox.setFixedHeight(100)
        thresholdGroupBox.setLayout(thresholdLayout)
        
        pdfGroupBox = QGroupBox("PDF Categories")
        pdfLayout = QVBoxLayout()
        self.pdfLabel = QLabel("No of PDF categories")
        self.pdfSpinBox = QSpinBox()
        self.pdfSpinBox.setValue(20)
        pdfLayout.addWidget(self.pdfLabel)
        pdfLayout.addWidget(self.pdfSpinBox)
        pdfGroupBox.setFixedHeight(100)
        pdfGroupBox.setLayout(pdfLayout)
        
        extraSettingsLayout.addWidget(dataPeriodGroupBox)
        extraSettingsLayout.addWidget(thresholdGroupBox)
        extraSettingsLayout.addWidget(pdfGroupBox)
        layout.addLayout(extraSettingsLayout)
        
        idfSettingsLayout = QHBoxLayout()
        idfGroupBox = QGroupBox("IDF Settings")
        idfLayout = QHBoxLayout()
        self.methodMomentsRadio = QRadioButton("Method of Moments")
        self.parameterPowerRadio = QRadioButton("Parameter Power Scaling")
        self.parameterLinearRadio = QRadioButton("Parameter Linear Scaling")
        self.methodMomentsRadio.setChecked(True)
        self.runningSumLabel = QLabel("Running Sum Length (Days):")
        self.runningSumInput = QSpinBox()
        self.runningSumInput.setValue(2)
        idfLayout.addWidget(self.methodMomentsRadio)
        idfLayout.addWidget(self.parameterPowerRadio)
        idfLayout.addWidget(self.parameterLinearRadio)
        idfLayout.addWidget(self.runningSumLabel)
        idfLayout.addWidget(self.runningSumInput)
        idfGroupBox.setLayout(idfLayout)
        idfSettingsLayout.addWidget(idfGroupBox)
        layout.addLayout(idfSettingsLayout)
        
        graphButtonsLayout = QHBoxLayout()
        self.qqPlotButton = QPushButton("Q-Q Plot")
        self.qqPlotButton.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.pdfPlotButton = QPushButton("PDF Plot")
        self.pdfPlotButton.setStyleSheet("background-color: #1FC7F5; color: white; font-weight: bold")
        self.linePlotButton = QPushButton("Line Plot")
        self.linePlotButton.setStyleSheet("background-color: #F57F0C; color: white; font-weight: bold")
        self.faGraphicalButton = QPushButton("FA Graphical")
        self.faGraphicalButton.setStyleSheet("background-color: #5adbb5; color: white; font-weight: bold;")
        
        graphButtonsLayout.addWidget(self.qqPlotButton)
        graphButtonsLayout.addWidget(self.pdfPlotButton)
        graphButtonsLayout.addWidget(self.linePlotButton)
        graphButtonsLayout.addWidget(self.faGraphicalButton)
        layout.addLayout(graphButtonsLayout)
        
        tabButtonsLayout = QHBoxLayout()
        self.faTabButton = QPushButton("FA Tabular")
        self.faTabButton.setStyleSheet("background-color: #ffbd03; color: white; font-weight: bold;")
        self.faTabButton.clicked.connect(self.faTabButtonClicked)
        self.idfPlotButton = QPushButton("IDF Plot")
        self.idfPlotButton.setStyleSheet("background-color: #dd7973; color: white; font-weight: bold")
        self.idfTabButton = QPushButton("IDF Tabular")
        self.idfTabButton.setStyleSheet("background-color: #4681f4; color: white; font-weight: bold")
        self.resetButton = QPushButton(" 🔄 Reset Values")
        self.resetButton.setStyleSheet("background-color: #ED0800; color: white; font-weight: bold;")
        
        tabButtonsLayout.addWidget(self.faTabButton)
        tabButtonsLayout.addWidget(self.idfPlotButton)
        tabButtonsLayout.addWidget(self.idfTabButton)
        tabButtonsLayout.addWidget(self.resetButton)
        layout.addLayout(tabButtonsLayout)
        
        self.setLayout(layout)
    
    def saveResults(self):
        fileName, _ = QFileDialog.getSaveFileName(self, "Save Results File")
        if fileName:
            self.saveLabel.setText(f"File: {fileName}")

    def selectObservedData(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Select Observed Data File")
        if fileName:
            self.obsDataFile = fileName
            self.obsDataLabel.setText(f"File: {fileName}")
    
    def selectModelledData(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Select Modelled Data File")
        if fileName:
            self.modDataFile = fileName
            self.modDataLabel.setText(f"File: {fileName}")
    
    def faTabButtonClicked(self):
        if not hasattr(self, "obsDataFile") or not hasattr(self, "modDataFile"):
            print("Please select both Observed and Modelled data files.")
            return

        fsDate = self.startDate.date().toPyDate()
        feDate = self.endDate.date().toPyDate()
        applyThresh = self.applyThresholdCheckbox.isChecked()
        threshValue = self.thresholdInput.value()
        dataPeriodChoice = self.dataPeriodCombo.currentText()

        if not self.empiricalRadio.isChecked():
            print("Please select the 'Empirical' option for this analysis.")
            return

        # Use the durations as given in the VB example
        durations = [1.0, 1.1, 1.2, 1.3, 1.5, 2.0, 2.5, 3.0, 3.5]

        tableDict = computeFATableFromFiles(
            observedFilePath=self.obsDataFile,
            modelledFilePath=self.modDataFile,
            fsDate=fsDate,
            feDate=feDate,
            dataPeriodChoice=dataPeriodChoice,
            applyThreshold=applyThresh,
            thresholdValue=threshValue,
            durations=durations,
            ensembleIndex=0
        )

        print("FA Tabular Results with 2.5%ile and 97.5%ile intervals:")
        printFATabularOutput(
            tableDict=tableDict,
            durations=durations,
            obsFileName=self.obsDataFile,
            modFileName=self.modDataFile,
            seasonText=dataPeriodChoice,
            fitType="Empirical"
        )
        # Optionally, load results into a QTableWidget for GUI display.

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ContentWidget()
    window.show()
    sys.exit(app.exec_())
