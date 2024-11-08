import configparser
from datetime import datetime, timedelta
import os
from PyQt5.QtWidgets import (QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QSizePolicy, QFrame, QLabel, QLineEdit, QCheckBox, QFileSystemModel, QGroupBox, QApplication, QHeaderView, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, QDir
from PyQt5.QtGui import QPalette, QColor
import sys

# Constants
defaultIniFile = 'settings.ini'

# Global Variables
leapValue = 1
yearLength = 1
yearIndicator = 366
globalSDate = "01/01/1961"
globalEDate = "31/12/1990"
globalNDays = 0
allowNeg = True
randomSeed = True
thresh = 0
defaultDir = QDir.homePath()
globalMissingCode = -999

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

        # Data Group Box
        dataGroupBox = QGroupBox("Data")
        dataGroupBox.setStyleSheet("color: white;")
        dataLayout = QVBoxLayout()
        dataGroupBox.setLayout(dataLayout)

        self.startDateEdit = QLineEdit()
        self.endDateEdit = QLineEdit()
        dataLayout.addWidget(QLabel("Standard Start Date:"))
        dataLayout.addWidget(self.startDateEdit)
        dataLayout.addWidget(QLabel("Standard End Date:"))
        dataLayout.addWidget(self.endDateEdit)

        mainLayout.addWidget(dataGroupBox)

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

        mainLayout.addWidget(miscGroupBox)

        # Spacer to fill the rest of the layout
        mainLayout.addStretch()

        # Ensure input fields adapt to system's theme
        self.startDateEdit.setStyleSheet("color: black;")
        self.endDateEdit.setStyleSheet("color: black;")
        self.eventThresholdEdit.setStyleSheet("color: black;")
        self.missingDataEdit.setStyleSheet("color: black;")

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
        global leapValue, yearLength, yearIndicator, globalSDate, globalEDate, globalNDays
        global allowNeg, randomSeed, thresh, defaultDir, globalMissingCode

        if not os.path.exists(iniFile):
            return

        config = configparser.ConfigParser()
        config.read(iniFile)

        try:
            yearIndicator = config.getint('SDSM', 'YearIndicator', fallback=366)
            globalSDate = config.get('SDSM', 'GlobalSDate', fallback="01/01/1961")
            globalEDate = config.get('SDSM', 'GlobalEDate', fallback="31/12/1990")
            allowNeg = config.getboolean('SDSM', 'AllowNeg', fallback=True)
            randomSeed = config.getboolean('SDSM', 'RandomSeed', fallback=True)
            thresh = config.getfloat('SDSM', 'Thresh', fallback=0)
            globalMissingCode = int(float(config.get('SDSM', 'GlobalMissingCode', fallback='-999')))
            defaultDir = config.get('SDSM', 'DefaultDir', fallback=QDir.homePath())

            startDate = self.validateDate(globalSDate)
            endDate = self.validateDate(globalEDate)
            if startDate and endDate:
                if startDate > endDate:
                    QMessageBox.critical(self, "Error", "Error: Start date cannot be after end date. Using default values.")
                    globalSDate = '01/01/1961'
                    globalEDate = '31/12/1990'
                    startDate = self.validateDate(globalSDate)
                    endDate = self.validateDate(globalEDate)
                globalNDays = self.calculateDays(startDate, endDate)

        except configparser.Error as e:
            QMessageBox.critical(self, "Error", f"Error loading settings: {e}")

    def saveSettings(self, iniFile=None):
        if iniFile is None:
            iniFile = QFileDialog.getExistingDirectory(None, "Select Directory to Save Settings", defaultDir)

        if not iniFile:
            QMessageBox.critical(self, "Error", "Error: No directory selected for saving settings.")
            return
        iniFile = os.path.join(iniFile, 'settings.ini')

        config = configparser.ConfigParser()
        config['SDSM'] = {
            'YearIndicator': str(yearIndicator),
            'GlobalSDate': globalSDate,
            'GlobalEDate': globalEDate,
            'AllowNeg': str(allowNeg),
            'RandomSeed': str(randomSeed),
            'Thresh': str(thresh),
            'GlobalMissingCode': str(int(globalMissingCode)),
            'DefaultDir': defaultDir
        }

        try:
            if os.path.isdir(iniFile):
                iniFile = os.path.join(iniFile, 'settings.ini')
            with open(iniFile, 'w') as configfile:
                config.write(configfile)
                QMessageBox.information(self, "Info", f"Settings saved to '{iniFile}'")
        except OSError as e:
            QMessageBox.critical(self, "Error", f"Error: Could not save settings to the specified location '{iniFile}'. Reason: {e}")

    def loadSettingsIntoUi(self):
        self.loadSettings()
        self.startDateEdit.setText(globalSDate)
        self.endDateEdit.setText(globalEDate)
        self.eventThresholdEdit.setText(str(thresh))
        self.missingDataEdit.setText(str(globalMissingCode))
        self.allowNegativeCheckBox.setChecked(allowNeg)
        self.randomSeedCheckBox.setChecked(randomSeed)

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
