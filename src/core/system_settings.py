from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QRadioButton, QLineEdit, QLabel, QGroupBox,
    QPushButton, QCheckBox, QFileDialog, QButtonGroup,
    QMessageBox
)
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt
import configparser
import os
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
months = defaultValues['months'][:]


class ContentWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Main content layout
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(10, 10, 10, 10)
        mainLayout.setSpacing(10)
        self.setLayout(mainLayout)

        # Model Transformation
        modelTransGroupBox = QGroupBox("Model Transformation")
        modelTransGroupBox.setStyleSheet("color: black;")
        modelTransLayout = QHBoxLayout()
        modelTransLayout.setSpacing(5)
        modelTransLayout.setContentsMargins(5, 0, 5, 0)
        modelTransGroupBox.setLayout(modelTransLayout)

        self.transNone = QRadioButton("None")
        self.transFourthRoot = QRadioButton("Fourth root")
        self.transNaturalLog = QRadioButton("Natural log")
        self.transInverseNormal = QRadioButton("Inverse Normal")
        self.transBoxCox = QRadioButton("Box Cox")
        self.transNone.setChecked(True)

        for btn in (
            self.transNone, self.transFourthRoot, self.transNaturalLog,
            self.transInverseNormal, self.transBoxCox
        ):
            modelTransLayout.addWidget(btn)

        mainLayout.addWidget(modelTransGroupBox)

        # Variance / Bias / Conditional row
        groupContainer = QHBoxLayout()

        varianceInflationGroup = QGroupBox("Variance Inflation")
        varianceInflationGroup.setStyleSheet("color: black;")
        varLayout = QHBoxLayout()
        varianceInflationGroup.setLayout(varLayout)
        varLayout.addWidget(QLabel("Value:"))
        self.varianceInflationEdit = QLineEdit()
        self.varianceInflationEdit.setFixedWidth(60)
        varLayout.addWidget(self.varianceInflationEdit)
        groupContainer.addWidget(varianceInflationGroup)

        biasCorrectionGroup = QGroupBox("Bias Correction")
        biasCorrectionGroup.setStyleSheet("color: black;")
        biasLayout = QHBoxLayout()
        biasCorrectionGroup.setLayout(biasLayout)
        biasLayout.addWidget(QLabel("Value:"))
        self.biasCorrectionEdit = QLineEdit()
        self.biasCorrectionEdit.setFixedWidth(60)
        biasLayout.addWidget(self.biasCorrectionEdit)
        groupContainer.addWidget(biasCorrectionGroup)

        conditionalGroupBox = QGroupBox("Conditional Selection")
        conditionalGroupBox.setStyleSheet("color: black;")
        condLayout = QHBoxLayout()
        conditionalGroupBox.setLayout(condLayout)
        self.conditionalStochastic = QRadioButton("Stochastic")
        self.conditionalFixedThreshold = QRadioButton("Fixed Threshold:")
        self.fixedThresholdEdit = QLineEdit()
        self.fixedThresholdEdit.setFixedWidth(50)
        condLayout.addWidget(self.conditionalStochastic)
        condLayout.addWidget(self.conditionalFixedThreshold)
        condLayout.addWidget(self.fixedThresholdEdit)
        self.conditionalStochastic.setChecked(True)
        groupContainer.addWidget(conditionalGroupBox)

        mainLayout.addLayout(groupContainer)

        # Optimization Algorithm & Criteria
        optimGroupBox = QGroupBox("Optimization Algorithm")
        optimGroupBox.setStyleSheet("color: black;")
        optimLayout = QVBoxLayout()
        optimGroupBox.setLayout(optimLayout)

        self.optimOrdinaryLeastSquares = QRadioButton("Ordinary Least Squares")
        self.optimDualSimplex = QRadioButton("Dual Simplex")
        self.stepwiseRegressionCheck = QCheckBox("Stepwise Regression")
        self.aicCriterion = QRadioButton("AIC Criteria")
        self.bicCriterion = QRadioButton("BIC Criteria")

        self.optimOrdinaryLeastSquares.setChecked(True)
        self.aicCriterion.setChecked(True)

        optimButtons = QButtonGroup(self)
        optimButtons.addButton(self.optimOrdinaryLeastSquares)
        optimButtons.addButton(self.optimDualSimplex)

        criteriaButtons = QButtonGroup(self)
        criteriaButtons.addButton(self.aicCriterion)
        criteriaButtons.addButton(self.bicCriterion)

        for w in (
            self.optimOrdinaryLeastSquares, self.optimDualSimplex,
            self.stepwiseRegressionCheck, self.aicCriterion, self.bicCriterion
        ):
            optimLayout.addWidget(w)

        mainLayout.addWidget(optimGroupBox)

        # Wet Day Percentage (months)
        wetDayGroupBox = QGroupBox("Wet Day Percentage Profile")
        wetDayGroupBox.setStyleSheet("color: black;")
        wetDayLayout = QHBoxLayout()
        wetDayGroupBox.setLayout(wetDayLayout)

        self.wetDayEdits = []
        for month in [
            "Jan","Feb","Mar","Apr","May","Jun",
            "Jul","Aug","Sep","Oct","Nov","Dec"
        ]:
            mLayout = QVBoxLayout()
            mLabel = QLabel(month)
            mLabel.setAlignment(Qt.AlignCenter)
            mEdit = QLineEdit()
            mEdit.setFixedWidth(40)
            mEdit.setAlignment(Qt.AlignCenter)
            self.wetDayEdits.append(mEdit)
            mLayout.addWidget(mLabel)
            mLayout.addWidget(mEdit)
            wetDayLayout.addLayout(mLayout)

        mainLayout.addWidget(wetDayGroupBox)

        # Reset button
        resetBtn = QPushButton("🔄 Reset Settings")
        resetBtn.setStyleSheet("background-color: #ED0800; color: white; font-weight: bold;")
        resetBtn.clicked.connect(self.resetSettings)
        mainLayout.addWidget(resetBtn)

        # Export / Save / Load buttons
        btnLayout = QHBoxLayout()

        exportBtn = QPushButton("📤 Export Settings")
        exportBtn.setStyleSheet("background-color: #1FC7F5; color: white; font-weight: bold;")
        exportBtn.clicked.connect(self.saveSettingsFromUi)
        btnLayout.addWidget(exportBtn)

        saveBtn = QPushButton("💾 Save Settings")
        saveBtn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        saveBtn.clicked.connect(self.saveSettingsDefault)
        btnLayout.addWidget(saveBtn)

        loadBtn = QPushButton("📂 Load Settings")
        loadBtn.setStyleSheet("background-color: #F57F0C; color: white; font-weight: bold;")
        loadBtn.clicked.connect(self.loadSettingsFromUi)
        btnLayout.addWidget(loadBtn)

        mainLayout.addLayout(btnLayout)

        # Input colors
        self.varianceInflationEdit.setStyleSheet("color: black;")
        self.biasCorrectionEdit.setStyleSheet("color: black;")
        self.fixedThresholdEdit.setStyleSheet("color: black;")
        for e in self.wetDayEdits:
            e.setStyleSheet("color: black;")

        # Window setup
        self.setWindowTitle("Settings")
        self.resize(800, 600)

        # Initial load
        self.loadSettings()
        self.loadSettingsIntoUi()

    def resetSettings(self):
        global varianceInflation, biasCorrection, fixedThreshold
        global modelTransformation, optimizationAlgorithm, criteriaType
        global stepwiseRegression, conditionalSelection, months

        varianceInflation = defaultValues['varianceInflation']
        biasCorrection = defaultValues['biasCorrection']
        fixedThreshold = defaultValues['fixedThreshold']
        modelTransformation = defaultValues['modelTransformation']
        optimizationAlgorithm = defaultValues['optimizationAlgorithm']
        criteriaType = defaultValues['criteriaType']
        stepwiseRegression = defaultValues['stepwiseRegression']
        conditionalSelection = defaultValues['conditionalSelection']
        months = defaultValues['months'][:]

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
        self.optimOrdinaryLeastSquares.setChecked(
            optimizationAlgorithm == 'Ordinary Least Squares'
        )
        self.optimDualSimplex.setChecked(
            optimizationAlgorithm == 'Dual Simplex'
        )
        self.aicCriterion.setChecked(criteriaType == 'AIC Criteria')
        self.bicCriterion.setChecked(criteriaType == 'BIC Criteria')
        self.conditionalStochastic.setChecked(
            conditionalSelection == 'Stochastic'
        )
        self.conditionalFixedThreshold.setChecked(
            conditionalSelection == 'Fixed Threshold'
        )
        self.stepwiseRegressionCheck.setChecked(stepwiseRegression)
        for i, edit in enumerate(self.wetDayEdits):
            edit.setText(str(months[i]))

    def loadSettings(self, iniFile=defaultIniFile):
        global varianceInflation, biasCorrection, fixedThreshold
        global modelTransformation, optimizationAlgorithm, criteriaType
        global stepwiseRegression, conditionalSelection, months

        if not os.path.exists(iniFile):
            return

        cfg = configparser.ConfigParser()
        cfg.read(iniFile)

        # use safeGetInt / safeGetFloat so "12.0" falls back cleanly
        varianceInflation = self.safeGetInt(
            cfg, 'Settings', 'VarianceInflation', defaultValues['varianceInflation']
        )
        biasCorrection = self.safeGetInt(
            cfg, 'Settings', 'BiasCorrection', defaultValues['biasCorrection']
        )
        fixedThreshold = self.safeGetFloat(
            cfg, 'Settings', 'FixedThreshold', defaultValues['fixedThreshold']
        )
        modelTransformation = cfg.get(
            'Settings', 'ModelTransformation',
            fallback=defaultValues['modelTransformation']
        )
        optimizationAlgorithm = cfg.get(
            'Settings', 'OptimizationAlgorithm',
            fallback=defaultValues['optimizationAlgorithm']
        )
        criteriaType = cfg.get(
            'Settings', 'CriteriaType',
            fallback=defaultValues['criteriaType']
        )
        stepwiseRegression = cfg.getboolean(
            'Settings', 'StepwiseRegression',
            fallback=defaultValues['stepwiseRegression']
        )
        conditionalSelection = cfg.get(
            'Settings', 'ConditionalSelection',
            fallback=defaultValues['conditionalSelection']
        )
        months = [
            int(x) for x in cfg.get(
                'Settings', 'Months',
                fallback=','.join(map(str, defaultValues['months']))
            ).split(',')
        ]

    def saveSettings(self, iniFile=None, silent=False):
        global varianceInflation, biasCorrection, fixedThreshold
        global modelTransformation, optimizationAlgorithm, criteriaType
        global stepwiseRegression, conditionalSelection, months

        # determine target INI path
        if iniFile is None:
            iniDir = QFileDialog.getExistingDirectory(
                self, "Select Directory to Save Settings", defaultDir
            )
            if not iniDir:
                return
            iniFile = os.path.join(iniDir, 'settings.ini')

        # load existing so we preserve every key
        cfg = configparser.ConfigParser()
        if os.path.exists(iniFile):
            cfg.read(iniFile)
        if 'Settings' not in cfg:
            cfg['Settings'] = {}

        # now overwrite only our system‐settings keys
        cfg['Settings']['VarianceInflation']      = str(varianceInflation)
        cfg['Settings']['BiasCorrection']         = str(biasCorrection)
        cfg['Settings']['FixedThreshold']         = str(fixedThreshold)
        cfg['Settings']['ModelTransformation']    = modelTransformation
        cfg['Settings']['OptimizationAlgorithm']  = optimizationAlgorithm
        cfg['Settings']['CriteriaType']           = criteriaType
        cfg['Settings']['StepwiseRegression']     = str(stepwiseRegression)
        cfg['Settings']['ConditionalSelection']   = conditionalSelection
        cfg['Settings']['Months']                 = ','.join(map(str, months))

        # write it all back
        try:
            with open(iniFile, 'w') as f:
                cfg.write(f)
            if not silent:
                QMessageBox.information(
                    self, "Info", f"Settings written to '{iniFile}'"
                )
        except OSError as e:
            QMessageBox.critical(self, "Error", f"Could not write settings: {e}")

    def saveSettingsFromUi(self):
        """Export (old Save)"""
        self._gatherUiValues()
        self.saveSettings(iniFile=None, silent=False)

    def saveSettingsDefault(self):
        """Save to default INI on “Save Settings” button"""
        # validate
        try:
            vi = int(float(self.varianceInflationEdit.text()))
            bc = int(float(self.biasCorrectionEdit.text()))
            ft = float(self.fixedThresholdEdit.text())
        except ValueError:
            QMessageBox.critical(
                self, "Error", "Variance/Bias/Threshold must be numeric."
            )
            return

        global varianceInflation, biasCorrection, fixedThreshold
        global modelTransformation, optimizationAlgorithm, criteriaType
        global stepwiseRegression, conditionalSelection, months

        varianceInflation       = vi
        biasCorrection          = bc
        fixedThreshold          = ft
        modelTransformation     = self.get_model_transformation()
        optimizationAlgorithm   = self.get_optimization_algorithm()
        criteriaType            = self.get_criteria_type()
        stepwiseRegression      = self.stepwiseRegressionCheck.isChecked()
        conditionalSelection    = self.get_conditional_selection()
        months                  = [int(e.text()) for e in self.wetDayEdits]

        self.saveSettings(iniFile=defaultIniFile, silent=False)

    def loadSettingsFromUi(self):
        iniFile, _ = QFileDialog.getOpenFileName(
            self, "Open Settings File", defaultDir, "INI Files (*.ini)"
        )
        if iniFile:
            self.loadSettings(iniFile)
            self.loadSettingsIntoUi()

    def _gatherUiValues(self):
        global varianceInflation, biasCorrection, fixedThreshold
        global modelTransformation, optimizationAlgorithm, criteriaType
        global stepwiseRegression, conditionalSelection, months

        varianceInflation       = int(float(self.varianceInflationEdit.text()))
        biasCorrection          = int(float(self.biasCorrectionEdit.text()))
        fixedThreshold          = float(self.fixedThresholdEdit.text())
        modelTransformation     = self.get_model_transformation()
        optimizationAlgorithm   = self.get_optimization_algorithm()
        criteriaType            = self.get_criteria_type()
        stepwiseRegression      = self.stepwiseRegressionCheck.isChecked()
        conditionalSelection    = self.get_conditional_selection()
        months                  = [int(e.text()) for e in self.wetDayEdits]

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

    def get_model_transformation(self):
        if self.transNone.isChecked(): return "None"
        if self.transFourthRoot.isChecked(): return "Fourth root"
        if self.transNaturalLog.isChecked(): return "Natural log"
        if self.transInverseNormal.isChecked(): return "Inverse Normal"
        if self.transBoxCox.isChecked(): return "Box Cox"

    def get_optimization_algorithm(self):
        return (
            "Ordinary Least Squares"
            if self.optimOrdinaryLeastSquares.isChecked()
            else "Dual Simplex"
        )

    def get_criteria_type(self):
        return "AIC Criteria" if self.aicCriterion.isChecked() else "BIC Criteria"

    def get_conditional_selection(self):
        return (
            "Stochastic"
            if self.conditionalStochastic.isChecked()
            else "Fixed Threshold"
        )


# Main for standalone testing
def main():
    app = QApplication(sys.argv)
    w = ContentWidget()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
