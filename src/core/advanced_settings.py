from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QRadioButton, QLineEdit, QLabel, QGroupBox, QPushButton, QCheckBox, QFileDialog, QButtonGroup, QMessageBox)
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt,QDir

import configparser
import os
import sys

# Constants
defaultIniFile = 'settings.ini'

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
    'defaultDir': QDir.homePath(),
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
        mainLayout.setContentsMargins(10, 10, 10, 10)  # Set margins to create some padding
        mainLayout.setSpacing(10)  # Set spacing between elements to minimize space
        self.setLayout(mainLayout)

        # Set the background color to dark blue
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(10, 10, 55))  # Dark Blue background
        self.setAutoFillBackground(True)
        self.setPalette(palette)

        # Model Transformation Group Box
        modelTransGroupBox = QGroupBox("Model Transformation")
        modelTransGroupBox.setStyleSheet("color: white;")
        modelTransLayout = QHBoxLayout()
        modelTransGroupBox.setLayout(modelTransLayout)
        
        # Reduce unnecessary space
        modelTransLayout.setSpacing(5)  # Adjust spacing between buttons
        modelTransLayout.setContentsMargins(5, 0, 5, 0)
        
        # Create radio buttons
        self.transNone = QRadioButton("None")
        self.transFourthRoot = QRadioButton("Fourth root")
        self.transNaturalLog = QRadioButton("Natural log")
        self.transInverseNormal = QRadioButton("Inverse Normal")
        self.transBoxCox = QRadioButton("Box Cox")
        self.transNone.setChecked(True)

        modelTransLayout.addWidget(self.transNone)
        modelTransLayout.addWidget(self.transFourthRoot)
        modelTransLayout.addWidget(self.transNaturalLog)
        modelTransLayout.addWidget(self.transInverseNormal)
        modelTransLayout.addWidget(self.transBoxCox)

        mainLayout.addWidget(modelTransGroupBox)
        
        # Parent layout to hold all three group boxes horizontally
        groupContainer = QHBoxLayout()
        
        # Variance Inflation Group
        varianceInflationGroup = QGroupBox("Variance Inflation")
        varianceInflationGroup.setStyleSheet("color: white;")
        varianceInflationLayout = QHBoxLayout()
        varianceInflationGroup.setLayout(varianceInflationLayout)
        
        varianceInflationLayout.addWidget(QLabel("Value:"))
        self.varianceInflationEdit = QLineEdit()
        self.varianceInflationEdit.setFixedWidth(60)
        varianceInflationLayout.addWidget(self.varianceInflationEdit)
        
        groupContainer.addWidget(varianceInflationGroup)
        
        # Bias Correction Group
        biasCorrectionGroup = QGroupBox("Bias Correction")
        biasCorrectionGroup.setStyleSheet("color: white;")
        biasCorrectionLayout = QHBoxLayout()
        biasCorrectionGroup.setLayout(biasCorrectionLayout)
        
        biasCorrectionLayout.addWidget(QLabel("Value:"))
        self.biasCorrectionEdit = QLineEdit()
        self.biasCorrectionEdit.setFixedWidth(60)
        biasCorrectionLayout.addWidget(self.biasCorrectionEdit)
        
        groupContainer.addWidget(biasCorrectionGroup)
        
        # Conditional Selection Group Box
        conditionalGroupBox = QGroupBox("Conditional Selection")
        conditionalGroupBox.setStyleSheet("color: white;")
        conditionalLayout = QHBoxLayout()
        conditionalGroupBox.setLayout(conditionalLayout)
        
        self.conditionalStochastic = QRadioButton("Stochastic")
        self.conditionalFixedThreshold = QRadioButton("Fixed Threshold:")
        self.fixedThresholdEdit = QLineEdit()
        self.fixedThresholdEdit.setFixedWidth(50)
        
        conditionalLayout.addWidget(self.conditionalStochastic)
        conditionalLayout.addWidget(self.conditionalFixedThreshold)
        conditionalLayout.addWidget(self.fixedThresholdEdit)
        
        self.conditionalStochastic.setChecked(True)
        
        groupContainer.addWidget(conditionalGroupBox)
        
        # Add the entire horizontal row to the main layout
        mainLayout.addLayout(groupContainer)

        # Optimization Algorithm Group Box
        optimGroupBox = QGroupBox("Optimization Algorithm")
        optimGroupBox.setStyleSheet("color: white;")
        optimLayout = QVBoxLayout()
        optimGroupBox.setLayout(optimLayout)

        # Radio buttons for optimization algorithms
        self.optimOrdinaryLeastSquares = QRadioButton("Ordinary Least Squares")
        self.optimDualSimplex = QRadioButton("Dual Simplex")
        self.stepwiseRegressionCheck = QCheckBox("Stepwise Regression")
        self.aicCriterion = QRadioButton("AIC Criteria")
        self.aicCriterion.setChecked(True)
        self.bicCriterion = QRadioButton("BIC Criteria")

        self.optimOrdinaryLeastSquares.setChecked(True)

        # Group OLS and Dual Simplex into a button group
        optimButtonGroup = QButtonGroup(self)
        optimButtonGroup.addButton(self.optimOrdinaryLeastSquares)
        optimButtonGroup.addButton(self.optimDualSimplex)

        # Group AIC and BIC into a separate button group
        criteriaButtonGroup = QButtonGroup(self)
        criteriaButtonGroup.addButton(self.aicCriterion)
        criteriaButtonGroup.addButton(self.bicCriterion)

        optimLayout.addWidget(self.optimOrdinaryLeastSquares)
        optimLayout.addWidget(self.optimDualSimplex)
        optimLayout.addWidget(self.stepwiseRegressionCheck)
        optimLayout.addWidget(self.aicCriterion)
        optimLayout.addWidget(self.bicCriterion)

        mainLayout.addWidget(optimGroupBox)

        # Wet Day Percentage Profile Group Box
        wetDayGroupBox = QGroupBox("Wet Day Percentage Profile")
        wetDayGroupBox.setStyleSheet("color: white;")
        wetDayLayout = QHBoxLayout()  # Horizontal layout for all months
        wetDayGroupBox.setLayout(wetDayLayout)
        
        self.wetDayEdits = []
        
        for month in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]:
            monthLayout = QVBoxLayout()  # Vertical layout for label & textbox
            
            monthLabel = QLabel(month)
            monthLabel.setAlignment(Qt.AlignCenter)  # Center text for better alignment
            
            monthEdit = QLineEdit()
            monthEdit.setFixedWidth(40)
            monthEdit.setAlignment(Qt.AlignCenter)  # Center text inside input box
            
            self.wetDayEdits.append(monthEdit)
            
            monthLayout.addWidget(monthLabel)
            monthLayout.addWidget(monthEdit)
            
            wetDayLayout.addLayout(monthLayout)  # Add vertical layout to horizontal layout
        
        mainLayout.addWidget(wetDayGroupBox)

        # Reset Button
        resetButton = QPushButton("Reset")
        resetButton.clicked.connect(self.resetSettings)
        mainLayout.addWidget(resetButton)

        # Save and Load buttons
        buttonLayout = QHBoxLayout()
        saveButton = QPushButton("Save Settings")
        saveButton.clicked.connect(self.saveSettingsFromUi)
        loadButton = QPushButton("Load Settings")
        loadButton.clicked.connect(self.loadSettingsFromUi)
        buttonLayout.addWidget(saveButton)
        buttonLayout.addWidget(loadButton)
        mainLayout.addLayout(buttonLayout)

        # Set input fields color
        self.varianceInflationEdit.setStyleSheet("color: black;")
        self.biasCorrectionEdit.setStyleSheet("color: black;")
        self.fixedThresholdEdit.setStyleSheet("color: black;")
        for edit in self.wetDayEdits:
            edit.setStyleSheet("color: black;")

        # Set window properties
        self.setWindowTitle("Settings")
        self.resize(800, 600)

        # Load the default settings into the UI upon startup
        self.loadSettings()
        self.loadSettingsIntoUi()

    def resetSettings(self):
        global varianceInflation, biasCorrection, fixedThreshold, modelTransformation, optimizationAlgorithm, criteriaType, stepwiseRegression, conditionalSelection, months

        # Reset all global variables to their default values
        varianceInflation = defaultValues['varianceInflation']
        biasCorrection = defaultValues['biasCorrection']
        fixedThreshold = defaultValues['fixedThreshold']
        modelTransformation = defaultValues['modelTransformation']
        optimizationAlgorithm = defaultValues['optimizationAlgorithm']
        criteriaType = defaultValues['criteriaType']
        stepwiseRegression = defaultValues['stepwiseRegression']
        conditionalSelection = defaultValues['conditionalSelection']
        months = defaultValues['months']

        # Load default values into UI
        self.loadSettingsIntoUi()

    def loadSettingsIntoUi(self):
        self.varianceInflationEdit.setText(str(varianceInflation))
        self.biasCorrectionEdit.setText(str(biasCorrection))
        self.fixedThresholdEdit.setText(str(fixedThreshold))
        self.transNone.setChecked(modelTransformation == 'None')
        self.transFourthRoot.setChecked(modelTransformation == 'Fourth root')
        self.transNaturalLog.setChecked(modelTransformation == 'Natural log')
        self.transInverseNormal.setChecked(modelTransformation == 'Inverse Normal')
        self.transBoxCox.setChecked(modelTransformation == 'Box Cox')
        self.optimOrdinaryLeastSquares.setChecked(optimizationAlgorithm == 'Ordinary Least Squares')
        self.optimDualSimplex.setChecked(optimizationAlgorithm == 'Dual Simplex')
        self.aicCriterion.setChecked(criteriaType == 'AIC Criteria')
        self.bicCriterion.setChecked(criteriaType == 'BIC Criteria')
        self.conditionalStochastic.setChecked(conditionalSelection == 'Stochastic')
        self.conditionalFixedThreshold.setChecked(conditionalSelection == 'Fixed Threshold')
        self.stepwiseRegressionCheck.setChecked(stepwiseRegression)
        for i, edit in enumerate(self.wetDayEdits):
            edit.setText(str(months[i]))

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

        except configparser.Error as e:
            QMessageBox.critical(self, "Error", f"Error loading settings: {e}")

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

    def saveSettings(self, iniFile=None):
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
            if os.path.isdir(iniFile):
                iniFile = os.path.join(iniFile, 'settings.ini')
            with open(iniFile, 'w') as configfile:
                config.write(configfile)
                QMessageBox.information(self, "Info", f"Settings saved to '{iniFile}'")
        except OSError as e:
            QMessageBox.critical(self, "Error", f"Error: Could not save settings to the specified location '{iniFile}'. Reason: {e}")
    
    def saveSettingsFromUi(self):
        global varianceInflation, biasCorrection, fixedThreshold, modelTransformation, optimizationAlgorithm, criteriaType, stepwiseRegression, conditionalSelection, months

        varianceInflation =  self.varianceInflationEdit.text()
        biasCorrection = self.biasCorrectionEdit.text()
        fixedThreshold = self.fixedThresholdEdit.text()
        modelTransformation =  self.get_model_transformation()
        optimizationAlgorithm = self.get_optimization_algorithm()
        stepwiseRegression = str(self.stepwiseRegressionCheck.isChecked())
        criteriaType = self.get_criteria_type()
        conditionalSelection = self.get_conditional_selection()

        months = [self.wetDayEdits[i].text() for i in range(12)]

        # If all validations pass, proceed with saving settings
        self.saveSettings()

    def loadSettingsFromUi(self):
        iniFile = QFileDialog.getOpenFileName(self, "Open Settings File", defaultDir, "INI Files (*.ini)")[0]
        if iniFile and os.path.isfile(iniFile):
            self.loadSettings(iniFile)
            self.loadSettingsIntoUi()

    def get_model_transformation(self):
        if self.transNone.isChecked():
            return "None"
        elif self.transFourthRoot.isChecked():
            return "Fourth root"
        elif self.transNaturalLog.isChecked():
            return "Natural log"
        elif self.transInverseNormal.isChecked():
            return "Inverse Normal"
        elif self.transBoxCox.isChecked():
            return "Box Cox"

    def get_optimization_algorithm(self):
        return "Ordinary Least Squares" if self.optimOrdinaryLeastSquares.isChecked() else "Dual Simplex"

    def get_criteria_type(self):
        return "AIC Criteria" if self.aicCriterion.isChecked() else "BIC Criteria"

    def get_conditional_selection(self):
        return "Stochastic" if self.conditionalStochastic.isChecked() else "Fixed Threshold"

# Main function for testing the UI
def main():
    app = QApplication(sys.argv)
    window = ContentWidget()
    window.setWindowTitle("SDSM Wireframe")
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
