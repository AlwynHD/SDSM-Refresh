import configparser
from datetime import datetime, timedelta
import os
import json
from PyQt5.QtWidgets import (QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QSizePolicy, QFrame, QLabel, QLineEdit, QCheckBox, QFileSystemModel, QGroupBox, QApplication, QHeaderView, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, QDir
from PyQt5.QtGui import QPalette, QColor
import sys

# Constants
defaultIniFile = os.path.join("src", "lib", "settings.ini")

# Default Values for Reset
defaultValues = {
    'leapValue': 1,
    'yearLength': 1,
    'yearIndicator': 366,
    'globalSDate': "01/01/1961",
    'globalEDate': "31/12/1990",
    'globalNDays': 0,
    'allowNeg': True,
    'randomSeed': True,
    'thresh': 0,
    'defaultDir': os.path.join("src", "lib"),
    'globalMissingCode': -999,
    'varianceInflation': 12,
    'biasCorrection': 1,
    'fixedThreshold': 0.5,
    'modelTransformation': 'None',
    'optimizationAlgorithm': 'Ordinary Least Squares',
    'criteriaType': 'AIC Criteria',
    'stepwiseRegression': False,
    'conditionalSelection': 'Stochastic',
    'months': [0] * 12
}

# Global Variables
leapValue = defaultValues['leapValue']
yearLength = defaultValues['yearLength']
yearIndicator = defaultValues['yearIndicator']
globalSDate = defaultValues['globalSDate']
globalEDate = defaultValues['globalEDate']
globalNDays = defaultValues['globalNDays']
allowNeg = defaultValues['allowNeg']
randomSeed = defaultValues['randomSeed']
thresh = defaultValues['thresh']
defaultDir = defaultValues['defaultDir']
globalMissingCode = defaultValues['globalMissingCode']
varianceInflation = defaultValues['varianceInflation']
biasCorrection = defaultValues['biasCorrection']
fixedThreshold = defaultValues['fixedThreshold']
modelTransformation = defaultValues['modelTransformation']
optimizationAlgorithm = defaultValues['optimizationAlgorithm']
criteriaType = defaultValues['criteriaType']
stepwiseRegression  = defaultValues['stepwiseRegression']
conditionalSelection = defaultValues['conditionalSelection']
months = defaultValues['months']

# Main PyQt5 Widget Class
class ContentWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Main content layout
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(10, 10, 10, 10)  # Set margins to create some padding
        mainLayout.setSpacing(20)  # Set spacing between elements
        self.setLayout(mainLayout)

        # Set the background color to dark blue if dark mode, else light blue
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(10, 10, 55))  # Dark Blue background
        self.setAutoFillBackground(True)
        self.setPalette(palette)

        # Create a horizontal layout to hold both groups
        groupLayout = QHBoxLayout()

        # Data Group Box
        dataGroupBox = QGroupBox("Data")
        dataGroupBox.setStyleSheet("color: white;")
        dataLayout = QVBoxLayout()
        dataGroupBox.setLayout(dataLayout)
        
        # Create a layout for the Start and End Date fields (Label & Input stacked vertically)
        dateLayout = QVBoxLayout()
        
        # Start Date Layout (Label & Input side by side)
        startDateLayout = QHBoxLayout()
        startLabel = QLabel("Start Date:")
        self.startDateEdit = QLineEdit()
        self.startDateEdit.setFixedWidth(80)
        self.startDateEdit.setAlignment(Qt.AlignCenter)
        startDateLayout.addWidget(startLabel)
        startDateLayout.addWidget(self.startDateEdit)
        
        # End Date Layout (Label & Input below Start Date)
        endDateLayout = QHBoxLayout()
        endLabel = QLabel("End Date:")
        self.endDateEdit = QLineEdit()
        self.endDateEdit.setFixedWidth(80)
        self.endDateEdit.setAlignment(Qt.AlignCenter)
        endDateLayout.addWidget(endLabel)
        endDateLayout.addWidget(self.endDateEdit)
        
        # Add start & end date layouts to the main vertical layout
        dateLayout.addLayout(startDateLayout)
        dateLayout.addLayout(endDateLayout)
        
        # Add the vertical layout to the data group
        dataLayout.addLayout(dateLayout)
        
        # Miscellaneous Group Box
        miscGroupBox = QGroupBox("Miscellaneous")
        miscGroupBox.setStyleSheet("color: white;")
        miscLayout = QVBoxLayout()
        miscGroupBox.setLayout(miscLayout)
        
        self.allowNegativeCheckBox = QCheckBox("Allow Negative Values")
        self.allowNegativeCheckBox.setChecked(True)
        self.eventThresholdEdit = QLineEdit()
        self.missingDataEdit = QLineEdit()
        self.randomSeedCheckBox = QCheckBox("Random Number Seed")
        self.randomSeedCheckBox.setChecked(True)
        
        miscLayout.addWidget(self.allowNegativeCheckBox)
        miscLayout.addWidget(QLabel("Event Threshold:"))
        miscLayout.addWidget(self.eventThresholdEdit)
        miscLayout.addWidget(QLabel("Missing Data Identifier:"))
        miscLayout.addWidget(self.missingDataEdit)
        miscLayout.addWidget(self.randomSeedCheckBox)
        
        # Default Directory Group Box
        directoryGroupBox = QGroupBox("Default Directory")
        directoryGroupBox.setStyleSheet("color: white;")
        directoryLayout = QVBoxLayout()
        directoryLayout.setAlignment(Qt.AlignCenter)
        directoryGroupBox.setLayout(directoryLayout)
        
        # Create the label, read-only text box, and button
        currentDirLabel = QLabel("Current Directory:")
        self.defaultDirDisplay = QLineEdit(defaultDir)
        self.defaultDirDisplay.setReadOnly(True)
        chooseDirButton = QPushButton("Choose Folder")
        chooseDirButton.clicked.connect(self.chooseDefaultDir)
        
        directoryLayout.addWidget(currentDirLabel)
        directoryLayout.addWidget(self.defaultDirDisplay)
        directoryLayout.addWidget(chooseDirButton)
        
        # Add the group boxes to the horizontal layout with proportional sizing
        groupLayout.addWidget(dataGroupBox, 1)         # Data group on the left
        groupLayout.addWidget(miscGroupBox, 1)         # Miscellaneous group in the center
        groupLayout.addWidget(directoryGroupBox, 2)    # Default Directory group on the right
        
        # Add the horizontal group layout to the main layout
        mainLayout.addLayout(groupLayout)
        
        # Reset Button (moved outside the Miscellaneous Group Box)
        resetButton = QPushButton("Reset")
        resetButton.clicked.connect(self.resetSettings)
        mainLayout.addWidget(resetButton)

        # Spacer to fill the rest of the layout
        mainLayout.addStretch()

        # Ensure input fields adapt to system's theme
        self.startDateEdit.setStyleSheet("color: black;")
        self.endDateEdit.setStyleSheet("color: black;")
        self.eventThresholdEdit.setStyleSheet("color: black;")
        self.missingDataEdit.setStyleSheet("color: black;")
        self.defaultDirDisplay.setStyleSheet("color: black;")

        # Load existing settings into UI elements
        self.loadSettingsIntoUi()

        # Save and Load buttons
        buttonLayout = QHBoxLayout()
        saveButton = QPushButton("Save Settings")
        saveButton.clicked.connect(self.saveSettingsFromUi)
        buttonLayout.addWidget(saveButton)

        loadButton = QPushButton("Load Settings")
        loadButton.clicked.connect(self.loadSettingsFromUi)
        buttonLayout.addWidget(loadButton)

        mainLayout.addLayout(buttonLayout)

    def chooseDefaultDir(self):
        global defaultDir
        directory = QFileDialog.getExistingDirectory(self, "Select Default Directory", defaultDir)
        if directory:
            defaultDir = directory
            self.defaultDirDisplay.setText(defaultDir)

    def validateDate(self, dateStr):
        try:
            return datetime.strptime(dateStr, "%d/%m/%Y")
        except ValueError:
            QMessageBox.critical(self, "Error", f"Error: Date '{dateStr}' is invalid. It must be in the format dd/mm/yyyy.")
            return None

    def validateNumeric(self, value, minValue=None, maxValue=None):
        try:
            num = float(value)
            if (minValue is not None and num < minValue) or (maxValue is not None and num > maxValue):
                QMessageBox.critical(self, "Error", f"Error: Value '{value}' must be between {minValue} and {maxValue}.")
                return None
            return num
        except ValueError:
            QMessageBox.critical(self, "Error", f"Error: Value '{value}' must be numeric.")
            return None

    def calculateDays(self, startDate, endDate):
        return (endDate - startDate).days + 1

    def loadSettings(self, iniFile=defaultIniFile):
        global leapValue, yearLength, yearIndicator, globalSDate, globalEDate, globalNDays, allowNeg, randomSeed, thresh, defaultDir, globalMissingCode
        global varianceInflation, biasCorrection, fixedThreshold, modelTransformation, optimizationAlgorithm, criteriaType, stepwiseRegression, conditionalSelection, months

        if not os.path.exists(iniFile):
            return

        config = configparser.ConfigParser()
        config.read(iniFile)

        try:
            yearIndicator = self.safeGetInt(config, 'Settings', 'YearIndicator', defaultValues['yearIndicator'])
            globalSDate = config.get('Settings', 'GlobalSDate', fallback=defaultValues['globalSDate'])
            globalEDate = config.get('Settings', 'GlobalEDate', fallback=defaultValues['globalEDate'])
            allowNeg = config.getboolean('Settings', 'AllowNeg', fallback=defaultValues['allowNeg'])
            randomSeed = config.getboolean('Settings', 'RandomSeed', fallback=defaultValues['randomSeed'])
            thresh = self.safeGetFloat(config, 'Settings', 'Thresh', defaultValues['thresh'])
            globalMissingCode = self.safeGetInt(config, 'Settings', 'GlobalMissingCode', defaultValues['globalMissingCode'])
            defaultDir = config.get('Settings', 'DefaultDir', fallback=defaultValues['defaultDir'])
            varianceInflation = self.safeGetInt(config, 'Settings', 'VarianceInflation', defaultValues['varianceInflation'])
            biasCorrection = self.safeGetInt(config, 'Settings', 'BiasCorrection', defaultValues['biasCorrection'])
            fixedThreshold = self.safeGetFloat(config, 'Settings', 'FixedThreshold', defaultValues['fixedThreshold'])
            modelTransformation = config.get('Settings', 'ModelTransformation', fallback=defaultValues['modelTransformation'])
            optimizationAlgorithm = config.get('Settings', 'OptimizationAlgorithm', fallback=defaultValues['optimizationAlgorithm'])
            criteriaType = config.get('Settings', 'CriteriaType', fallback=defaultValues['criteriaType'])
            stepwiseRegression = config.getboolean('Settings', 'StepwiseRegression', fallback=defaultValues['stepwiseRegression'])
            conditionalSelection = config.get('Settings', 'ConditionalSelection', fallback=defaultValues['conditionalSelection'])
            months = [int(x) for x in config.get('Settings', 'Months', fallback=','.join(map(str, defaultValues['months']))).split(',')]

            startDate = self.validateDate(globalSDate)
            endDate = self.validateDate(globalEDate)
            if startDate and endDate:
                if startDate > endDate:
                    QMessageBox.critical(self, "Error", "Error: Start date cannot be after end date. Using default values.")
                    globalSDate = defaultValues['globalSDate']
                    globalEDate = defaultValues['globalEDate']
                    startDate = self.validateDate(globalSDate)
                    endDate = self.validateDate(globalEDate)
                globalNDays = self.calculateDays(startDate, endDate)

        except configparser.Error as e:
            QMessageBox.critical(self, "Error", f"Error loading settings: {e}")

    def get_settings_json(self):
        settings = {
            "yearIndicator": yearIndicator,
            "globalSDate": globalSDate,
            "globalEDate": globalEDate,
            "allowNeg": allowNeg,
            "randomSeed": randomSeed,
            "thresh": thresh,
            "globalMissingCode": globalMissingCode,
            "defaultDir": defaultDir,
            "varianceInflation": varianceInflation,
            "biasCorrection": biasCorrection,
            "fixedThreshold": fixedThreshold,
            "modelTransformation": modelTransformation,
            "optimizationAlgorithm": optimizationAlgorithm,
            "criteriaType": criteriaType,
            "stepwiseRegression": stepwiseRegression,
            "conditionalSelection": conditionalSelection,
            "months": months
        }
        return json.dumps(settings, indent=4)

    def safeGetInt(self, config, section, option, fallback):
        try:
            return config.getint(section, option, fallback=fallback)
        except ValueError:
            return fallback

    def safeGetFloat(self, config, section, option, fallback):
        try:
            return config.getfloat(section, option, fallback=fallback)
        except ValueError:
            return fallback

    def saveSettings(self, iniFile=None, silent=False):
        global yearIndicator, globalSDate, globalEDate, allowNeg, randomSeed, thresh, globalMissingCode, defaultDir
        global varianceInflation, biasCorrection, fixedThreshold, modelTransformation, optimizationAlgorithm, criteriaType, stepwiseRegression, conditionalSelection, months

        if iniFile is None:
            iniFile = QFileDialog.getExistingDirectory(None, "Select Directory to Save Settings", defaultDir)
            if not iniFile:
                return
            iniFile = os.path.join(iniFile, 'settings.ini')

        config = configparser.ConfigParser()
        config['Settings'] = {
            'YearIndicator': str(yearIndicator),
            'GlobalSDate': globalSDate,
            'GlobalEDate': globalEDate,
            'AllowNeg': str(allowNeg),
            'RandomSeed': str(randomSeed),
            'Thresh': str(thresh),
            'GlobalMissingCode': str(int(globalMissingCode)),
            'DefaultDir': defaultDir,
            'VarianceInflation': str(varianceInflation),
            'BiasCorrection': str(biasCorrection),
            'FixedThreshold': str(fixedThreshold),
            'ModelTransformation': modelTransformation,
            'OptimizationAlgorithm': optimizationAlgorithm,
            'CriteriaType': criteriaType,
            'StepwiseRegression': str(stepwiseRegression),
            'ConditionalSelection': conditionalSelection,
            'Months': ','.join(map(str, months))
        }

        try:
            with open(iniFile, 'w') as configfile:
                config.write(configfile)
            if not silent:
                QMessageBox.information(self, "Info", f"Settings saved to '{iniFile}'")
        except OSError as e:
            QMessageBox.critical(self, "Error", f"Error: Could not save settings to '{iniFile}'. Reason: {e}")

    def loadSettingsIntoUi(self, ini=True):
        if ini:
            self.loadSettings()
        self.startDateEdit.setText(globalSDate)
        self.endDateEdit.setText(globalEDate)
        self.eventThresholdEdit.setText(str(thresh))
        self.missingDataEdit.setText(str(globalMissingCode))
        self.allowNegativeCheckBox.setChecked(allowNeg)
        self.randomSeedCheckBox.setChecked(randomSeed)
        # Update the default directory display
        self.defaultDirDisplay.setText(defaultDir)

    def saveSettingsFromUi(self):
        global globalSDate, globalEDate, thresh, globalMissingCode, allowNeg, randomSeed, defaultDir

        # Validate Start Date
        globalSDate = self.startDateEdit.text()
        startDate = self.validateDate(globalSDate)
        if not startDate:
            QMessageBox.critical(self, "Error", "Error: Invalid start date. Abandoning save process.")
            return

        # Validate End Date
        globalEDate = self.endDateEdit.text()
        endDate = self.validateDate(globalEDate)
        if not endDate:
            QMessageBox.critical(self, "Error", "Error: Invalid end date. Abandoning save process.")
            return

        # Ensure Start Date is before End Date
        if startDate > endDate:
            QMessageBox.critical(self, "Error", "Error: Start date cannot be after end date. Abandoning save process.")
            return

        # Validate Threshold
        thresh = self.validateNumeric(self.eventThresholdEdit.text(), minValue=0)
        if thresh is None:
            QMessageBox.critical(self, "Error", "Error: Invalid threshold value. Abandoning save process.")
            return

        # Validate Missing Data Code
        if self.missingDataEdit.text():
            globalMissingCode = self.validateNumeric(self.missingDataEdit.text())
            if globalMissingCode is None:
                QMessageBox.critical(self, "Error", "Error: Invalid missing data code. Abandoning save process.")
                return
        else:
            globalMissingCode = -999

        # Update other settings
        allowNeg = self.allowNegativeCheckBox.isChecked()
        randomSeed = self.randomSeedCheckBox.isChecked()

        # If all validations pass, proceed with saving settings
        self.saveSettings()

    def loadSettingsFromUi(self):
        iniFile = QFileDialog.getOpenFileName(self, "Open Settings File", defaultDir, "INI Files (*.ini)")[0]
        if iniFile and os.path.isfile(iniFile):
            self.loadSettings(iniFile)
            self.loadSettingsIntoUi()

    def resetSettings(self):
        global leapValue, yearLength, yearIndicator, globalSDate, globalEDate, globalNDays, allowNeg, randomSeed, thresh, defaultDir, globalMissingCode, varianceInflation, biasCorrection, fixedThreshold
        
        # Reset to default values
        leapValue = defaultValues['leapValue']
        yearLength = defaultValues['yearLength']
        yearIndicator = defaultValues['yearIndicator']
        globalSDate = defaultValues['globalSDate']
        globalEDate = defaultValues['globalEDate']
        globalNDays = self.calculateDays(self.validateDate(globalSDate), self.validateDate(globalEDate))
        allowNeg = defaultValues['allowNeg']
        randomSeed = defaultValues['randomSeed']
        thresh = defaultValues['thresh']
        defaultDir = defaultValues['defaultDir']
        globalMissingCode = defaultValues['globalMissingCode']

        # Load the default values into the UI elements
        self.loadSettingsIntoUi(False)

    def hideEvent(self, event):
        """
        Upon hiding the window, validate the UI values and silently save them to the default INI file.
        All validation prompts (e.g. for date or numeric errors) remain active.
        """
        global globalSDate, globalEDate, thresh, globalMissingCode, allowNeg, randomSeed

        # Validate Start Date
        globalSDate = self.startDateEdit.text()
        startDate = self.validateDate(globalSDate)
        if not startDate:
            event.ignore()
            return

        # Validate End Date
        globalEDate = self.endDateEdit.text()
        endDate = self.validateDate(globalEDate)
        if not endDate:
            event.ignore()
            return

        # Check date order
        if startDate > endDate:
            QMessageBox.critical(self, "Error", "Error: Start date cannot be after end date. Abandoning save process.")
            event.ignore()
            return

        # Validate Threshold
        thresh = self.validateNumeric(self.eventThresholdEdit.text(), minValue=0)
        if thresh is None:
            event.ignore()
            return

        # Validate Missing Data Code
        if self.missingDataEdit.text():
            globalMissingCode = self.validateNumeric(self.missingDataEdit.text())
            if globalMissingCode is None:
                event.ignore()
                return
        else:
            globalMissingCode = -999

        # Update checkboxes
        allowNeg = self.allowNegativeCheckBox.isChecked()
        randomSeed = self.randomSeedCheckBox.isChecked()

        # Save settings silently to the default ini file without file-dialog or confirmation prompt.
        self.saveSettings(defaultIniFile, silent=True)
        event.accept()

# Main function for testing the UI
def main():
    app = QApplication(sys.argv)
    window = ContentWidget()
    window.setWindowTitle("SDSM Wireframe")
    window.resize(600, 600)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
