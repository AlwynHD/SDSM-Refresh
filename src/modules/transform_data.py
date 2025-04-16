from PyQt5.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QFrame,
    QLabel,
    QFileDialog,
    QScrollArea,
    QDateEdit,
    QCheckBox,
    QButtonGroup,
    QRadioButton,
    QLineEdit,
    QGroupBox,
    QMessageBox,
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QPalette, QColor, QIcon
from src.lib.utils import loadFilesIntoMemory
import os

# Define the name of the module for display in the content area
moduleName = "Transform Data"


def displayBox(messageType, messageInfo, messageTitle, isError=False):
    messageBox = QMessageBox()
    if isError:
        messageBox.setIcon(QMessageBox.Critical)
    else:
        messageBox.setIcon(QMessageBox.Information)
    messageBox.setText(messageType)
    messageBox.setInformativeText(messageInfo)
    messageBox.setWindowTitle(messageTitle)
    messageBox.exec_()


class borderedQGroupBox(QGroupBox):
    def __init__(self, args):
        super().__init__(args)


class labeledQLineEditFrame(QFrame):
    def __init__(self, labelVal, lineEditVal):
        super().__init__()
        layout = QHBoxLayout()
        label = QLabel(labelVal)
        self.lineEdit = QLineEdit(lineEditVal)
        layout.addWidget(label)
        layout.addWidget(self.lineEdit)
        self.setLayout(layout)

    def getLineEditVal(self):
        return self.lineEdit.text()

    def setLineEditVal(self, text):
        self.lineEdit.setText(text)


