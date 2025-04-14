from PyQt5.QtWidgets import (QApplication, QCheckBox, QPushButton, QComboBox, QFrame, QWidget, 
                             QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, QTableWidget, QTableWidgetItem, 
                             QRadioButton, QGroupBox, QSpinBox, QLineEdit, QDateEdit, QFileDialog)
from PyQt5.QtCore import Qt
import sys
from src.lib.FrequencyAnalysis import IDFTabular
from src.lib.FrequencyAnalysis.FATabular import *
import configparser
from PyQt5.QtCore import QDate
from datetime import datetime

def convert_value(key, value):
    """
    Convert the raw string value from the config into an appropriate Python type.
    """
    # Parse dates using their known format
    if key in ['globalsdate', 'globaledate']:
        return datetime.strptime(value, "%d/%m/%Y").date()
    # Convert numeric values
    elif key == 'yearindicator':
        return int(value)
    elif key in ['globalmissingcode']:
        # You might want these as int or float. Adjust if needed.
        try:
            return int(value)
        except ValueError:
            return float(value)
    elif key in ['thresh', 'fixedthreshold']:
        return float(value)
    elif key in ['varianceinflation', 'biascorrection']:
        # Assuming these values should be integers
        return int(value)
    # Convert booleans (case insensitive)
    elif key in ['allowneg', 'randomseed']:
        return value.lower() in ['true', '1', 'yes']
    # Convert comma-separated lists. Here we only expect this for 'months'
    elif key == "months":
        return [int(x.strip()) for x in value.split(',') if x.strip()]
    else:
        # If none of the above applies, return the raw string
        return value

# Read the settings file
config = configparser.ConfigParser()
config.read("src/lib/settings.ini")  # Adjust the path as needed

# Fetch and convert all settings from the 'Settings' section
settings = {}
for key, value in config["Settings"].items():
    settings[key] = convert_value(key, value)

    # Optionally, wrap all values in arrays (lists) if they aren't already
settingsAsArrays = {
    key: (val if isinstance(val, list) else [val])
    for key, val in settings.items()
}

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

        # Extract the first (and only) element from the array for both start and end dates
        py_start_date = settingsAsArrays["globalsdate"][0]
        py_end_date = settingsAsArrays["globaledate"][0]

        # Convert Python date objects to QDate objects
        q_start_date = QDate(py_start_date.year, py_start_date.month, py_start_date.day)
        q_end_date = QDate(py_end_date.year, py_end_date.month, py_end_date.day)

        # Set the QDate values into your QDate widgets
        self.startDate.setDate(q_start_date)
        self.endDate.setDate(q_end_date)


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
        self.idfTabButton.clicked.connect(self.idfTabButtonClicked)
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
        # Use the default directory from your configuration (assuming it's in settingsAsArrays)
        default_dir = settingsAsArrays["defaultdir"][0]
        fileName, _ = QFileDialog.getSaveFileName(self, "Save Results File", default_dir)
        if fileName:
            self.saveLabel.setText(f"File: {fileName}")

    def selectObservedData(self):
        # Use the default directory for open dialogs as well
        default_dir = settingsAsArrays["defaultdir"][0]
        fileName, _ = QFileDialog.getOpenFileName(self, "Select Observed Data File", default_dir)
        if fileName:
            self.obsDataFile = fileName
            self.obsDataLabel.setText(f"File: {fileName}")

    def selectModelledData(self):
        # Same default starting directory is used here
        default_dir = settingsAsArrays["defaultdir"][0]
        fileName, _ = QFileDialog.getOpenFileName(self, "Select Modelled Data File", default_dir)
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

    def idfTabButtonClicked(self):
        # --- Fetch UI inputs ---
        # Analysis start and end dates.
        startDateValue = self.startDate.date().toPyDate()
        endDateValue = self.endDate.date().toPyDate()
        numDays = (endDateValue - startDateValue).days + 1

        # Threshold from the UI.
        thresholdUI = self.thresholdInput.value()
        
        # Running Sum Length (in days) from the UI.
        runningSumLength = self.runningSumInput.value()
        
        # Determine the parameter estimation method.
        if self.methodMomentsRadio.isChecked():
            paramMethod = "Method of Moments"
        elif self.parameterPowerRadio.isChecked():
            paramMethod = "Parameter Power Scaling"
        elif self.parameterLinearRadio.isChecked():
            paramMethod = "Parameter Linear Scaling"
        else:
            paramMethod = "Method of Moments"
        
        # Determine the ensemble option.
        if self.allMembersRadio.isChecked():
            ensembleOption = "All Members"
        elif self.ensembleMeanRadio.isChecked():
            ensembleOption = "Ensemble Mean"
        elif self.ensembleMemberRadio.isChecked():
            ensembleOption = f"Ensemble Member: {self.ensembleMemberSpinBox.value()}"
        elif self.allMeanEnsembleRadio.isChecked():
            ensembleOption = "All + Mean Ensemble"
        else:
            ensembleOption = "Not selected"
        
        # Additional settings.
        dataPeriod = self.dataPeriodCombo.currentText()
        pdfCategories = self.pdfSpinBox.value()
        confidence = self.confidenceInput.value()
        
        # File information (the UI labels show the file name).
        observedFileUI = self.obsDataLabel.text()
        modelledFileUI = self.modDataLabel.text()
        
        # --- Print all UI inputs ---
        print("====== UI Inputs ======")
        print("Analysis Start Date       :", startDateValue)
        print("Analysis End Date         :", endDateValue)
        print("Number of Days in Period  :", numDays)
        print("Threshold (UI)            :", thresholdUI)
        print("Running Sum Length (Days) :", runningSumLength)
        print("Parameter Estimation Method:", paramMethod)
        print("Ensemble Option           :", ensembleOption)
        print("Data Period               :", dataPeriod)
        print("PDF Categories            :", pdfCategories)
        print("Confidence (%)            :", confidence)
        print("Observed Data File (UI)   :", observedFileUI)
        print("Modelled Data File (UI)   :", modelledFileUI)
        
        for key, value in settingsAsArrays.items():
            print(f"{key} ({type(value[0]).__name__}): {value}")




if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ContentWidget()
    window.show()
    sys.exit(app.exec_())
