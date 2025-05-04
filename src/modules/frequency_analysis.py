from PyQt5.QtWidgets import (QApplication, QCheckBox, QPushButton, QComboBox, QFrame, QWidget, 
                             QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, QTableWidget, QTableWidgetItem, 
                             QRadioButton, QGroupBox, QSpinBox, QLineEdit, QDateEdit, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics
import sys
from src.lib.FrequencyAnalysis.PDF import pdfPlot
from src.lib.FrequencyAnalysis.Line import linePlot
from src.lib.FrequencyAnalysis.QQ import qqPlot
from src.lib.FrequencyAnalysis.IDF import run_idf
from src.lib.FrequencyAnalysis.FA import frequency_analysis
import configparser
from PyQt5.QtCore import QDate
from datetime import datetime

def convert_value(key, value):
    """
    Convert a raw string value from the configuration file into an appropriate Python type.

    The conversion is determined by the key:
      - globalsdate, globaledate: Parse the date string (expected format "DD/MM/YYYY")
                                  and return a date object.
      - yearindicator: Converts the value to an integer.
      - globalmissingcode: Converts to int (or to float if int conversion fails).
      - thresh, fixedthreshold: Converts the value to a float.
      - varianceinflation, biascorrection: Converts the value to an int.
      - allowneg, randomseed: Converts the value to a boolean (interprets the value
                              as True if it case-insensitively matches 'true', '1', or 'yes').
      - months: Converts a comma-separated string into a list of integers.
      - All other keys: Returns the value as the raw string.

    Example expected keys and default values:
      - yearindicator (int):         [366]
      - globalsdate (date):          [datetime.date(1948, 1, 1)]
      - globaledate (date):          [datetime.date(2015, 12, 31)]
      - allowneg (bool):             [False]
      - randomseed (bool):           [True]
      - thresh (float):              [5.0]
      - globalmissingcode (int):     [-999]
      - defaultdir (str):            ['src/lib/data']
      - varianceinflation (int):     [12]
      - biascorrection (int):        [1]
      - fixedthreshold (float):      [0.5]
      - modeltransformation (str):   ['Natural log']
      - optimizationalgorithm (str): ['Dual Simplex']
      - criteriatype (str):          ['AIC Criteria']
      - stepwiseregression (str):    ['True']
      - conditionalselection (str):  ['Fixed Threshold']
      - months (list[int]):          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    Args:
        key (str): The configuration key.
        value (str): The raw string value from the configuration file.

    Returns:
        The converted value in the appropriate Python type.
    """
    if key in ['globalsdate', 'globaledate']:
        return datetime.strptime(value, "%d/%m/%Y").date()
    elif key == 'yearindicator':
        return int(value)
    elif key in ['globalmissingcode']:
        try:
            return int(value)
        except ValueError:
            return float(value)
    elif key in ['thresh', 'fixedthreshold']:
        return float(value)
    elif key in ['varianceinflation', 'biascorrection']:
        return int(value)
    elif key in ['allowneg', 'randomseed']:
        return value.lower() in ['true', '1', 'yes']
    elif key == "months":
        return [int(x.strip()) for x in value.split(',') if x.strip()]
    else:
        return value

def load_settings(config_path="src/lib/settings.ini"):
    """
    Load and convert settings from the configuration file.

    This function reads the 'Settings' section from the specified .ini file,
    converts each value using the `convert_value` function, and then ensures that
    each setting's value is wrapped in a list (if it is not already one) to maintain
    a uniform data structure for further processing.

    Args:
        config_path (str): The file path to the configuration file.

    Returns:
        tuple: A tuple containing two dictionaries:
            - settings: A dictionary with the settings converted to their appropriate types.
            - settingsAsArrays: A dictionary with each setting's value ensured to be a list.
    """
    config = configparser.ConfigParser()
    with open(config_path, 'r') as f:
        config.read_file(f)

    # Fetch and convert all settings from the 'Settings' section.
    settings = {}
    for key, value in config["Settings"].items():
        settings[key] = convert_value(key, value)

    # Wrap all values in arrays (lists) if they aren't already.
    settingsAsArrays = {
        key: (val if isinstance(val, list) else [val])
        for key, val in settings.items()
    }

    return settings, settingsAsArrays

# Integrate the settings into your existing code without changing variable names.
settings, settingsAsArrays = load_settings()

globalSDate = settings["globalsdate"]

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
        self.qqPlotButton.clicked.connect(self.qqPlotButtonClicked)
        self.pdfPlotButton = QPushButton("PDF Plot")
        self.pdfPlotButton.setStyleSheet("background-color: #1FC7F5; color: white; font-weight: bold")
        self.pdfPlotButton.clicked.connect(self.pdfPlotButtonClicked)
        self.linePlotButton = QPushButton("Line Plot")
        self.linePlotButton.setStyleSheet("background-color: #F57F0C; color: white; font-weight: bold")
        self.linePlotButton.clicked.connect(self.linePlotButtonClicked)
        self.faGraphicalButton = QPushButton("FA Graphical")
        self.faGraphicalButton.setStyleSheet("background-color: #5adbb5; color: white; font-weight: bold;")
        self.faGraphicalButton.clicked.connect(lambda: self.faButtonClicked("Graphical"))
        
        graphButtonsLayout.addWidget(self.qqPlotButton)
        graphButtonsLayout.addWidget(self.pdfPlotButton)
        graphButtonsLayout.addWidget(self.linePlotButton)
        graphButtonsLayout.addWidget(self.faGraphicalButton)
        layout.addLayout(graphButtonsLayout)
        
        tabButtonsLayout = QHBoxLayout()
        self.faTabButton = QPushButton("FA Tabular")
        self.faTabButton.setStyleSheet("background-color: #ffbd03; color: white; font-weight: bold;")
        self.faTabButton.clicked.connect(lambda: self.faButtonClicked("Tabular"))
        self.idfPlotButton = QPushButton("IDF Plot")
        self.idfPlotButton.setStyleSheet("background-color: #dd7973; color: white; font-weight: bold")
        #self.idfPlotButton.clicked.connect(lambda: self.run_idf_analysis("Graphical"))
        self.idfTabButton = QPushButton("IDF Tabular")
        #self.idfTabButton.clicked.connect(lambda: self.run_idf_analysis("Tabular"))
        self.idfTabButton.setStyleSheet("background-color: #4681f4; color: white; font-weight: bold")
        self.resetButton = QPushButton(" 🔄 Reset Values")
        self.resetButton.setStyleSheet("background-color: #ED0800; color: white; font-weight: bold;")
        self.resetButton.clicked.connect(self.resetValues)
        
        tabButtonsLayout.addWidget(self.faTabButton)
        tabButtonsLayout.addWidget(self.idfPlotButton)
        tabButtonsLayout.addWidget(self.idfTabButton)
        tabButtonsLayout.addWidget(self.resetButton)
        layout.addLayout(tabButtonsLayout)
        
        self.setLayout(layout)

    def showEvent(self, event):
        global globalSDate 
        settings, settingsAsArrays = load_settings()
        globalSDate = settings["globalsdate"]

        # Extract the first (and only) element from the array for both start and end dates
        py_start_date = settingsAsArrays["globalsdate"][0]
        py_end_date = settingsAsArrays["globaledate"][0]

        # Convert Python date objects to QDate objects
        q_start_date = QDate(py_start_date.year, py_start_date.month, py_start_date.day)
        q_end_date = QDate(py_end_date.year, py_end_date.month, py_end_date.day)

        # Set the QDate values into your QDate widgets
        self.startDate.setDate(q_start_date)
        self.endDate.setDate(q_end_date)

        return super().showEvent(event)
    
    def resetValues(self):
        # ── Clear file selections ──
        self.obsDataFile = None
        self.modDataFile = None
        self.obsDataLabel.setText("File: Not selected")
        self.modDataLabel.setText("File: Not selected")
        self.saveLabel.setText("File: Not selected")

        # ── Reset dates to the global settings ──
        py_start = settingsAsArrays["globalsdate"][0]
        py_end   = settingsAsArrays["globaledate"][0]
        self.startDate.setDate(QDate(py_start.year, py_start.month, py_start.day))
        self.endDate  .setDate(QDate(py_end.year,   py_end.month,   py_end.day))

        # ── Frequency‐analysis inputs ──
        self.confidenceInput.setValue(5)     # 5% default
        self.thresholdInput .setValue(10)    # 10 default
        self.pdfSpinBox     .setValue(20)    # 20 bins
        self.dataPeriodCombo.setCurrentIndex(0)  # “All Data”
        self.applyThresholdCheckbox.setChecked(False)

        # ── Ensemble default ──
        self.allMembersRadio.setChecked(True)

        # ── IDF settings ──
        self.methodMomentsRadio   .setChecked(True)
        self.parameterPowerRadio  .setChecked(False)
        self.parameterLinearRadio .setChecked(False)
        self.runningSumInput      .setValue(2)

    
    def saveResults(self):
        # Use the default directory from your configuration (assuming it's in settingsAsArrays)
        default_dir = settingsAsArrays["defaultdir"][0]
        fileName, _ = QFileDialog.getSaveFileName(self, "Save Results File", default_dir)
        if fileName:
            fm = QFontMetrics(self.saveLabel.font())
            elided = fm.elidedText(fileName, Qt.ElideMiddle, self.saveLabel.width())
            self.saveLabel.setText(elided)

    def selectObservedData(self):
        # Use the default directory for open dialogs as well
        default_dir = settingsAsArrays["defaultdir"][0]
        filter_str = (
        "TXT Files (*.TXT);;OUT Files (*.OUT);;DAT Files (*.DAT);;All Files (*.*)"
         )
        fileName, _ = QFileDialog.getOpenFileName(self, "Select Observed Data File", default_dir,filter_str)
        if fileName:
            self.obsDataFile = fileName
            fm = QFontMetrics(self.obsDataLabel.font())
            elided = fm.elidedText(fileName, Qt.ElideMiddle, self.obsDataLabel.width())
            self.obsDataLabel.setText(elided)

    def selectModelledData(self):
        # Same default starting directory is used here
        default_dir = settingsAsArrays["defaultdir"][0]
        filter_str = (
        "OUT Files (*.OUT);;DAT Files (*.DAT);;TXT Files (*.TXT);;All Files (*.*)"
         )
        fileName, _ = QFileDialog.getOpenFileName(self, "Select Modelled Data File", default_dir,filter_str)
        if fileName:
            self.modDataFile = fileName
            fm = QFontMetrics(self.modDataLabel.font())
            elided = fm.elidedText(fileName, Qt.ElideMiddle, self.modDataLabel.width())
            self.modDataLabel.setText(elided)

    def pdfPlotButtonClicked(self):
        # 1) file paths
        obsPath = getattr(self, "obsDataFile", None)
        modPath = getattr(self, "modDataFile", None)

        # 2) global start date from settings
        globalSDate = settingsAsArrays["globalsdate"][0]

        # 3) analysis dates
        fsDate = self.startDate.date().toPyDate()
        feDate = self.endDate.date().toPyDate()

        # 4) ensemble option
        if self.allMembersRadio.isChecked():
            ensembleMode  = 'allMembers'
            ensembleIndex = None
        elif self.ensembleMeanRadio.isChecked():
            ensembleMode  = 'ensembleMean'
            ensembleIndex = None
        elif self.ensembleMemberRadio.isChecked():
            ensembleMode  = 'ensembleMember'
            ensembleIndex = self.ensembleMemberSpinBox.value()
        else:
            ensembleMode  = 'allPlusMean'
            ensembleIndex = None

        # 5) number of PDF bins
        numPdfCategories = self.pdfSpinBox.value()

        dataPeriod = self.dataPeriodCombo.currentIndex()

        # 6) threshold
        applyThreshold = self.applyThresholdCheckbox.isChecked()
        threshold = self.thresholdInput.value()

        # 7) missing‐code
        globalMissingCode = settings["globalmissingcode"]

        #try:
        pdfPlot(
            observedFile      = obsPath,
            modelledFile      = modPath,
            fsDate            = fsDate,
            feDate            = feDate,
            globalStartDate   = globalSDate,
            ensembleOption    = ensembleMode,
            ensembleWanted    = ensembleIndex,
            numPdfCategories  = numPdfCategories,
            dataPeriod        = dataPeriod,
            applyThreshold    = applyThreshold,
            threshold         = threshold,
            missingCode       = globalMissingCode,
            exitAnalyses      = lambda: False
        )
        #except Exception as e:
        #    QMessageBox.critical(self, "PDF Plot Error", str(e))
    
    def linePlotButtonClicked(self):
        # 1) file paths (None if not selected)
        obsPath = getattr(self, "obsDataFile", None)
        modPath = getattr(self, "modDataFile", None)

        # 2) dates
        startDate = self.startDate.date().toPyDate()
        endDate   = self.endDate.date().toPyDate()

        # ─── VALIDATION: must be exactly 10 years apart ───
        yearDiff = endDate.year - startDate.year
        if yearDiff > 10:
            QMessageBox.warning(
                self,
                "Invalid Date Range",
                "For a line plot, start and end dates must be less than 10 years apart."
            )
            return

        # 3) ensemble mode + index
        if self.allMembersRadio.isChecked():
            ensembleMode  = 'allMembers'
            ensembleIndex = None
        elif self.ensembleMeanRadio.isChecked():
            ensembleMode  = 'ensembleMean'
            ensembleIndex = None
        elif self.ensembleMemberRadio.isChecked():
            ensembleMode  = 'ensembleMember'
            ensembleIndex = self.ensembleMemberSpinBox.value()
        else:
            ensembleMode  = 'allPlusMean'
            ensembleIndex = None

        # 4) data period
        dataPeriod = self.dataPeriodCombo.currentIndex()

        # 5) threshold toggles
        applyThreshold  = self.applyThresholdCheckbox.isChecked()
        thresholdValue  = self.thresholdInput.value()

        #try:
        linePlot(
                observedFilePath  = obsPath,
                modelledFilePath  = modPath,
                analysisStartDate = startDate,
                analysisEndDate   = endDate,
                globalStartDate   = globalSDate,
                ensembleMode      = ensembleMode,
                ensembleIndex     = ensembleIndex,
                dataPeriod        = dataPeriod,
                applyThreshold    = applyThreshold,
                thresholdValue    = thresholdValue,
                globalMissingCode = settings["globalmissingcode"],
                exitAnalysesFunc  = lambda: False
            )
        #except Exception as e:
        #    print("Line Plot Error")

    
    def qqPlotButtonClicked(self):
        # 1) files
        if not hasattr(self, "obsDataFile") or not hasattr(self, "modDataFile"):
            QMessageBox.warning(self, "Input Required",
                                "Please select both Observed and Modelled data files.")
            return
        obsPath = self.obsDataFile
        modPath = self.modDataFile

        # 2) dates
        fsDate = self.startDate.date().toPyDate()
        feDate = self.endDate.date().toPyDate()
        if fsDate >= feDate:
            QMessageBox.critical(self, "Error", "Start date must be before end date.")
            return

        # 3) ensemble settings
        if self.allMembersRadio.isChecked():
            ensembleMode  = 'allMembers'
            ensembleIndex = None
        elif self.ensembleMeanRadio.isChecked():
            ensembleMode  = 'ensembleMean'
            ensembleIndex = None
        elif self.ensembleMemberRadio.isChecked():
            ensembleMode  = 'ensembleMember'
            ensembleIndex = self.ensembleMemberSpinBox.value()
        else:
            ensembleMode  = 'allPlusMean'
            ensembleIndex = None

        # 4) numeric period index (matches your QQ.py _in_period)
        dataPeriodIndex = self.dataPeriodCombo.currentIndex()

        # 5) threshold
        applyThresh = self.applyThresholdCheckbox.isChecked()
        threshValue = self.thresholdInput.value()

        # 6) call QQ routine with error‐handling
        try:
            qqPlot(
                observedFilePath   = obsPath,
                modelledFilePath   = modPath,
                analysisStartDate  = fsDate,
                analysisEndDate    = feDate,
                globalStartDate    = globalSDate,
                ensembleMode       = ensembleMode,
                ensembleIndex      = ensembleIndex,
                dataPeriod         = dataPeriodIndex,
                applyThreshold     = applyThresh,
                thresholdValue     = threshValue,
                exitAnalysesFunc   = lambda: False
            )

        except IOError as ioe:
            QMessageBox.critical(self, "Q-Q Plot Error", str(ioe))
        except ValueError as ve:
            QMessageBox.critical(self, "Q-Q Plot Error", str(ve))
    
    
    def run_idf_analysis(self, presentation_type):
    # Fetch file paths
       file1_used = hasattr(self, "obsDataFile") and bool(self.obsDataFile)
       file2_used = hasattr(self, "modDataFile") and bool(self.modDataFile)
       file1_name = getattr(self, "obsDataFile", "")
       file2_name = getattr(self, "modDataFile", "")

    # Dates
       start_date = self.startDate.date().toPyDate()
       end_date = self.endDate.date().toPyDate()

    # Parameter method
       if self.methodMomentsRadio.isChecked():
              idf_method = "Intensity"
       elif self.parameterPowerRadio.isChecked():
            idf_method = "Power"
       elif self.parameterLinearRadio.isChecked():
           idf_method = "Linear"
       else:
            idf_method = "Intensity"

    # Running sum length
       running_sum_length = self.runningSumInput.value()

    #Threshold check
       use_threshold = self.applyThresholdCheckbox.isChecked()

    # Data period 
       data_period_choice = self.dataPeriodCombo.currentText()

    # Ensemble options
       if self.ensembleMemberRadio.isChecked():
           ensemble_option = "Single Member"
           ensemble_index = self.ensembleMemberSpinBox.value()
       else:
           ensemble_option = "All Members"
           ensemble_index = 0

       print(f"🔍 Calling run_idf with: {presentation_type}, {idf_method}, files: {file1_name}, {file2_name}")
    
       # Call the run_idf function
       run_idf(
           file1_used=file1_used,
           file2_used=file2_used,
           file1_name=file1_name,
           file2_name=file2_name,
           start_date=start_date,
           end_date=end_date,
           presentation_type= presentation_type,
           idf_method=idf_method,
           running_sum_length=running_sum_length,
           ensemble_option=ensemble_option,
           ensemble_index=ensemble_index,
           use_threshold=use_threshold,
           data_period_choice = data_period_choice
       )
       
    def faButtonClicked(self, type):
        if not hasattr(self, "obsDataFile"):
            QMessageBox.warning(self, "Input Required",
                                "Please select at least the Observed File.")
            return
        
        if not hasattr(self, "modDataFile"):
            modDataFile = None
        else:
            modDataFile = self.modDataFile

        fsDate = self.startDate.date().toPyDate()
        feDate = self.endDate.date().toPyDate()
        applyThresh = self.applyThresholdCheckbox.isChecked()
        threshValue = self.thresholdInput.value()
        dataPeriodChoice = self.dataPeriodCombo.currentIndex()

        # Determine the frequency model based on the selected radio button in faLayout
        if self.empiricalRadio.isChecked():
            freqModel = 0
        elif self.gevRadio.isChecked():
            freqModel = 1
        elif self.gumbelRadio.isChecked():
            freqModel = 2
        elif self.stretchedExpRadio.isChecked():
            freqModel = 3
        else:
            freqModel = 0 # Fallback default

        # Use the durations as given in the VB example
        durations = [1.0, 1.1, 1.2, 1.3, 1.5, 2.0, 2.5, 3.0, 3.5]

        # Determine which ensemble to pass in (0=all, >0 specific)
        if self.ensembleMemberRadio.isChecked():
            ensembleIndex = self.ensembleMemberSpinBox.value()
        else:
            ensembleIndex = 0

        # 6) Call the new Tabular FA
        frequency_analysis(
            type,
            self.obsDataFile,
            modDataFile,
            fsDate,
            feDate,
            dataPeriodChoice,
            applyThresh,
            threshValue,
            durations,
            self.confidenceInput.value(),
            ensembleIndex,
            freqModel
        )

        # Optionally, load results into a QTableWidget for GUI display.


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ContentWidget()
    window.show()
    sys.exit(app.exec_())