class ContentWidget(QWidget):
    """
    A widget to display the Transform Data screen (UI/UX).
    Includes a buttonBar at the top and a contentArea for displaying details.
    """

    def __init__(self):
        """
        Initialize the Transform Data screen UI/UX, setting up the layout, buttonBar, and contentArea.
        """
        super().__init__()

        self.predictorPath = "predictor files"

        self.inputSelected = ""
        self.outputSelected = ""

        # Main layout for the entire widget
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(0, 0, 0, 0)  # Remove padding from the layout
        mainLayout.setSpacing(0)  # No spacing between elements
        self.setLayout(mainLayout)  # Apply the main layout to the widget

        self.setStyleSheet(
            """
                            
                            QFrame{
                                background-color: #F0F0F0;
                                font-size: 18px;}
                           
                            QRadioButton
                           {
                                font-size: 18px;
                           }
                           QDateEdit
                           {
                                font-size: 18px;
                           }
                           QLineEdit
                           {
                                font-size: 18px;
                           }
                           QCheckBox
                           {
                                font-size: 18px;
                           }
                            borderedQGroupBox{
                                background-color: #F0F0F0;
                                border : 1px solid #CECECE;
                                border-top-left-radius : 20px;
                                border-top-right-radius : 20px;
                                border-bottom-left-radius : 20px;
                                border-bottom-right-radius : 20px;}"""
        )

        # --- Frame Area ---

        contentAreaFrame = QFrame()
        contentAreaFrame.setFrameStyle(QFrame.NoFrame)  # No border around the frame
        contentAreaFrame.setBaseSize(600, 100)
        contentAreaFrame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        # Layout for the contentArea frame
        contentAreaLayout = QHBoxLayout()
        contentAreaLayout.setContentsMargins(
            25, 25, 25, 25
        )  # Remove padding from the layout
        contentAreaLayout.setSpacing(10)  # No spacing between elements
        contentAreaFrame.setLayout(contentAreaLayout)  # Apply the layout to the frame

        mainLayout.addWidget(contentAreaFrame)

        # Frame to hold Input file, Columns in input file, SIM file, Ensemble member, Threshold, OUT File (ICSETO)
        selectICSETOFrame = QFrame()
        selectICSETOFrame.setFrameStyle(QFrame.NoFrame)
        selectICSETOFrame.setBaseSize(200, 500)
        selectICSETOFrame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        selectICSETOLayout = QVBoxLayout()
        selectICSETOLayout.setContentsMargins(
            0, 0, 0, 0
        )  # Remove padding from the layout
        selectICSETOLayout.setSpacing(10)  # No spacing between elements
        selectICSETOFrame.setLayout(selectICSETOLayout)

        contentAreaLayout.addWidget(selectICSETOFrame)

        # Create selectInputFile frame
        selectInputFileFrame = borderedQGroupBox("Select Input File")
        selectInputFileFrame.setBaseSize(200, 200)

        # Layout for selectInputFile frame
        selectInputFileLayout = QVBoxLayout()
        selectInputFileLayout.setContentsMargins(
            25, 25, 25, 25
        )  # Pad 10 pixels each way
        selectInputFileLayout.setSpacing(0)  # No spacing between elements

        selectInputFileFrame.setLayout(selectInputFileLayout)

        selectICSETOLayout.addWidget(selectInputFileFrame)

        columnFrame = borderedQGroupBox("Columns in Input File")
        columnFrame.setBaseSize(200, 200)

        columnLayout = QHBoxLayout()
        columnLayout.setContentsMargins(25, 25, 25, 25)
        columnLayout.setSpacing(0)

        columnFrame.setLayout(columnLayout)

        selectICSETOLayout.addWidget(columnFrame)

        simFrame = borderedQGroupBox("Create SIM File")
        simFrame.setBaseSize(200, 200)

        simLayout = QHBoxLayout()
        simLayout.setContentsMargins(25, 25, 25, 25)
        simLayout.setSpacing(0)

        simFrame.setLayout(simLayout)

        selectICSETOLayout.addWidget(simFrame)

        ensembleFrame = borderedQGroupBox("Extract Ensemble Member")
        ensembleFrame.setBaseSize(200, 200)

        ensembleLayout = QHBoxLayout()
        ensembleLayout.setContentsMargins(25, 25, 25, 25)
        ensembleLayout.setSpacing(0)

        ensembleFrame.setLayout(ensembleLayout)

        selectICSETOLayout.addWidget(ensembleFrame)

        thresholdFrame = borderedQGroupBox("Threshold")
        thresholdFrame.setBaseSize(200, 200)

        thresholdLayout = QHBoxLayout()
        thresholdLayout.setContentsMargins(25, 25, 25, 25)
        thresholdLayout.setSpacing(0)

        thresholdFrame.setLayout(thresholdLayout)

        selectICSETOLayout.addWidget(thresholdFrame)

        outputFrame = borderedQGroupBox("Create .OUT File ")
        outputFrame.setBaseSize(200, 200)

        outputLayout = QHBoxLayout()
        outputLayout.setContentsMargins(25, 25, 25, 25)
        outputLayout.setSpacing(0)

        outputFrame.setLayout(outputLayout)

        selectICSETOLayout.addWidget(outputFrame)

        transformationFrame = borderedQGroupBox("Transformation")
        transformationFrame.setBaseSize(200, 500)
        transformationFrame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        transformationLayout = QVBoxLayout()
        transformationLayout.setContentsMargins(
            0, 25, 0, 25
        )  # Remove padding from the layout
        transformationLayout.setSpacing(10)  # No spacing between elements
        transformationFrame.setLayout(
            transformationLayout
        )  # Apply the layout to the frame

        contentAreaLayout.addWidget(transformationFrame)

        # selectOPBOFrame, Output file, Pad data, Box, Outliers (OPBO)
        selectOPBOFrame = QFrame()
        selectOPBOFrame.setFrameStyle(QFrame.NoFrame)  # No border around the frame
        selectOPBOFrame.setBaseSize(200, 500)
        selectOPBOFrame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        selectOPBOLayout = QVBoxLayout()
        selectOPBOLayout.setContentsMargins(
            0, 0, 0, 0
        )  # Remove padding from the layout
        selectOPBOLayout.setSpacing(10)  # No spacing between elements
        selectOPBOFrame.setLayout(selectOPBOLayout)  # Apply the layout to the frame

        contentAreaLayout.addWidget(selectOPBOFrame)

        # Select Output File
        selectOutputFileFrame = borderedQGroupBox("Select Output File")
        selectOutputFileFrame.setBaseSize(200, 200)

        # Layout for selectPredictandFile frame
        selectOutputFileLayout = QVBoxLayout()
        selectOutputFileLayout.setContentsMargins(
            25, 25, 25, 25
        )  # Pad 10 pixels each way
        selectOutputFileLayout.setSpacing(0)  # No spacing between elements

        selectOutputFileFrame.setLayout(selectOutputFileLayout)

        selectOPBOLayout.addWidget(selectOutputFileFrame)

        padDataFrame = borderedQGroupBox("Pad Data")
        padDataFrame.setBaseSize(200, 200)

        padDataLayout = QVBoxLayout()
        padDataLayout.setContentsMargins(25, 25, 25, 25)
        padDataLayout.setSpacing(0)

        padDataFrame.setLayout(padDataLayout)
        selectOPBOLayout.addWidget(padDataFrame)

        boxFrame = borderedQGroupBox("Box Cox")
        boxFrame.setBaseSize(200, 200)

        boxLayout = QVBoxLayout()
        boxLayout.setContentsMargins(25, 25, 25, 25)
        boxLayout.setSpacing(0)

        boxFrame.setLayout(boxLayout)
        selectOPBOLayout.addWidget(boxFrame)

        outlierFrame = borderedQGroupBox("Outlier Filter")
        outlierFrame.setBaseSize(200, 200)

        outlierLayout = QVBoxLayout()
        outlierLayout.setContentsMargins(25, 25, 25, 25)
        outlierLayout.setSpacing(0)

        outlierFrame.setLayout(outlierLayout)
        selectOPBOLayout.addWidget(outlierFrame)

        buttonFrame = QFrame()
        buttonFrame.setBaseSize(600, 60)
        buttonFrame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        buttonLayout = QHBoxLayout()
        buttonLayout.setContentsMargins(25, 25, 25, 25)
        buttonLayout.setSpacing(10)

        buttonFrame.setLayout(buttonLayout)

        mainLayout.addWidget(buttonFrame)

        # Content

        # Predictand file selector button
        selectInputButton = QPushButton("📂 Select Input File")
        selectInputButton.clicked.connect(self.selectInputButtonClicked)
        selectInputFileLayout.addWidget(selectInputButton)

        self.selectInputLabel = QLabel("File: Not Selected")
        selectInputFileLayout.addWidget(self.selectInputLabel)

        self.columnInput = QLineEdit("1")
        columnLayout.addWidget(self.columnInput)

        self.simCheckBox = QCheckBox("Create")
        simLayout.addWidget(self.simCheckBox)

        self.ensembleCheckBox = QCheckBox("Extract")
        self.ensembleInput = QLineEdit("1")
        ensembleLayout.addWidget(self.ensembleCheckBox)
        ensembleLayout.addWidget(self.ensembleInput)

        self.thresholdCheckBox = QCheckBox("Apply Threshold")
        thresholdLayout.addWidget(self.thresholdCheckBox)

        self.outputCheckBox = QCheckBox("Create .OUT File")
        outputLayout.addWidget(self.outputCheckBox)

        self.transformRadioGroup = QButtonGroup()
        self.transformRadioGroup.setExclusive(True)
        self.transformRadioGroup.buttonPressed.connect(self.unPressOtherRadios)

        transformationsFrame = QFrame()
        transformationsFrame.setBaseSize(200, 300)
        transformationFrame.setContentsMargins(25, 0, 25, 0)
        transformationsFrame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        transformationsLayout = QHBoxLayout()
        transformationsFrame.setLayout(transformationsLayout)
        functionTransformationsFrame = QFrame()
        functionTransformationsLayout = QVBoxLayout()
        functionTransformationsFrame.setLayout(functionTransformationsLayout)

        functionsLabel = QLabel("Functions")
        functionsLabel.setAlignment(Qt.AlignTop)
        functionTransformationsLayout.addWidget(functionsLabel)

        natLogRadio = QRadioButton("Ln")
        self.transformRadioGroup.addButton(natLogRadio)
        functionTransformationsLayout.addWidget(natLogRadio)

        logRadio = QRadioButton("Log")
        self.transformRadioGroup.addButton(logRadio)
        functionTransformationsLayout.addWidget(logRadio)

        squareRadio = QRadioButton("x²")
        self.transformRadioGroup.addButton(squareRadio)
        functionTransformationsLayout.addWidget(squareRadio)

        cubeRadio = QRadioButton("x³")
        self.transformRadioGroup.addButton(cubeRadio)
        functionTransformationsLayout.addWidget(cubeRadio)

        fourRadio = QRadioButton("x⁴")
        self.transformRadioGroup.addButton(fourRadio)
        functionTransformationsLayout.addWidget(fourRadio)

        recipRadio = QRadioButton("x⁻¹")
        self.transformRadioGroup.addButton(recipRadio)
        functionTransformationsLayout.addWidget(recipRadio)

        inverseTransformationsFrame = QFrame()
        inverseTransformationsLayout = QVBoxLayout()
        inverseTransformationsFrame.setLayout(inverseTransformationsLayout)

        inverseLabel = QLabel("Inverse")
        inverseLabel.setAlignment(Qt.AlignTop)
        inverseTransformationsLayout.addWidget(inverseLabel)

        eXRadio = QRadioButton("eˣ")
        self.transformRadioGroup.addButton(eXRadio)
        inverseTransformationsLayout.addWidget(eXRadio)

        tenXRadio = QRadioButton("10ˣ")
        self.transformRadioGroup.addButton(tenXRadio)
        inverseTransformationsLayout.addWidget(tenXRadio)

        sqrtRadio = QRadioButton("√x")
        self.transformRadioGroup.addButton(sqrtRadio)
        inverseTransformationsLayout.addWidget(sqrtRadio)

        cbrtRadio = QRadioButton("∛x")
        self.transformRadioGroup.addButton(cbrtRadio)
        inverseTransformationsLayout.addWidget(cbrtRadio)

        fourRtRadio = QRadioButton("∜x")
        self.transformRadioGroup.addButton(fourRtRadio)
        inverseTransformationsLayout.addWidget(fourRtRadio)

        xRadio = QRadioButton("x")
        self.transformRadioGroup.addButton(xRadio)
        inverseTransformationsLayout.addWidget(xRadio)

        transformationsLayout.addWidget(functionTransformationsFrame)
        transformationsLayout.addWidget(inverseTransformationsFrame)

        transformationLayout.addWidget(transformationsFrame)

        spacerFrame = QFrame()
        spacerFrame.setFrameShape(QFrame.HLine | QFrame.Sunken)
        transformationLayout.addWidget(spacerFrame)

        otherTransformationsFrame = QFrame()
        otherTransformationsLayout = QVBoxLayout()
        otherTransformationsFrame.setContentsMargins(25, 0, 25, 0)
        backwardChangeRadio = QRadioButton("Backward Change")
        self.transformRadioGroup.addButton(backwardChangeRadio)
        otherTransformationsFrame.setLayout(otherTransformationsLayout)
        otherTransformationsLayout.addWidget(backwardChangeRadio)
        transformationLayout.addWidget(otherTransformationsFrame)

        lagNFrame = QFrame()
        lagNLayout = QHBoxLayout()
        lagNRadio = QRadioButton("Lag n")
        self.transformRadioGroup.addButton(lagNRadio)
        self.lagNLineEdit = QLineEdit("0")
        self.wrapCheckBox = QCheckBox("Wrap")
        lagNLayout.addWidget(lagNRadio)

        lagNLayout.addWidget(self.lagNLineEdit)
        lagNLayout.addWidget(self.wrapCheckBox)
        lagNFrame.setLayout(lagNLayout)

        otherTransformationsLayout.addWidget(lagNFrame)

        binomialFrame = QFrame()
        binomialLayout = QHBoxLayout()
        binomialRadio = QRadioButton("Binomial")
        self.transformRadioGroup.addButton(binomialRadio)

        self.binomialLineEdit = QLineEdit("0")

        binomialLayout.addWidget(binomialRadio)
        binomialLayout.addWidget(self.binomialLineEdit)
        binomialFrame.setLayout(binomialLayout)
        otherTransformationsLayout.addWidget(binomialFrame)

        selectOutputButton = QPushButton("📂 Select Output File")
        selectOutputButton.clicked.connect(self.selectOutputButtonClicked)
        selectOutputFileLayout.addWidget(selectOutputButton)

        self.selectOutputLabel = QLabel("File: Not Selected")
        selectOutputFileLayout.addWidget(self.selectOutputLabel)

        self.padDataCheckBox = QCheckBox("Pad Data")

        startDateFrame = QFrame()
        startDateLayout = QHBoxLayout()
        startDateLabel = QLabel("Start Date: ")
        self.startDateEdit = QDateEdit(calendarPopup=True)
        self.startDateEdit.setDate(QDate(1948, 1, 1))

        startDateLayout.addWidget(startDateLabel)
        startDateLayout.addWidget(self.startDateEdit)
        startDateFrame.setLayout(startDateLayout)

        endDateFrame = QFrame()
        endDateLayout = QHBoxLayout()
        endDateLabel = QLabel("End Date: ")
        self.endDateEdit = QDateEdit(calendarPopup=True)
        self.endDateEdit.setDate(QDate(2015, 12, 31))
        endDateLayout.addWidget(endDateLabel)
        endDateLayout.addWidget(self.endDateEdit)
        endDateFrame.setLayout(endDateLayout)

        padDataLayout.addWidget(self.padDataCheckBox)
        padDataLayout.addWidget(startDateFrame)
        padDataLayout.addWidget(endDateFrame)

        boxCoxRadio = QRadioButton("Box Cox")
        unBoxCoxRadio = QRadioButton("Un-Box Cox")
        self.transformRadioGroup.addButton(boxCoxRadio)
        self.transformRadioGroup.addButton(unBoxCoxRadio)
        self.lambdaFrame = labeledQLineEditFrame("Lambda: ", "1")
        self.shiftFrame = labeledQLineEditFrame("Shift: ", "0")

        boxLayout.addWidget(boxCoxRadio)
        boxLayout.addWidget(unBoxCoxRadio)
        boxLayout.addWidget(self.lambdaFrame)
        boxLayout.addWidget(self.shiftFrame)

        self.outlierRadio = QRadioButton("Remove Outliers")
        self.transformRadioGroup.addButton(self.outlierRadio)
        self.standardDevFrame = labeledQLineEditFrame("Standard Dev: ", "0")
        outlierLayout.addWidget(self.outlierRadio)
        outlierLayout.addWidget(self.standardDevFrame)

        transformButton = QPushButton("Transform Data")
        transformButton.clicked.connect(self.doTransform)
        transformButton.setStyleSheet(
            "background-color: #4CAF50; color: white; font-weight: bold;"
        )

        buttonLayout.addWidget(transformButton)

        resetButton = QPushButton("🔄 Reset")
        resetButton.clicked.connect(self.resetAll)
        resetButton.setStyleSheet(
            "background-color: #F44336; color: white; font-weight: bold;"
        )
        buttonLayout.addWidget(resetButton)

    def resetAll(self):
        # Uncheck all buttons
        buttons = self.transformRadioGroup.buttons()
        self.transformRadioGroup.setExclusive(
            False
        )  # Set exclusive to false so that its fine with none being checked
        for button in buttons:
            button.setChecked(False)
        self.transformRadioGroup.setExclusive(True)
        # Remove selected files
        self.inputSelected = ""
        self.outputSelected = ""

        self.selectInputLabel.setText("File: Not Selected")
        self.selectOutputLabel.setText("File: Not Selected")

        # Reset check boxes
        self.simCheckBox.setChecked(False)
        self.ensembleCheckBox.setChecked(False)
        self.thresholdCheckBox.setChecked(False)
        self.outputCheckBox.setChecked(False)
        self.wrapCheckBox.setChecked(False)
        self.padDataCheckBox.setChecked(False)

        # Reset line edit fields
        self.columnInput.setText("1")
        self.ensembleInput.setText("1")
        self.lagNLineEdit.setText("0")
        self.binomialLineEdit.setText("0")
        self.lambdaFrame.setLineEditVal("1")
        self.shiftFrame.setLineEditVal("0")
        self.standardDevFrame.setLineEditVal("0")

        # Reset dates
        self.startDateEdit.setDate(QDate(1948, 1, 1))
        self.endDateEdit.setDate(QDate(2015, 12, 31))

    def QDateEditToDateTime(self, dateEdit):
        rawStartDate = dateEdit.date()
        dateTime = rawStartDate.toPyDate()
        return dateTime

    def selectInputButtonClicked(self):
        # Will have to be changed soon, as it relies on known file "predictand files"
        fileName = QFileDialog.getOpenFileName(
            self, "Select input file", "predictand files", "DAT Files (*.DAT)"
        )
        print(fileName)
        if fileName[0] != "":
            self.inputSelected = fileName[0]
            self.selectInputLabel.setText(
                "File: " + self.inputSelected.split("/")[-1]
            )  # Only show the name of the file, not the whole path
        else:
            self.inputSelected = ""
            self.selectInputLabel.setText("File: Not Selected")

    def selectOutputButtonClicked(self):
        # Will have to be changed soon, as it relies on known file "predictand files"
        fileName = QFileDialog.getOpenFileName(
            self, "Select output file", "SDSM Refresh", ""
        )
        print(fileName)
        if fileName[0] != "":
            self.outputSelected = fileName[0]
            self.selectOutputLabel.setText(
                "File: " + self.outputSelected.split("/")[-1]
            )  # Only show the name of the file, not the whole path
        else:
            self.outputSelected = ""
            self.selectOutputLabel.setText("File: Not Selected")

    def unPressOtherRadios(self, *args):
        # Needed to make sure function radio and inverse radio buttons cant be clicked at same time
        radio = self.sender()
        buttons = self.transformRadioGroup.buttons()
        for button in buttons:
            if button != radio:
                if button.isChecked():
                    button.setChecked(False)

    def doTransform(self):
        from src.lib.utils import getSettings
        from src.lib.TransformData import (
            square,
            cube,
            powFour,
            powMinusOne,
            eToTheN,
            tenToTheN,
            lag,
            binomial,
            backwardsChange,
            removeOutliers,
        )
        from src.lib.TransformData import (
            powHalf,
            powThird,
            powQuarter,
            returnSelf,
            padData,
            genericTransform,
            loadData,
            boxCox,
            unBoxCox,
        )
        from numpy import log, log10, ndim, empty, longdouble

        # print("https://www.youtube.com/watch?v=7F2QE8O-Y1g")

        settings = getSettings()
        try:  # Check if an input file is selected
            file = open(self.inputSelected, "r")
            file.close()
        except FileNotFoundError:
            return displayBox(
                "Input Error", "No input file selected.", "Error", isError=True
            )
        try:  # Check if an output file is selected
            outputFile = open(self.outputSelected, "w")
        except (FileNotFoundError, TypeError) as e:
            if (
                not self.outputCheckBox.isChecked()
            ):  # If an OUT file is not being generated
                return displayBox(
                    "Output Error",
                    "No output file selected, and you have not selected one to be generated.",
                    "Error",
                    isError=True,
                )
            else:
                outputFile = open(
                    self.inputSelected.split("/")[-1] + " transformed.OUT", "w"
                )
        applyThresh = self.thresholdCheckBox.isChecked()
        data = loadData([self.inputSelected])
        try:  # Check if a transformation is selected
            trans = self.transformRadioGroup.checkedButton().text()
        except AttributeError:
            return displayBox(
                "Transformation Error",
                "A transformation must be selected.",
                "Error",
                isError=True,
            )
        transformations = [
            ["Ln", log],
            ["Log", log10],
            ["x²", square],
            ["x³", cube],
            ["x⁴", powFour],
            ["x⁻¹", powMinusOne],
            ["eˣ", eToTheN],
            ["10ˣ", tenToTheN],
            ["√x", powHalf],
            ["∛x", powThird],
            ["∜x", powQuarter],
            ["x", returnSelf],
        ]
        if self.padDataCheckBox.isChecked():
            data = padData(
                data,
                self.QDateEditToDateTime(self.startDateEdit),
                self.QDateEditToDateTime(self.endDateEdit),
            )
        genericTrans = False
        for i in transformations:
            if i[0] == trans:
                genericTrans = True
                returnedData, returnedInfo = genericTransform(data, i[1], applyThresh)
                for i in returnedData:
                    outputFile.write(str(i[0]) + "\n")
        if not genericTrans:
            if trans == "Box Cox":
                returnedData, returnedInfo = boxCox(data, applyThresh)
            elif trans == "Un-Box Cox":
                if (
                    not self.lambdaFrame.getLineEditVal().isdigit()
                    or not self.shiftFrame.getLineEditVal().isdigit()
                ):
                    return displayBox(
                        "Value error",
                        "Lamda and left shift values must be integers",
                        "Error",
                        isError=True,
                    )
                returnedData, returnedInfo = unBoxCox(
                    data,
                    self.lambdaFrame.getLineEditVal(),
                    self.shiftFrame.getLineEditVal(),
                    applyThresh,
                )
            elif trans == "Lag n":
                if not self.lagNLineEdit.text().isdigit():
                    return displayBox(
                        "Value error",
                        "Lag N value must be an integer",
                        "Error",
                        isError=True,
                    )
                returnedData, returnedInfo = lag(
                    data, int(self.lagNLineEdit.text()), self.wrapCheckBox.isChecked()
                )
            elif trans == "Binomial":
                if not self.binomialLineEdit.text().isdigit():
                    return displayBox(
                        "Value error",
                        "Binomial value must be an integer",
                        "Error",
                        isError=True,
                    )
                returnedData, returnedInfo = binomial(
                    data, int(self.binomialLineEdit.text()), applyThresh
                )
            elif trans == "Backward Change":
                returnedData, returnedInfo = backwardsChange(data, applyThresh)
            elif trans == "Remove Outliers":
                if not self.standardDevFrame.getLineEditVal().isdigit():
                    return displayBox(
                        "Value error",
                        "Standard deviation value must be an integer",
                        "Error",
                        isError=True,
                    )
                returnedData, returnedInfo = removeOutliers(
                    data, int(self.standardDevFrame.getLineEditVal()), applyThresh
                )

        outputFile.close()
        if self.outputSelected != "" and self.outputCheckBox.isChecked():
            transformedFile = open(self.outputSelected, "r")
            outputFile = open(
                self.inputSelected.split("/")[-1] + " transformed.OUT", "w"
            )
            for line in transformedFile:
                outputFile.write(line)
        return displayBox("Data Transformed", returnedInfo, "Transformation Success")
