import configparser
from datetime import datetime
import os
import json
from PyQt5.QtWidgets import (
    QVBoxLayout, QWidget, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QCheckBox, QGroupBox,
    QFileDialog, QMessageBox, QApplication
)
from PyQt5.QtCore import Qt
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
stepwiseRegression = defaultValues['stepwiseRegression']
conditionalSelection = defaultValues['conditionalSelection']
months = defaultValues['months']

class ContentWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Main content layout
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(10, 10, 10, 10)
        mainLayout.setSpacing(20)
        self.setLayout(mainLayout)

        # === Data Group ===
        dataGroupBox = QGroupBox("Data")
        dataGroupBox.setStyleSheet("color: black;")
        dataLayout = QVBoxLayout()
        dataGroupBox.setLayout(dataLayout)

        # Start Date
        startLayout = QHBoxLayout()
        startLayout.addWidget(QLabel("Start Date:"))
        self.startDateEdit = QLineEdit()
        self.startDateEdit.setFixedWidth(80)
        self.startDateEdit.setAlignment(Qt.AlignCenter)
        startLayout.addWidget(self.startDateEdit)
        dataLayout.addLayout(startLayout)

        # End Date
        endLayout = QHBoxLayout()
        endLayout.addWidget(QLabel("End Date:"))
        self.endDateEdit = QLineEdit()
        self.endDateEdit.setFixedWidth(80)
        self.endDateEdit.setAlignment(Qt.AlignCenter)
        endLayout.addWidget(self.endDateEdit)
        dataLayout.addLayout(endLayout)

        # === Miscellaneous Group ===
        miscGroupBox = QGroupBox("Miscellaneous")
        miscGroupBox.setStyleSheet("color: black;")
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

        # === Default Directory Group ===
        dirGroupBox = QGroupBox("Default Directory")
        dirGroupBox.setStyleSheet("color: black;")
        dirLayout = QVBoxLayout()
        dirGroupBox.setLayout(dirLayout)

        dirLayout.addWidget(QLabel("Current Directory:"))
        self.defaultDirDisplay = QLineEdit(defaultDir)
        self.defaultDirDisplay.setReadOnly(True)
        dirLayout.addWidget(self.defaultDirDisplay)
        chooseBtn = QPushButton("Choose Folder")
        chooseBtn.clicked.connect(self.chooseDefaultDir)
        dirLayout.addWidget(chooseBtn)

        # Assemble top groups
        topLayout = QHBoxLayout()
        topLayout.addWidget(dataGroupBox, 1)
        topLayout.addWidget(miscGroupBox, 1)
        topLayout.addWidget(dirGroupBox, 2)
        mainLayout.addLayout(topLayout)

        # Reset Button
        mainLayout.addStretch()
        resetButton = QPushButton("🔄 Reset Settings")
        resetButton.setStyleSheet("background-color: #ED0800; color: white; font-weight: bold;")
        resetButton.clicked.connect(self.resetSettings)
        mainLayout.addWidget(resetButton)
        

        # Text color for inputs
        for w in (self.startDateEdit, self.endDateEdit,
                  self.eventThresholdEdit, self.missingDataEdit,
                  self.defaultDirDisplay):
            w.setStyleSheet("color: black;")

        # Load into UI
        self.loadSettingsIntoUi()

        # === Export / Save / Load Buttons ===
        buttonLayout = QHBoxLayout()

        exportBtn = QPushButton("📤 Export Settings")
        exportBtn.setStyleSheet("background-color: #1FC7F5; color: white; font-weight: bold;")
        exportBtn.clicked.connect(self.saveSettingsFromUi)
        buttonLayout.addWidget(exportBtn)

        saveBtn = QPushButton("💾 Save Settings")
        saveBtn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        saveBtn.clicked.connect(self.saveSettingsDefault)
        buttonLayout.addWidget(saveBtn)

        loadBtn = QPushButton("📂 Load Settings")
        loadBtn.setStyleSheet("background-color: #F57F0C; color: white; font-weight: bold;")
        loadBtn.clicked.connect(self.loadSettingsFromUi)
        buttonLayout.addWidget(loadBtn)

        mainLayout.addLayout(buttonLayout)

    def chooseDefaultDir(self):
        global defaultDir
        d = QFileDialog.getExistingDirectory(self, "Select Default Directory", defaultDir)
        if d:
            self.defaultDirDisplay.setText(d)

    def validateDate(self, s):
        try:
            return datetime.strptime(s, "%d/%m/%Y")
        except ValueError:
            QMessageBox.critical(self, "Error",
                                 f"Date '{s}' is invalid. Must be dd/mm/yyyy.")
            return None

    def validateNumeric(self, s, minValue=None, maxValue=None):
        try:
            val = float(s)
            if (minValue is not None and val < minValue) or \
               (maxValue is not None and val > maxValue):
                QMessageBox.critical(self, "Error",
                                     f"Value '{s}' must be between {minValue} and {maxValue}.")
                return None
            return val
        except ValueError:
            QMessageBox.critical(self, "Error", f"Value '{s}' must be numeric.")
            return None

    def calculateDays(self, start, end):
        return (end - start).days + 1

    def loadSettings(self, iniFile=defaultIniFile):
        global leapValue, yearLength, yearIndicator, globalSDate, globalEDate, globalNDays
        global allowNeg, randomSeed, thresh, defaultDir, globalMissingCode
        global varianceInflation, biasCorrection, fixedThreshold
        global modelTransformation, optimizationAlgorithm, criteriaType
        global stepwiseRegression, conditionalSelection, months

        if not os.path.exists(iniFile):
            return

        cfg = configparser.ConfigParser()
        cfg.read(iniFile)

        try:
            yearIndicator = self.safeGetInt(cfg, 'Settings', 'YearIndicator', defaultValues['yearIndicator'])
            globalSDate   = cfg.get('Settings', 'GlobalSDate', fallback=defaultValues['globalSDate'])
            globalEDate   = cfg.get('Settings', 'GlobalEDate', fallback=defaultValues['globalEDate'])
            allowNeg      = cfg.getboolean('Settings', 'AllowNeg', fallback=defaultValues['allowNeg'])
            randomSeed    = cfg.getboolean('Settings', 'RandomSeed', fallback=defaultValues['randomSeed'])
            thresh        = self.safeGetFloat(cfg, 'Settings', 'Thresh', fallback=defaultValues['thresh'])
            globalMissingCode = self.safeGetInt(cfg, 'Settings', 'GlobalMissingCode',
                                                defaultValues['globalMissingCode'])
            defaultDir    = cfg.get('Settings', 'DefaultDir', fallback=defaultValues['defaultDir'])
            varianceInflation = self.safeGetInt(cfg, 'Settings', 'VarianceInflation',
                                                defaultValues['varianceInflation'])
            biasCorrection    = self.safeGetInt(cfg, 'Settings', 'BiasCorrection',
                                                defaultValues['biasCorrection'])
            fixedThreshold    = self.safeGetFloat(cfg, 'Settings', 'FixedThreshold',
                                                  defaultValues['fixedThreshold'])
            modelTransformation = cfg.get('Settings', 'ModelTransformation',
                                          fallback=defaultValues['modelTransformation'])
            optimizationAlgorithm = cfg.get('Settings', 'OptimizationAlgorithm',
                                            fallback=defaultValues['optimizationAlgorithm'])
            criteriaType   = cfg.get('Settings', 'CriteriaType',
                                     fallback=defaultValues['criteriaType'])
            stepwiseRegression = cfg.getboolean('Settings', 'StepwiseRegression',
                                                fallback=defaultValues['stepwiseRegression'])
            conditionalSelection = cfg.get('Settings', 'ConditionalSelection',
                                           fallback=defaultValues['conditionalSelection'])
            months = [int(x) for x in cfg.get('Settings', 'Months',
                                             fallback=','.join(map(str, defaultValues['months']))).split(',')]
            dt_s = self.validateDate(globalSDate)
            dt_e = self.validateDate(globalEDate)
            if dt_s and dt_e:
                if dt_s > dt_e:
                    QMessageBox.critical(self, "Error",
                                         "Start date after end date. Reverting to defaults.")
                    globalSDate = defaultValues['globalSDate']
                    globalEDate = defaultValues['globalEDate']
                    dt_s = self.validateDate(globalSDate)
                    dt_e = self.validateDate(globalEDate)
                globalNDays = self.calculateDays(dt_s, dt_e)
        except configparser.Error as e:
            QMessageBox.critical(self, "Error", f"Error loading settings: {e}")

    def saveSettings(self, iniFile=None, silent=False):
        """
        Write out current globals into an INI. If iniFile is None, prompt for folder.
        """
        global yearIndicator, globalSDate, globalEDate, allowNeg, randomSeed, thresh
        global globalMissingCode, defaultDir, varianceInflation, biasCorrection
        global fixedThreshold, modelTransformation, optimizationAlgorithm
        global criteriaType, stepwiseRegression, conditionalSelection, months

        if iniFile is None:
            folder = QFileDialog.getExistingDirectory(self, "Select Directory to Save Settings", defaultDir)
            if not folder:
                return
            iniFile = os.path.join(folder, 'settings.ini')

        cfg = configparser.ConfigParser()
        cfg['Settings'] = {
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
            with open(iniFile, 'w') as f:
                cfg.write(f)
            if not silent:
                QMessageBox.information(self, "Info", f"Settings saved to '{iniFile}'")
        except OSError as e:
            QMessageBox.critical(self, "Error", f"Could not save settings to '{iniFile}': {e}")

    def loadSettingsIntoUi(self, ini=True):
        if ini:
            self.loadSettings()
        self.startDateEdit.setText(globalSDate)
        self.endDateEdit.setText(globalEDate)
        self.eventThresholdEdit.setText(str(thresh))
        self.missingDataEdit.setText(str(globalMissingCode))
        self.allowNegativeCheckBox.setChecked(allowNeg)
        self.randomSeedCheckBox.setChecked(randomSeed)
        self.defaultDirDisplay.setText(defaultDir)

    def saveSettingsFromUi(self):
        """
        EXPORT: Prompt for folder & write settings.ini there.
        """
        global globalSDate, globalEDate, thresh, globalMissingCode, allowNeg, randomSeed

        # 1) Validate Start Date
        gs = self.startDateEdit.text().strip()
        dt_s = self.validateDate(gs)
        if not dt_s:
            QMessageBox.critical(self, "Error", "Invalid start date. Export aborted.")
            return

        # 2) Validate End Date
        ge = self.endDateEdit.text().strip()
        dt_e = self.validateDate(ge)
        if not dt_e:
            QMessageBox.critical(self, "Error", "Invalid end date. Export aborted.")
            return

        if dt_s > dt_e:
            QMessageBox.critical(self, "Error", "Start date cannot be after end date.")
            return

        # 3) Validate threshold
        tv = self.validateNumeric(self.eventThresholdEdit.text().strip(), minValue=0)
        if tv is None:
            QMessageBox.critical(self, "Error", "Invalid threshold. Export aborted.")
            return

        # 4) Validate missing-data code
        md = self.missingDataEdit.text().strip()
        if md:
            mc = self.validateNumeric(md)
            if mc is None:
                QMessageBox.critical(self, "Error", "Invalid missing-data code. Export aborted.")
                return
            globalMissingCode = mc
        else:
            globalMissingCode = defaultValues['globalMissingCode']

        # 5) Update globals
        globalSDate = gs
        globalEDate = ge
        thresh = tv
        allowNeg = self.allowNegativeCheckBox.isChecked()
        randomSeed = self.randomSeedCheckBox.isChecked()

        # 6) Write out via saveSettings (will prompt for folder)
        self.saveSettings(iniFile=None, silent=False)

    def saveSettingsDefault(self):
        """
        SAVE: Write current settings to the default INI without prompting.
        """
        global globalSDate, globalEDate, thresh, globalMissingCode, allowNeg, randomSeed

        # Validate as above
        gs = self.startDateEdit.text().strip()
        dt_s = self.validateDate(gs)
        if not dt_s:
            QMessageBox.critical(self, "Error", "Invalid start date. Save aborted.")
            return

        ge = self.endDateEdit.text().strip()
        dt_e = self.validateDate(ge)
        if not dt_e:
            QMessageBox.critical(self, "Error", "Invalid end date. Save aborted.")
            return

        if dt_s > dt_e:
            QMessageBox.critical(self, "Error", "Start date cannot be after end date.")
            return

        tv = self.validateNumeric(self.eventThresholdEdit.text().strip(), minValue=0)
        if tv is None:
            QMessageBox.critical(self, "Error", "Invalid threshold. Save aborted.")
            return

        md = self.missingDataEdit.text().strip()
        if md:
            mc = self.validateNumeric(md)
            if mc is None:
                QMessageBox.critical(self, "Error", "Invalid missing-data code. Save aborted.")
                return
            globalMissingCode = mc
        else:
            globalMissingCode = defaultValues['globalMissingCode']

        globalSDate = gs
        globalEDate = ge
        thresh = tv
        allowNeg = self.allowNegativeCheckBox.isChecked()
        randomSeed = self.randomSeedCheckBox.isChecked()

        # Write to defaultIniFile
        global defaultDir
        defaultDir = self.defaultDirDisplay.text()
        self.saveSettings(iniFile=defaultIniFile, silent=False)

    def loadSettingsFromUi(self):
        """
        LOAD: Prompt for existing INI and load it into UI.
        """
        iniFile, _ = QFileDialog.getOpenFileName(self, "Open Settings File",
                                                 defaultDir, "INI Files (*.ini)")
        if iniFile and os.path.isfile(iniFile):
            self.loadSettings(iniFile)
            self.loadSettingsIntoUi(ini=False)

    def resetSettings(self):
        """
        Reset all settings to defaults, then refresh UI.
        """
        global leapValue, yearLength, yearIndicator, globalSDate, globalEDate, globalNDays
        global allowNeg, randomSeed, thresh, defaultDir, globalMissingCode

        leapValue = defaultValues['leapValue']
        yearLength = defaultValues['yearLength']
        yearIndicator = defaultValues['yearIndicator']
        globalSDate = defaultValues['globalSDate']
        globalEDate = defaultValues['globalEDate']
        dt_s = self.validateDate(globalSDate)
        dt_e = self.validateDate(globalEDate)
        globalNDays = self.calculateDays(dt_s, dt_e) if dt_s and dt_e else 0
        allowNeg = defaultValues['allowNeg']
        randomSeed = defaultValues['randomSeed']
        thresh = defaultValues['thresh']
        defaultDir = defaultValues['defaultDir']
        globalMissingCode = defaultValues['globalMissingCode']

        self.loadSettingsIntoUi(ini=False)

    def safeGetInt(self, cfg, section, option, fallback):
        try:
            return cfg.getint(section, option, fallback=fallback)
        except ValueError:
            return fallback

    def safeGetFloat(self, cfg, section, option, fallback):
        try:
            return cfg.getfloat(section, option, fallback=fallback)
        except ValueError:
            return fallback

    def get_settings_json(self):
        """
        Return current settings as a JSON string.
        """
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

def main():
    app = QApplication(sys.argv)
    w = ContentWidget()
    w.setWindowTitle("Data Settings")
    w.resize(600, 600)
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
